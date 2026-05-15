# Phase 1 usage snippet

## 1. Start the database

```bash
docker compose up -d
```

## 2. Install and run the backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env

python -m app.cli sources
python -m app.cli ingest generic_csv_sample

uvicorn app.main:app --reload
```

## 3. Pick a dataset

Use the starter dataset:

```text
generic_csv_sample
```

It contains sample observations for:

```text
Multnomah / Portland
Lane / Eugene
Jackson / Medford
```

## 4. Query by region

After applying the Phase 2 backend patch:

```bash
curl "http://127.0.0.1:8000/observations/query?county=Multnomah"
```

Or by bounding box:

```bash
curl "http://127.0.0.1:8000/observations/query?bbox=-123,45,-122,46"
```

The bbox format is:

```text
minLongitude,minLatitude,maxLongitude,maxLatitude
```

## 5. Open the dashboard

```bash
cd apps/web-dashboard
npm install
npm run dev
```
