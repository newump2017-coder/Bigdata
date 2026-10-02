"""
Index definitions. At least one Compound Index is required.
Each index has a documented justification.
"""
from .database import db

INDEX_DEFS = [
    {
        "name": "idx_orders_order_date",
        "collection": "orders",
        "keys": [("order_date", 1)],
        "reason": "تسريع الاستعلامات المعتمدة على نطاق زمني (recent_orders).",
    },
    {
        "name": "idx_orders_city_date",     # ✅ Compound Index
        "collection": "orders",
        "keys": [("city", 1), ("order_date", -1)],
        "reason": "فهرس مركّب لتسريع استعلامات (المدينة + التاريخ) مع الترتيب التنازلي.",
    },
    {
        "name": "idx_orders_status_total",  # ✅ Compound Index
        "collection": "orders",
        "keys": [("status", 1), ("total", -1)],
        "reason": "فهرس مركّب لتصفية الحالة وترتيب القيمة (high_value_orders).",
    },
    {
        "name": "idx_orders_product_id",
        "collection": "orders",
        "keys": [("product_id", 1)],
        "reason": "لتسريع الربط مع مجموعة المنتجات.",
    },
    {
        "name": "idx_orders_customer_id",
        "collection": "orders",
        "keys": [("customer_id", 1)],
        "reason": "لتسريع استعلامات الزبون الواحد.",
    },
]


def create_indexes() -> list:
    created = []
    for spec in INDEX_DEFS:
        col = db[spec["collection"]]
        name = col.create_index(spec["keys"], name=spec["name"])
        created.append({
            "collection": spec["collection"],
            "name": name,
            "keys": spec["keys"],
            "reason": spec["reason"],
        })
    return created


def list_indexes() -> dict:
    out = {}
    for spec in INDEX_DEFS:
        col = db[spec["collection"]]
        out.setdefault(spec["collection"], [])
        for ix in col.list_indexes():
            out[spec["collection"]].append({
                "name": ix["key"][0] if False else ix.get("name"),
                "keys": list(ix["key"].items()),
            })
    return out
