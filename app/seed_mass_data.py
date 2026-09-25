import os
import sys
import random
from decimal import Decimal
from faker import Faker

# Add backend root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core import security
from app.core.database import SessionLocal
from app.models.user import User
from app.models.role import Role
from app.models.worker import Worker, KycStatus
from app.models.contractor import Contractor
from app.models.wallet import Wallet
from app.models.service import Service

fake = Faker('en_IN')

def seed_database():
    db = SessionLocal()
    try:
        print("Starting Mass Database Seeding...")

        # 1. Fetch Roles
        customer_role = db.query(Role).filter(Role.name == "customer").first()
        worker_role = db.query(Role).filter(Role.name == "worker").first()
        contractor_role = db.query(Role).filter(Role.name == "contractor").first()

        if not all([customer_role, worker_role, contractor_role]):
            print("Roles not found. Run the initial seed script first.")
            return
            
        services = db.query(Service).all()
        categories = [s.name for s in services]
        if not categories:
            categories = ["Plumber", "Electrician", "Carpenter", "Beautician", "Mason", "Painter"]
            for c in categories:
                role = Role(name=c.lower(), description=f"{c} Role")
                db.add(role)
                svc = Service(name=c, base_price=Decimal("150.00"), icon_url=f"/static/icons/{c.lower()}.png")
                db.add(svc)
            db.commit()
            services = db.query(Service).all()

        service_roles = {r.name: r for r in db.query(Role).all()}

        # Generate 10 Customers
        print("Seeding 10 Customers...")
        for i in range(10):
            phone = f"+9199{random.randint(10000000, 99999999)}"
            cust = User(
                phone_number=phone,
                full_name=fake.name(),
                language_preference="English",
                is_verified=True
            )
            cust.roles.append(customer_role)
            db.add(cust)
            db.flush()
            wallet = Wallet(user_id=cust.id, balance=Decimal(random.randint(500, 5000)))
            db.add(wallet)
        db.commit()

        # Generate 10 Contractors
        print("Seeding 10 Contractors...")
        for i in range(10):
            phone = f"+9177{random.randint(10000000, 99999999)}"
            cont = User(
                phone_number=phone,
                full_name=fake.name(),
                language_preference="English",
                is_verified=True
            )
            cont.roles.append(contractor_role)
            db.add(cont)
            db.flush()
            wallet = Wallet(user_id=cont.id, balance=Decimal("0.00"))
            db.add(wallet)
            
            c_profile = Contractor(
                user_id=cont.id,
                company_name=fake.company(),
                gst_number=f"07{fake.bothify('?????####?')}1Z1",
                pan_number=fake.bothify('?????####?').upper(),
                kyc_status=KycStatus.approved,
                profile_picture="/uploads/kyc/company_logo.png",
                business_license="/uploads/kyc/business_license.png"
            )
            db.add(c_profile)
        db.commit()

        # Generate 100 Workers
        print("Seeding 100 Workers...")
        for i in range(100):
            phone = f"+9188{random.randint(10000000, 99999999)}"
            cat = random.choice(categories)
            work_usr = User(
                phone_number=phone,
                full_name=fake.name(),
                language_preference="English",
                is_verified=True
            )
            work_usr.roles.append(worker_role)
            if cat.lower() in service_roles:
                work_usr.roles.append(service_roles[cat.lower()])
                
            db.add(work_usr)
            db.flush()
            
            wallet = Wallet(user_id=work_usr.id, balance=Decimal(random.randint(0, 3000)))
            db.add(wallet)
            
            # Scatter coordinates slightly around Connaught Place (28.6304, 77.2177)
            # 1 degree is roughly 111km. We want them within say 50km
            lat = 28.6304 + random.uniform(-0.3, 0.3)
            lng = 77.2177 + random.uniform(-0.3, 0.3)
            
            w_profile = Worker(
                user_id=work_usr.id,
                category=cat,
                experience_years=random.randint(1, 15),
                pricing_per_hour=Decimal(random.randint(100, 500)),
                rating=Decimal(round(random.uniform(3.0, 5.0), 2)),
                total_jobs_done=random.randint(0, 50),
                availability_status="available_now",
                location_lat=lat,
                location_lng=lng,
                working_radius_km=100,
                kyc_status=KycStatus.approved,
                profile_picture="/uploads/kyc/worker_selfie.jpg",
                aadhaar_number=f"{random.randint(100000000000, 999999999999)}"
            )
            db.add(w_profile)
        db.commit()

        print("Mass Database Seeding Completed Successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
