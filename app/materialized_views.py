"""
Materialized Views مبنية على نتائج Aggregations.
يُعاد بناؤها بالكامل عبر $out (تحديث ذرّي كامل للمجموعة الهدف).
"""
from .database import db


def _daily_sales_pipeline(db):
    return [
        {"$match": {"status": {"$ne": "cancelled"}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$order_date"}},
            "total_orders": {"$sum": 1},
            "total_revenue": {"$sum": "$total"},
            "total_items": {"$sum": "$quantity"},
            "avg_order_value": {"$avg": "$total"},
        }},
        {"$project": {
            "_id": 0,
            "date": "$_id",
            "total_orders": 1,
            "total_items": 1,
            "total_revenue": {"$round": ["$total_revenue", 2]},
            "avg_order_value": {"$round": ["$avg_order_value", 2]},
        }},
        {"$sort": {"date": 1}},
    ]


def _top_products_pipeline(db):
    return [
        {"$match": {"status": {"$ne": "cancelled"}}},
        {"$group": {
            "_id": "$product_id",
            "product_name": {"$first": "$product_name"},
            "category": {"$first": "$category"},
            "total_quantity": {"$sum": "$quantity"},
            "total_revenue": {"$sum": "$total"},
            "orders_count": {"$sum": 1},
        }},
        {"$sort": {"total_revenue": -1}},
        {"$limit": 50},
        {"$project": {
            "_id": 0,
            "product_id": "$_id",
            "product_name": 1,
            "category": 1,
            "total_quantity": 1,
            "orders_count": 1,
            "total_revenue": {"$round": ["$total_revenue", 2]},
        }},
    ]


MV_DEFS = {
    "daily_sales_summary": {
        "source": "orders",
        "target": "mv_daily_sales_summary",
        "pipeline": _daily_sales_pipeline,
        "description": "ملخص المبيعات اليومية (إجمالي الطلبات، الإيراد، متوسط قيمة الطلب).",
    },
    "top_products_summary": {
        "source": "orders",
        "target": "mv_top_products_summary",
        "pipeline": _top_products_pipeline,
        "description": "ملخص أفضل المنتجات (الكمية، الإيراد، عدد الطلبات).",
    },
}


def refresh_mv(name: str) -> int:
    if name not in MV_DEFS:
        raise KeyError(name)
    spec = MV_DEFS[name]
    pipeline = spec["pipeline"](db) + [{"$out": spec["target"]}]
    db[spec["source"]].aggregate(pipeline)
    return db[spec["target"]].count_documents({})


def refresh_all() -> dict:
    return {name: refresh_mv(name) for name in MV_DEFS}


def read_mv(name: str, limit: int = 100):
    if name not in MV_DEFS:
        raise KeyError(name)
    return list(db[MV_DEFS[name]["target"]].find({}, {"_id": 0}).limit(int(limit)))
