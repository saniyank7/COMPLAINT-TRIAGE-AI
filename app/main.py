from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app import db
from app.llm import run_triage

app = FastAPI(title="Complaint Triage Service")

templates = Jinja2Templates(directory="templates")


class ComplaintIn(BaseModel):
    text: str = Field(min_length=10, max_length=10000)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/triage")
def triage(body: ComplaintIn):
    try:
        result, meta = run_triage(body.text)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"LLM call failed: {type(e).__name__}"
        )

    db.log_result(len(body.text), result, meta)
    db.save_complaint_for_dashboard(body.text, result, meta)

    if result is None:
        raise HTTPException(
            status_code=422,
            detail=f"Model output invalid: {meta['error']}"
        )

    return {**result.model_dump(), "latency_ms": meta["latency_ms"]}


@app.get("/stats")
def stats():
    return db.stats()

@app.get("/banker/complaints")
def banker_complaints():
    return db.get_complaints_for_dashboard()
@app.post("/submit-complaint")
def submit_complaint(body: ComplaintIn):
    try:
        result, meta = run_triage(body.text)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Complaint processing failed: {type(e).__name__}"
        )

    if result is None:
        raise HTTPException(
            status_code=422,
            detail="Unable to process the complaint."
        )

    # Save full AI analysis for the banker dashboard
    db.log_result(len(body.text), result, meta)
    complaint_id = db.save_complaint_for_dashboard(
        body.text,
        result,
        meta
    )

    # Customer receives ONLY confirmation
    return {
        "status": "submitted",
        "complaint_id": complaint_id
    }

@app.get("/banker", response_class=HTMLResponse)
def banker_dashboard(request: Request):
    return templates.TemplateResponse(
        request = request,
        name="banker.html",
    )