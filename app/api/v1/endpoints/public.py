from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.service import Service
from app.schemas.service import ServiceResponse

router = APIRouter()

@router.get("/categories", response_model=List[ServiceResponse])
def get_categories(db: Session = Depends(get_db)):
    """
    Get all available service categories for the mobile app.
    No authentication required to view categories.
    """
    categories = db.query(Service).all()
    return categories
