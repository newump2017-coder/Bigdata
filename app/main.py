"""
Unified FastAPI interface to expose the entire project.
Swagger UI: /docs
"""
from typing import Any, Dict, List, Optional
import json

from bson import json_util
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from .database import db
from .ingest import ingest_file, ingest_records
from .indexes import create_indexes, INDEX_DEFS
from .queries import QUERIES, run_query, explain_query
from .aggregations import AGGREGATIONS, run_aggregation
from .materialized_views import MV_DEFS, refresh_mv, refresh_all, read_mv
from .jobs import JOBS, scheduler, register_jobs, run_job


# ---------- JSON helper (ObjectId / datetime) ----------
def to_json(obj: Any) -> Any:
    return json.loads(json_util.dumps(obj))


# ---------- App ----------
app = FastAPI(
    title="Big Data Project — Phase 2 API",
    version="1.0.0",
    description="Unified interface for queries, indexes, aggregations, "
                "materialized views and scheduled jobs.",
)


@app.on_event("startup")
def _startup():
    register_jobs()
    if not scheduler.running:
        scheduler.start()


@app.on_event("shutdown")
def _shutdown():
    if scheduler.running:
        scheduler.shutdown(wait=False)


# ---------- Models ----------
class IngestRequest(BaseModel):
    collection: str
    records: Optional[List[Dict[str, Any]]] = None
    path: Optional[str] = None


class RefreshMVRequest(BaseModel):
    name: Optional[str] = None  # None or "all" → refresh all


# ---------- 1) Health ----------
@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- 2) Ingest ----------
@app.post("/ingest")
def ingest(req: IngestRequest):
    try:
        if req.records is not None:
            n = ingest_records(req.collection, req.records)
        elif req.path:
            n = ingest_file(req.collection, req.path)
        else:
            raise HTTPException(400, "either 'records' or 'path' is required")
        return {"collection": req.collection, "processed": n}
    except FileNotFoundError as e:
        raise HTTPException(404, f"file not found: {e}")
    except Exception as e:
        raise HTTPException(500, str(e))


# ---------- 3) Indexes ----------
@app.post("/indexes")
def build_indexes():
    created = create_indexes()
    return {"created": created, "count": len(created)}


# ---------- 4) Queries ----------
@app.get("/queries")
def list_queries():
    return [{"name": k, "description": v["description"], "params": v["params"]}
            for k, v in QUERIES.items()]


@app.get("/queries/{name}")
def exec_query(name: str, request: Request, explain: bool = False):
    if name not in QUERIES:
        raise HTTPException(404, f"unknown query: {name}")
    params = dict(request.query_params)
    params.pop("explain", None)
    try:
        if explain:
            return to_json(explain_query(name, db, **params))
        docs = run_query(name, db, **params)
        return {"name": name, "count": len(docs), "results": to_json(docs)}
    except TypeError as e:
        raise HTTPException(400, f"bad params: {e}")


# ---------- 5) Aggregations ----------
@app.get("/aggregations")
def list_aggs():
    return [{"name": k, "description": v["description"], "params": v["params"]}
            for k, v in AGGREGATIONS.items()]


@app.get("/aggregations/{name}")
def exec_agg(name: str, request: Request):
    if name not in AGGREGATIONS:
        raise HTTPException(404, f"unknown aggregation: {name}")
    params = dict(request.query_params)
    try:
        docs = run_aggregation(name, db, **params)
        return {"name": name, "count": len(docs), "results": to_json(docs)}
    except TypeError as e:
        raise HTTPException(400, f"bad params: {e}")


# ---------- 6) Materialized Views ----------
@app.post("/refresh-mv")
def refresh_mv_endpoint(req: RefreshMVRequest):
    name = (req.name or "all").strip()
    try:
        if name == "all":
            counts = refresh_all()
            return {"refreshed": counts}
        n = refresh_mv(name)
        return {"refreshed": {name: n}}
    except KeyError:
        raise HTTPException(404, f"unknown MV: {name}")


@app.get("/materialized-views")
def list_mvs():
    return [{"name": k, "description": v["description"], "source": v["source"], "target": v["target"]}
            for k, v in MV_DEFS.items()]


@app.get("/materialized-views/{name}")
def read_mv_endpoint(name: str, limit: int = 100):
    if name not in MV_DEFS:
        raise HTTPException(404, f"unknown MV: {name}")
    return {"name": name, "results": to_json(read_mv(name, limit))}


# ---------- 7) Jobs ----------
@app.get("/jobs")
def list_jobs():
    jobs = []
    for jid, spec in JOBS.items():
        jobs.append({"name": jid, "description": spec["description"]})
    return jobs


@app.post("/jobs/{name}/run")
def trigger_job(name: str):
    if name not in JOBS:
        raise HTTPException(404, f"unknown job: {name}")
    return run_job(name)
