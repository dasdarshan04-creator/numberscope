"""NumberScope REST API (FastAPI).

A thin HTTP layer over the same local ``numberscope`` core that powers the
Streamlit UI and the CLI — "one engine, three interfaces". It performs no
network lookups and stores nothing.

Run:
    uvicorn api:app --reload
Then open the interactive docs at http://127.0.0.1:8000/docs
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from numberscope import __version__, analyse_number, metadata_version

app = FastAPI(
    title="NumberScope API",
    version=__version__,
    description=(
        "Analyse **public phone-number numbering-plan metadata** locally. "
        "No subscriber lookup, no live location, no network calls."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class AnalyseRequest(BaseModel):
    number: str = Field(..., examples=["+919876543210"])
    region: str = Field("IN", examples=["IN"], description="Default region for non-'+' input.")


class BatchRequest(BaseModel):
    numbers: list[str] = Field(..., examples=[["+919876543210", "+14155552671"]])
    region: str = Field("IN", examples=["IN"])


@app.get("/health", tags=["meta"])
def health() -> dict[str, Any]:
    return {"status": "ok", "metadata_version": metadata_version(), "version": __version__}


@app.post("/analyse", tags=["analysis"])
def analyse(request: AnalyseRequest) -> dict[str, Any]:
    """Analyse a single number and return its numbering-plan metadata."""
    try:
        return analyse_number(request.number, request.region).as_dict()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/batch", tags=["analysis"])
def batch(request: BatchRequest) -> dict[str, Any]:
    """Analyse many numbers; returns parsed results and per-input errors."""
    results, errors = [], []
    for number in request.numbers:
        try:
            results.append(analyse_number(number, request.region).as_dict())
        except ValueError as exc:
            errors.append({"input": number, "error": str(exc)})
    return {"count": len(results), "results": results, "errors": errors}
