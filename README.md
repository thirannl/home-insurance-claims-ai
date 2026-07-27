# Home Insurance Claims AI

AI-powered platform for processing, analysing, and managing home insurance claims end-to-end.

---

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows: venv\Scripts\activate | macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # fill in your credentials
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## Documentation

- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)
