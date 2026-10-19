"""FastAPI backend: mock Vahan API + /verify endpoint that fuses rules + ML + Vahan.
Run:  uvicorn server:app --reload --host 0.0.0.0 --port 8000
Docs: http://localhost:8000/docs
"""
import joblib
from fastapi import FastAPI
from pydantic import BaseModel
from scipy.sparse import hstack
import rules

app = FastAPI(title="ChallanGuard")
_m = joblib.load("models/sms_model.joblib")

# ---------- MOCK Vahan (replace with the real API if you ever get authorised access) ----------
MOCK_VAHAN = {
    "TN09AB1234": {"owner_state": "TN", "challans": [{"id": "TN2609001", "amount": 500, "status": "pending"}]},
    "KA01MN4321": {"owner_state": "KA", "challans": []},
    "MH12XY9999": {"owner_state": "MH", "challans": [{"id": "MH2608777", "amount": 1000, "status": "pending"}]},
}

@app.get("/mock-vahan/{plate}")
def mock_vahan(plate: str):
    rec = MOCK_VAHAN.get(plate.upper())
    return {"found": rec is not None, "data": rec}

def vahan_lookup(plate):
    return mock_vahan(plate)   # in production: requests.get(REAL_API_URL, ...)

# ---------- ML ----------
def ml_scam_prob(text):
    X = hstack([_m["word"].transform([text]), _m["char"].transform([text])])
    return float(_m["clf"].predict_proba(X)[0][1])

# ---------- Fusion ----------
class SMS(BaseModel):
    text: str
    sender: str | None = None

@app.post("/verify")
def verify(sms: SMS):
    r = rules.analyze(sms.text)
    p_ml = ml_scam_prob(sms.text)
    reasons = []
    vahan_flag = 0.0

    if r["claims_challan"]:
        if not r["plates"]:
            vahan_flag = 0.3; reasons.append("Claims a challan but gives no valid vehicle number")
        for plate in r["plates"]:
            v = vahan_lookup(plate)
            if not v["found"]:
                vahan_flag = max(vahan_flag, 0.6); reasons.append(f"{plate}: no record in Vahan")
            elif not v["data"]["challans"]:
                vahan_flag = max(vahan_flag, 1.0); reasons.append(f"{plate}: NO pending challan in official records")
            else:
                reasons.append(f"{plate}: pending challan exists in official records")
    for u in r["urls"]:
        if not u["official"]:
            reasons.append(f"Link {u['host']} is not an official .gov.in domain ({', '.join(u['flags'])})")

    score = 0.35 * p_ml + 0.35 * r["rule_score"] + 0.30 * vahan_flag
    # hard rule: challan claim + non-official link = never "safe"
    if r["claims_challan"] and any(not u["official"] for u in r["urls"]):
        score = max(score, 0.6)
    verdict = "SCAM" if score >= 0.6 else "SUSPICIOUS" if score >= 0.35 else "SAFE"
    return {"verdict": verdict, "score": round(score, 2), "ml_prob": round(p_ml, 2),
            "rule_score": r["rule_score"], "reasons": reasons, "details": r}