from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.service import Service
from app.models.legal_document import LegalDocument
from app.schemas.service import ServiceResponse
from app.schemas.legal_document import LegalDocumentResponse

router = APIRouter()

@router.get("/categories", response_model=List[ServiceResponse])
def get_categories(db: Session = Depends(get_db)):
    """
    Get all available service categories for the mobile app.
    No authentication required to view categories.
    """
    categories = db.query(Service).all()
    return categories

@router.get("/legal-documents", response_model=List[LegalDocumentResponse])
def get_public_legal_documents(db: Session = Depends(get_db)):
    """
    Publicly list active legal documents without requiring login.
    """
    return db.query(LegalDocument).filter(
        LegalDocument.is_deleted == False,
        LegalDocument.is_active == True
    ).all()

@router.get("/legal-documents/{slug}", response_model=LegalDocumentResponse)
def get_public_legal_document_by_slug(slug: str, db: Session = Depends(get_db)):
    """
    Publicly fetch Privacy Policy or Terms & Conditions by slug without requiring login.
    """
    doc = db.query(LegalDocument).filter(
        LegalDocument.slug == slug,
        LegalDocument.is_deleted == False,
        LegalDocument.is_active == True
    ).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Legal document not found"
        )
    return doc

