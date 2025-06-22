# QuantumVault Demo

This project includes a minimal FastAPI backend and a static frontend. The
backend connects to MongoDB using the `MONGODB_URL` environment variable.

## Running locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start MongoDB (or use Docker compose):
   ```bash
   docker-compose up mongodb
   ```
3. Run the API server:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Open `index.html` in a browser to use the frontend.

The `/api/health` endpoint checks database connectivity and the `/api/users`
endpoint lists users from the `users` collection.
