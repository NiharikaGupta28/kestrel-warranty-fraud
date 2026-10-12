"""Run:  uvicorn app.main:app --port 8000   then open http://127.0.0.1:8000"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from scoring import score_claim, ScoringError, _load

app = FastAPI(title="Kestrel claim risk scorer")
HERE = os.path.dirname(os.path.abspath(__file__))

@app.get("/health")
def health():
    try:
        _load(); return {"status": "ok"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "model not ready", "detail": str(e)})

@app.post("/score")
async def score(request: Request):
    try:
        rec = await request.json()
        if not isinstance(rec, dict):
            raise ScoringError("Send one claim as a JSON object")
        return score_claim(rec)
    except ScoringError as e:
        return JSONResponse(status_code=422, content={"error": str(e)})
    except RuntimeError as e:
        return JSONResponse(status_code=503, content={"error": str(e)})
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Could not read the request. Send valid JSON."})

@app.get("/", response_class=HTMLResponse)
def home():
    return open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
