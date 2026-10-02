"""يولّد بيانات تجريبية orders.json (1000 طلب) لاختبار المشروع."""
import json, random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

PRODUCTS = [
    ("P001", "Laptop",     "Electronics", 1200),
    ("P002", "Phone",      "Electronics",  800),
    ("P003", "Headphones", "Audio",        150),
    ("P004", "Book-A",     "Books",         25),
    ("P005", "Book-B",     "Books",         30),
    ("P006", "T-Shirt",    "Clothing",      20),
    ("P007", "Jeans",      "Clothing",      60),
    ("P008", "Coffee",     "Food",          15),
    ("P009", "Backpack",   "Accessories",   80),
    ("P010", "Watch",      "Accessories",  250),
]
CITIES = ["Cairo", "Giza", "Alexandria", "Mansoura", "Aswan"]
STATUSES = ["completed", "completed", "completed", "pending", "cancelled"]

start = datetime(2024, 1, 1)
rows = []
for i in range(1000):
    pid, pname, cat, price = random.choice(PRODUCTS)
    qty = random.randint(1, 4)
    total = qty * price
    rows.append({
        "order_id": f"ORD{i+1:05d}",
        "customer_id": f"C{random.randint(1, 100):03d}",
        "product_id": pid,
        "product_name": pname,
        "category": cat,
        "quantity": qty,
        "price": price,
        "total": total,
        "status": random.choice(STATUSES),
        "city": random.choice(CITIES),
        "order_date": (start + timedelta(days=random.randint(0, 364),
                                         hours=random.randint(0, 23))).isoformat(),
    })

out = Path(__file__).resolve().parent.parent / "data" / "orders.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
print(f"wrote {len(rows)} orders → {out}")
