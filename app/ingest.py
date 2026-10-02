"""
Ingestion pipeline: reads records (from file or inline) and upserts into MongoDB.
Uses natural keys (order_id / product_id / customer_id) for idempotent ingestion.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from .database import db

KEY_CANDIDATES = ("order_id", "product_id", "customer_id", "_id")


def _coerce(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert ISO date strings (keys ending in _date) to datetime."""
    out = {}
    for k, v in doc.items():
        if k.endswith("_date") and isinstance(v, str):
            try:
                out[k] = datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                out[k] = v
        else:
            out[k] = v
    return out


def _natural_key(doc: Dict[str, Any]):
    for k in KEY_CANDIDATES:
        if k in doc:
            return {k: doc[k]}
    return None


def ingest_records(collection: str, records: List[Dict[str, Any]]) -> int:
    col = db[collection]
    count = 0
    for raw in records:
        doc = _coerce(raw)
        key = _natural_key(doc)
        if key:
            res = col.update_one(key, {"$set": doc}, upsert=True)
            if res.upserted_id is not None or res.modified_count > 0:
                count += 1
        else:
            col.insert_one(doc)
            count += 1
    return count


def ingest_file(collection: str, path: str) -> int:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = [data]
    return ingest_records(collection, data)
