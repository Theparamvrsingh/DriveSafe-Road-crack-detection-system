## DriveSafe Road Crack Detection System (Backend)

### Run locally

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API

- `GET /api/health`
- `POST /api/infer` (multipart form)
  - `file`: image
  - `lat` (optional), `lon` (optional)
  - `weights_path` (optional)
- `GET /api/records`

