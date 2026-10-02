"""
5 Aggregation Reports حسب متطلبات المشروع.
"""
def _round(expr, n=2):
    return {"$round": [expr, n]}


# 1) إجمالي المبيعات حسب المدينة
def agg_sales_by_city(db, **kw):
    return list(db.orders.aggregate([
        {"$match": {"status": {"$ne": "cancelled"}}},
        {"$group": {
            "_id": "$city",
            "total_revenue": {"$sum": "$total"},
            "orders": {"$sum": 1},
            "avg_order_value": {"$avg": "$total"},
        }},
        {"$sort": {"total_revenue": -1}},
        {"$project": {
            "_id": 0, "city": "$_id",
            "total_revenue": _round("$total_revenue"),
            "orders": 1,
            "avg_order_value": _round("$avg_order_value"),
        }},
    ]))


# 2) أفضل المنتجات مبيعًا (كمية + إيراد)
def agg_top_products(db, limit=20, **kw):
    limit = int(limit)
    return list(db.orders.aggregate([
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
        {"$limit": limit},
        {"$project": {
            "_id": 0, "product_id": "$_id",
            "product_name": 1, "category": 1,
            "total_quantity": 1,
            "total_revenue": _round("$total_revenue"),
            "orders_count": 1,
        }},
    ]))


# 3) المبيعات الشهرية
def agg_monthly_sales(db, **kw):
    return list(db.orders.aggregate([
        {"$match": {"status": {"$ne": "cancelled"}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$order_date"}},
            "total_revenue": {"$sum": "$total"},
            "orders": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
        {"$project": {
            "_id": 0, "month": "$_id",
            "total_revenue": _round("$total_revenue"),
            "orders": 1,
        }},
    ]))


# 4) الإيراد حسب التصنيف
def agg_sales_by_category(db, **kw):
    return list(db.orders.aggregate([
        {"$match": {"status": {"$ne": "cancelled"}}},
        {"$group": {
            "_id": "$category",
            "total_revenue": {"$sum": "$total"},
            "total_quantity": {"$sum": "$quantity"},
            "orders": {"$sum": 1},
        }},
        {"$sort": {"total_revenue": -1}},
        {"$project": {
            "_id": 0, "category": "$_id",
            "total_revenue": _round("$total_revenue"),
            "total_quantity": 1, "orders": 1,
        }},
    ]))


# 5) أعلى الزبائن إنفاقًا
def agg_top_customers(db, limit=20, **kw):
    limit = int(limit)
    return list(db.orders.aggregate([
        {"$match": {"status": {"$ne": "cancelled"}}},
        {"$group": {
            "_id": "$customer_id",
            "total_spent": {"$sum": "$total"},
            "orders": {"$sum": 1},
            "avg_order_value": {"$avg": "$total"},
        }},
        {"$sort": {"total_spent": -1}},
        {"$limit": limit},
        {"$project": {
            "_id": 0, "customer_id": "$_id",
            "total_spent": _round("$total_spent"),
            "orders": 1,
            "avg_order_value": _round("$avg_order_value"),
        }},
    ]))


AGGREGATIONS = {
    "sales_by_city": {
        "description": "إجمالي المبيعات وعدد الطلبات ومتوسط قيمة الطلب لكل مدينة.",
        "params": {},
        "run": agg_sales_by_city,
    },
    "top_products": {
        "description": "أفضل المنتجات من حيث الكمية والإيراد.",
        "params": {"limit": "int"},
        "run": agg_top_products,
    },
    "monthly_sales": {
        "description": "إجمالي المبيعات والطلبات لكل شهر.",
        "params": {},
        "run": agg_monthly_sales,
    },
    "sales_by_category": {
        "description": "الإيراد والكمية والطلبات حسب تصنيف المنتج.",
        "params": {},
        "run": agg_sales_by_category,
    },
    "top_customers": {
        "description": "أعلى الزبائن إنفاقًا.",
        "params": {"limit": "int"},
        "run": agg_top_customers,
    },
}


def run_aggregation(name: str, db, **params):
    if name not in AGGREGATIONS:
        raise KeyError(name)
    return AGGREGATIONS[name]["run"](db, **params)
