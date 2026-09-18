# NyayVault

NyayVault is a FastAPI + static HTML/CSS/JavaScript digital evidence management demo. The frontend and backend are connected and served by one FastAPI process.

## Run

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python seed_data.py
uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/`.


## Demo accounts

Password for all approved demo accounts: `NyayVault@123`

- `officer.sharma` — role `io`
- `dr.rao` — role `forensic`
- `justice.verma` — role `judge`
- `admin` — role `admin`
- `officer.bhatt` — role `io`, pending approval (intentionally cannot log in until approved)

The login page uses the real `/api/auth/login` endpoint and JWT authentication. Dashboard cases/documents are loaded from the database, evidence upload uses the backend upload endpoint and real SHA-256 hashing, forensic verification calls the real integrity endpoint, search calls the API, and admin user approval/revocation uses backend RBAC endpoints.

API documentation is available at `/docs` while the app is running.
