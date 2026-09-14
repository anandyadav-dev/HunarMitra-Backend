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
        radius_km: float = 10.0
    ) -> List[Worker]:
        """
        Find online workers within a radius of (lat, lng).
        Uses a bounding-box DB query first, then Haversine formula filtering for correctness.
        """
        # Base query for online workers
        query = db.query(Worker).filter(Worker.availability_status == True)
        
        if category:
            query = query.filter(Worker.category.ilike(category))
        
        # Calculate bounding box offsets (1 degree lat ~= 111 km)
        lat_delta = radius_km / 111.0
        # Protect against division by zero at poles
        cos_lat = math.cos(math.radians(lat))
        if abs(cos_lat) < 0.001:
            lng_delta = radius_km / 111.0
        else:
            lng_delta = radius_km / (111.0 * abs(cos_lat))
            
        # Apply bounding box filters to utilize DB indexes
        query = query.filter(
            and_(
                Worker.location_lat >= lat - lat_delta,
                Worker.location_lat <= lat + lat_delta,
                Worker.location_lng >= lng - lng_delta,
                Worker.location_lng <= lng + lng_delta
            )
        )
        
        workers = query.all()
        nearby_workers = []
        
        # Refine distance using Haversine formula
        for w in workers:
            if w.location_lat is None or w.location_lng is None:
                continue
            
            w_lat = float(w.location_lat)
            w_lng = float(w.location_lng)
            
            d_lat = math.radians(w_lat - lat)
            d_lng = math.radians(w_lng - lng)
            
            a = (math.sin(d_lat / 2) ** 2 + 
                 math.cos(math.radians(lat)) * math.cos(math.radians(w_lat)) * 
                 math.sin(d_lng / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance = 6371.0 * c  # Earth radius in km
            
            if distance <= radius_km:
                w.distance_km = round(distance, 2)
                nearby_workers.append(w)
                
        # Sort by proximity
        nearby_workers.sort(key=lambda x: getattr(x, "distance_km", 0.0))
        return nearby_workers

worker = CRUDWorker(Worker)
