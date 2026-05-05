"""Get api routes"""
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Events History"])

@router.get("")
def health():
    return {"status": "ok"}
