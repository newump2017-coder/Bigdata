from pymongo import MongoClient
from .config import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

orders_col    = db["orders"]
products_col  = db["products"]
customers_col = db["customers"]

# Materialized Views collections
mv_daily_sales_col  = db["mv_daily_sales_summary"]
mv_top_products_col = db["mv_top_products_summary"]
