# ...existing code...
## Prerequisites
- On Ubuntu, install the following packages:
  sudo apt-get update && sudo apt-get install libffi-dev python3-dev build-essential
# ...existing code...
To start the FastAPI server and access it in the browser, you can use:

```bash
# From the backend directory
uvicorn main:app --reload --host 0.0.0.0 --port 8000

Create an Alembic migration
Run alembic revision --autogenerate -m "add feed history table"
Run alembic upgrade head
```

Once running, you can access:
- Browser UI: `http://localhost:8000`
- API Docs: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc` 

However, for testing the endpoints you listed you'll need to:

1. First get a token:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your@email.com&password=yourpassword"
```

2. Then use the token in your requests:
```bash
# Get articles
curl http://localhost:8000/api/v1/articles \
  -H "X-API-Version: 1.0" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Create article
curl -X POST http://localhost:8000/api/v1/articles \
  -H "X-API-Version: 1.0" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Would you like me to help you test specific endpoints or set up a test user?