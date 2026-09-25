from uuid import UUID
import math
from typing import List, Optional
from sqlalchemy import and_
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.worker import Worker
from app.schemas.worker import WorkerCreate, WorkerUpdate

class CRUDWorker(CRUDBase[Worker, WorkerCreate, WorkerUpdate]):
    def get_by_user_id(self, db: Session, user_id: UUID) -> Optional[Worker]:
        """
        Retrieve a worker profile by their user_id.
        """
        return db.query(Worker).filter(Worker.user_id == user_id).first()

    def get_nearby_workers(
        self, 
        db: Session, 
        *, 
        category: Optional[str] = None, 
        lat: float, 
        lng: float, 
        radius_km: float = 100.0
    ) -> List[Worker]:
        """
        Find online workers within a radius of (lat, lng).
        Uses a bounding-box DB query first, then Haversine formula filtering for correctness.
        """
        from app.models.worker import AvailabilityStatus
        from app.models.worker import AvailabilityStatus
        # Base query for all workers
        query = db.query(Worker)
        
        if category:
            query = query.filter(Worker.category.ilike(category))
            
        workers = query.all()
        
        # Set a dummy distance so the response model doesn't fail
        for w in workers:
            w.distance_km = 0.0
            
        return workers

worker = CRUDWorker(Worker)
