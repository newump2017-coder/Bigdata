# Big Data Project — Phase 2 (Final)

## نظرة عامة
مشروع نهائي مبني على المشروع النصفي (Phase 1) داخل نفس مستودع GitHub.
يضيف: 5 استعلامات + 5 فهارس (منها مركّبة) + Explain، 5 Aggregations،
2 Materialized Views، 2 Scheduled Jobs، وواجهة API موحّدة بـ FastAPI.

## المتطلبات
- Python 3.10+
- MongoDB 4.4+ (يُفضّل 6+)

## التثبيت
```bash
git clone <repo-url>
cd bigdata-phase2
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # عدّل MONGO_URI إذا لزم
```

## توليد بيانات تجريبية (اختياري)
```bash
python scripts/generate_sample_data.py
```

## تشغيل الـAPI
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Swagger UI: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

## سيناريو تشغيل كامل
1) إنشاء الفهارس:
```bash
curl -X POST http://localhost:8000/indexes
```
2) إدخال البيانات (نفس Pipeline المشروع النصفي):
```bash
curl -X POST http://localhost:8000/ingest \
     -H "Content-Type: application/json" \
     -d '{"collection":"orders","path":"data/orders.json"}'
```
3) الاستعلامات:
```bash
curl "http://localhost:8000/queries"
curl "http://localhost:8000/queries/orders_by_city_date?city=Cairo&start=2024-01-01&end=2024-12-31"
curl "http://localhost:8000/queries/orders_by_city_date?city=Cairo&explain=true"
```
4) Aggregations:
```bash
curl "http://localhost:8000/aggregations"
curl "http://localhost:8000/aggregations/top_products?limit=10"
```
5) Materialized Views:
```bash
curl -X POST http://localhost:8000/refresh-mv \
     -H "Content-Type: application/json" -d '{"name":"all"}'
curl "http://localhost:8000/materialized-views/daily_sales_summary"
```
6) Jobs:
```bash
curl "http://localhost:8000/jobs"
curl -X POST http://localhost:8000/jobs/refresh_daily_sales/run
```

## الفهارس
| Name | Keys | Reason |
|---|---|---|
| idx_orders_order_date | (order_date) | نطاقات زمنية |
| idx_orders_city_date **(Compound)** | (city, order_date desc) | مدينة + تاريخ |
| idx_orders_status_total **(Compound)** | (status, total desc) | تصفية + ترتيب |
| idx_orders_product_id | (product_id) | ربط المنتجات |
| idx_orders_customer_id | (customer_id) | طلبات الزبون |

**Explain:** كل استعلام يدعم `?explain=true` لعرض `executionStats`
(`executionTimeMillis`, `totalKeysExamined`, `totalDocsExamined`, `nReturned`،
والـ`stage` و`index_used`).

## Materialized Views
| Name | Source | Target | Refresh |
|---|---|---|---|
| daily_sales_summary | orders | mv_daily_sales_summary | يوميًا 00:00 / يدويًا |
| top_products_summary | orders | mv_top_products_summary | كل ساعة / يدويًا |

يستخدم `$out` لتحديث ذرّي كامل (full replace) — أي أن إعادة البناء لا تكرّر البيانات.

## Scheduled Jobs
| Job | Schedule | Description |
|---|---|---|
| refresh_daily_sales | Cron 00:00 يوميًا | تحديث daily_sales_summary |
| refresh_top_products | Cron كل ساعة | تحديث top_products_summary |

كل وظيفة تُسجّل النجاح/الفشل في اللوج وتُعيد `affected_docs`.

## Endpoints الموحّدة
| Method | Path |
|---|---|
| GET | /health |
| POST | /ingest |
| POST | /indexes |
| GET | /queries |
| GET | /queries/{name} (يدعم `?explain=true`) |
| GET | /aggregations |
| GET | /aggregations/{name} |
| POST | /refresh-mv |
| GET | /materialized-views |
| GET | /materialized-views/{name} |
| GET | /jobs |
| POST | /jobs/{name}/run |

## ملاحظات
- الـAPI ليست Backend مستقلًا؛ هي طبقة تشغيل فوق نفس Pipeline المشروع النصفي.
- لا يُعتمد على أسماء ملفات أو أعداد سجلات ثابتة داخل الكود — كل الاستعلامات معاملية.
- لا يحتوي المشروع على أي بيانات حساسة (فقط `.env.example`).
