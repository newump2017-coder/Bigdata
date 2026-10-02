"""
5 استعلامات + Explain لكل استعلام مع executionStats.
"""
from datetime import datetime, timedelta


# ---------- Helpers ----------
def _parse_date(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _summarize_explain(explain: dict) -> dict:
    """Extract the essential executionStats + winning plan info."""
    stats = explain.get("executionStats", {}) or {}
    plan = explain.get("queryPlanner", {}).get("winningPlan", {})

    def find_stage(node, stage_name):
        if isinstance(node, dict):
            if node.get("stage") == stage_name:
                return node
            for v in node.values():
                r = find_stage(v, stage_name)
                if r:
                    return r
        elif isinstance(node, list):
            for v in node:
                r = find_stage(v, stage_name)
                if r:
                    return r
        return None

    ixscan = find_stage(plan, "IXSCAN")
    collscan = find_stage(plan, "COLLSCAN")
    stage_type = "IXSCAN" if ixscan else ("COLLSCAN" if collscan else "UNKNOWN")

    return {
        "stage": stage_type,
        "index_used": ixscan.get("indexName") if ixscan else None,
        "executionTimeMillis": stats.get("executionTimeMillis"),
        "totalKeysExamined": stats.get("totalKeysExamined"),
        "totalDocsExamined": stats.get("totalDocsExamined"),
        "nReturned": stats.get("nReturned"),
    }


# ---------- Query 1 ----------
def q_orders_by_city_date(db, city="Cairo", start="2024-01-01", end="2024-12-31", limit=50, **kw):
    limit = int(limit)
    return list(db.orders.find(
        {"city": city,
         "order_date": {"$gte": _parse_date(start), "$lte": _parse_date(end)}},
        {"_id": 0}
    ).sort("order_date", -1).limit(limit))


def e_orders_by_city_date(db, city="Cairo", start="2024-01-01", end="2024-12-31", **kw):
    return db.command({
        "explain": {
            "find": "orders",
            "filter": {"city": city,
                       "order_date": {"$gte": _parse_date(start), "$lte": _parse_date(end)}},
            "sort": {"order_date": -1},
        },
        "verbosity": "executionStats",
    })


# ---------- Query 2 ----------
def q_high_value_orders(db, status="completed", min_total=1000, limit=50, **kw):
    limit = int(limit); min_total = float(min_total)
    return list(db.orders.find(
        {"status": status, "total": {"$gte": min_total}},
        {"_id": 0, "order_id": 1, "customer_id": 1, "total": 1, "status": 1, "order_date": 1}
    ).sort("total", -1).limit(limit))


def e_high_value_orders(db, status="completed", min_total=1000, **kw):
    return db.command({
        "explain": {
            "find": "orders",
            "filter": {"status": status, "total": {"$gte": float(min_total)}},
            "sort": {"total": -1},
        },
        "verbosity": "executionStats",
    })


# ---------- Query 3 ----------
def q_recent_orders(db, days=30, limit=100, **kw):
    days = int(days); limit = int(limit)
    since = datetime.utcnow() - timedelta(days=days)
    return list(db.orders.find(
        {"order_date": {"$gte": since}},
        {"_id": 0, "order_id": 1, "order_date": 1, "city": 1, "total": 1}
    ).sort("order_date", -1).limit(limit))


def e_recent_orders(db, days=30, **kw):
    days = int(days)
    since = datetime.utcnow() - timedelta(days=days)
    return db.command({
        "explain": {
            "find": "orders",
            "filter": {"order_date": {"$gte": since}},
            "sort": {"order_date": -1},
        },
        "verbosity": "executionStats",
    })


# ---------- Query 4 ----------
def q_orders_by_product(db, product_id="P001", limit=50, **kw):
    limit = int(limit)
    return list(db.orders.find(
        {"product_id": product_id},
        {"_id": 0, "order_id": 1, "product_id": 1, "product_name": 1,
         "quantity": 1, "total": 1, "order_date": 1}
    ).sort("order_date", -1).limit(limit))


def e_orders_by_product(db, product_id="P001", **kw):
    return db.command({
        "explain": {
            "find": "orders",
            "filter": {"product_id": product_id},
        },
        "verbosity": "executionStats",
    })


# ---------- Query 5 ----------
def q_customer_orders(db, customer_id="C001", limit=100, **kw):
    limit = int(limit)
    return list(db.orders.find(
        {"customer_id": customer_id},
        {"_id": 0, "order_id": 1, "customer_id": 1, "total": 1, "status": 1, "order_date": 1}
    ).sort("order_date", -1).limit(limit))


def e_customer_orders(db, customer_id="C001", **kw):
    return db.command({
        "explain": {
            "find": "orders",
            "filter": {"customer_id": customer_id},
        },
        "verbosity": "executionStats",
    })


# ---------- Registry ----------
QUERIES = {
    "orders_by_city_date": {
        "description": "طلبات مدينة معيّنة خلال نطاق زمني (يستخدم فهرس مركّب city+date).",
        "params": {"city": "str", "start": "ISO date", "end": "ISO date", "limit": "int"},
        "run": q_orders_by_city_date,
        "explain": e_orders_by_city_date,
    },
    "high_value_orders": {
        "description": "طلبات مرتفعة القيمة حسب الحالة.",
        "params": {"status": "str", "min_total": "float", "limit": "int"},
        "run": q_high_value_orders,
        "explain": e_high_value_orders,
    },
    "recent_orders": {
        "description": "أحدث الطلبات خلال آخر N يوم.",
        "params": {"days": "int", "limit": "int"},
        "run": q_recent_orders,
        "explain": e_recent_orders,
    },
    "orders_by_product": {
        "description": "كل الطلبات التي تحتوي منتجًا معيّنًا.",
        "params": {"product_id": "str", "limit": "int"},
        "run": q_orders_by_product,
        "explain": e_orders_by_product,
    },
    "customer_orders": {
        "description": "كل طلبات زبون معيّن.",
        "params": {"customer_id": "str", "limit": "int"},
        "run": q_customer_orders,
        "explain": e_customer_orders,
    },
}


def run_query(name: str, db, **params):
    if name not in QUERIES:
        raise KeyError(name)
    docs = QUERIES[name]["run"](db, **params)
    return docs


def explain_query(name: str, db, **params):
    if name not in QUERIES:
        raise KeyError(name)
    raw = QUERIES[name]["explain"](db, **params)
    return {"summary": _summarize_explain(raw), "raw": raw}
