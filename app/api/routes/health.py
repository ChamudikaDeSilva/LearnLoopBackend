from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
async def health_check():
    return {
        "status": "ok",
        "message": "LearnLoop AI Backend is running",
    }


@router.get("/database")
def database_health_check(
    db: Session = Depends(get_db),
):
    db.execute(
        text("SELECT 1")
    )

    return {
        "status": "ok",
        "database": "connected",
        "message": "MariaDB connection successful",
    }