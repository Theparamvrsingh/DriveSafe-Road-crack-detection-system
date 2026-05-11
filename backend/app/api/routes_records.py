from __future__ import annotations

from fastapi import APIRouter, Query

from app.db.sqlite import list_records

router = APIRouter()


@router.get("/records")
def records(limit: int = Query(default=200, ge=1, le=2000)):
    return {"items": list_records(limit=limit)}

