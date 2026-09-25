import os
import sys
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.service import Service
from app.models.role import Role

def seed_categories():
    db = SessionLocal()
    categories = [
        "Plumber", "Electrician", "Carpenter", "Painter", "Mason", 
        "Welder", "Mechanic", "Gardener", "Cleaning", "Laborer", 
        "Barber", "Beautician", "Driver", "Tailor", "Cook"
    ]
    
    count = 0
    for c in categories:
        if not db.query(Service).filter(Service.name == c).first():
            db.add(Service(
                name=c, 
                base_price=Decimal('100.00'), 
                icon_url=f"/static/icons/{c.lower()}.png"
            ))
            count += 1
            
        if not db.query(Role).filter(Role.name == c.lower()).first():
            db.add(Role(name=c.lower(), description=f"{c} Role"))
            
    db.commit()
    print(f"Added {count} new categories!")

if __name__ == "__main__":
    seed_categories()
