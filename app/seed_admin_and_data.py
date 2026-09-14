import os
import sys
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

# Add backend root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core import security
from app.core.database import SessionLocal
from app.models.user import User
from app.models.role import Role
from app.models.worker import Worker, KycStatus
from app.models.contractor import Contractor
from app.models.booking import Booking, BookingStatus
from app.models.wallet import Wallet
from app.models.service import Service

def seed_database():
    db = SessionLocal()
    try:
        print("Starting Database Seeding...")

        # 1. Resolve Roles
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        customer_role = db.query(Role).filter(Role.name == "customer").first()
        worker_role = db.query(Role).filter(Role.name == "worker").first()
        contractor_role = db.query(Role).filter(Role.name == "contractor").first()
        
        plumber_role = db.query(Role).filter(Role.name == "plumber").first()
        electrician_role = db.query(Role).filter(Role.name == "electrician").first()
        carpenter_role = db.query(Role).filter(Role.name == "carpenter").first()
        beautician_role = db.query(Role).filter(Role.name == "beautician").first()
        
        civil_contractor_role = db.query(Role).filter(Role.name == "civil_contractor").first()
        plumbing_contractor_role = db.query(Role).filter(Role.name == "plumbing_contractor").first()

        # Seed basic roles if missing
        if not admin_role:
            admin_role = Role(name="admin", description="Admin Role")
            db.add(admin_role)
        if not customer_role:
            customer_role = Role(name="customer", description="Customer Role")
            db.add(customer_role)
        if not worker_role:
            worker_role = Role(name="worker", description="Worker Role")
            db.add(worker_role)
        if not contractor_role:
            contractor_role = Role(name="contractor", description="Contractor Role")
            db.add(contractor_role)
        db.commit()

        # Refresh roles
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        customer_role = db.query(Role).filter(Role.name == "customer").first()
        worker_role = db.query(Role).filter(Role.name == "worker").first()
        contractor_role = db.query(Role).filter(Role.name == "contractor").first()

        # 2. Seed Admin User
        admin_user = db.query(User).filter(User.phone_number == "+919999999900").first()
        if not admin_user:
            admin_user = User(
                phone_number="+919999999900",
                full_name="System Administrator",
                language_preference="English",
                is_verified=True,
                hashed_password=security.get_password_hash("admin123")
            )
            admin_user.roles.append(admin_role)
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            # Add Wallet
            admin_wallet = Wallet(user_id=admin_user.id, balance=Decimal("100000.00"))
            db.add(admin_wallet)
            db.commit()
            print("Created Admin user (+919999999900)")
        else:
            admin_user.hashed_password = security.get_password_hash("admin123")
            db.add(admin_user)
            db.commit()
            print("Updated Admin user (+919999999900) password")

        # 3. Seed Customers
        customer_data = [
            ("+919999999999", "Ramesh Kumar", Decimal("5000.00")),
            ("+919999999911", "Anjali Sharma", Decimal("2500.00")),
            ("+919999999922", "Vijay Verma", Decimal("1200.00")),
            ("+919999999933", "Priya Singh", Decimal("800.00"))
        ]
        
        customers = []
        for phone, name, balance in customer_data:
            cust = db.query(User).filter(User.phone_number == phone).first()
            if not cust:
                cust = User(
                    phone_number=phone,
                    full_name=name,
                    language_preference="English",
                    is_verified=True
                )
                cust.roles.append(customer_role)
                db.add(cust)
                db.commit()
                db.refresh(cust)
                
                wallet = Wallet(user_id=cust.id, balance=balance)
                db.add(wallet)
                db.commit()
                print(f"Created customer: {name} ({phone})")
            customers.append(cust)

        # 4. Resolve default Services
        plumber_service = db.query(Service).filter(Service.name == "Plumber").first()
        electrician_service = db.query(Service).filter(Service.name == "Electrician").first()
        carpenter_service = db.query(Service).filter(Service.name == "Carpenter").first()
        beautician_service = db.query(Service).filter(Service.name == "Beautician").first()

        if not plumber_service:
            plumber_service = Service(name="Plumber", base_price=Decimal("150.00"), icon_url="/static/icons/plumber.png")
            db.add(plumber_service)
        if not electrician_service:
            electrician_service = Service(name="Electrician", base_price=Decimal("180.00"), icon_url="/static/icons/electrician.png")
            db.add(electrician_service)
        if not carpenter_service:
            carpenter_service = Service(name="Carpenter", base_price=Decimal("120.00"), icon_url="/static/icons/carpenter.png")
            db.add(carpenter_service)
        if not beautician_service:
            beautician_service = Service(name="Beautician", base_price=Decimal("110.00"), icon_url="/static/icons/beautician.png")
            db.add(beautician_service)
        db.commit()
        
        plumber_service = db.query(Service).filter(Service.name == "Plumber").first()
        electrician_service = db.query(Service).filter(Service.name == "Electrician").first()
        carpenter_service = db.query(Service).filter(Service.name == "Carpenter").first()
        beautician_service = db.query(Service).filter(Service.name == "Beautician").first()

        # 5. Seed Workers (Artisans)
        worker_data = [
            {
                "phone": "+918888888888",
                "name": "Satish Prasad",
                "category": "Plumber",
                "experience": 5,
                "pricing": Decimal("150.00"),
                "rating": Decimal("4.50"),
                "jobs": 3,
                "kyc": KycStatus.approved,
                "roles": [worker_role, plumber_role] if plumber_role else [worker_role],
                "balance": Decimal("1200.00")
            },
            {
                "phone": "+918888888877",
                "name": "Rajesh Carpenter",
                "category": "Carpenter",
                "experience": 8,
                "pricing": Decimal("120.00"),
                "rating": Decimal("4.80"),
                "jobs": 0,
                "kyc": KycStatus.pending,
                "roles": [worker_role, carpenter_role] if carpenter_role else [worker_role],
                "balance": Decimal("0.00")
            },
            {
                "phone": "+918888888866",
                "name": "Karan Electrician",
                "category": "Electrician",
                "experience": 3,
                "pricing": Decimal("180.00"),
                "rating": Decimal("4.20"),
                "jobs": 5,
                "kyc": KycStatus.approved,
                "roles": [worker_role, electrician_role] if electrician_role else [worker_role],
                "balance": Decimal("2400.00")
            },
            {
                "phone": "+918888888855",
                "name": "Sita Beautician",
                "category": "Beautician",
                "experience": 4,
                "pricing": Decimal("220.00"),
                "rating": Decimal("0.00"),
                "jobs": 0,
                "kyc": KycStatus.pending,
                "roles": [worker_role, beautician_role] if beautician_role else [worker_role],
                "balance": Decimal("0.00")
            }
        ]

        workers = []
        for wd in worker_data:
            usr = db.query(User).filter(User.phone_number == wd["phone"]).first()
            is_new = False
            if not usr:
                usr = User(
                    phone_number=wd["phone"],
                    full_name=wd["name"],
                    language_preference="English",
                    is_verified=(wd["kyc"] == KycStatus.approved)
                )
                for r in wd["roles"]:
                    usr.roles.append(r)
                db.add(usr)
                db.commit()
                db.refresh(usr)
                is_new = True
                
                wallet = Wallet(user_id=usr.id, balance=wd["balance"])
                db.add(wallet)
                db.commit()
                
            w_profile = db.query(Worker).filter(Worker.user_id == usr.id).first()
            if not w_profile:
                w_profile = Worker(
                    user_id=usr.id,
                    category=wd["category"],
                    experience_years=wd["experience"],
                    pricing_per_hour=wd["pricing"],
                    rating=wd["rating"],
                    total_jobs_done=wd["jobs"],
                    availability_status="available_now",
                    kyc_status=wd["kyc"],
                    profile_picture="/uploads/kyc/worker_selfie.jpg",
                    aadhaar_number="123456789012" if wd["kyc"] == KycStatus.pending else "123456789999",
                    aadhaar_image_front="/uploads/kyc/aadhaar_front.jpg",
                    aadhaar_image_back="/uploads/kyc/aadhaar_back.jpg"
                )
                db.add(w_profile)
                db.commit()
                print(f"Created worker profile for: {wd['name']}")
            workers.append(w_profile)

        # 6. Seed Contractors
        contractor_data = [
            {
                "phone": "+917777777777",
                "name": "Amit Civil Contractor",
                "company": "Apex Building Works",
                "gst": "07AAAAA1111A1Z1",
                "pan": "ABCDE1234F",
                "kyc": KycStatus.pending,
                "role": civil_contractor_role or contractor_role
            },
            {
                "phone": "+917777777766",
                "name": "Rakesh Plumbing Contractor",
                "company": "Rakesh Pipe & Sanitary",
                "gst": "07BBBBB2222B2Z2",
                "pan": "FGHIJ5678K",
                "kyc": KycStatus.approved,
                "role": plumbing_contractor_role or contractor_role
            }
        ]

        for cd in contractor_data:
            usr = db.query(User).filter(User.phone_number == cd["phone"]).first()
            if not usr:
                usr = User(
                    phone_number=cd["phone"],
                    full_name=cd["name"],
                    language_preference="English",
                    is_verified=(cd["kyc"] == KycStatus.approved)
                )
                usr.roles.append(contractor_role)
                if cd["role"]:
                    usr.roles.append(cd["role"])
                db.add(usr)
                db.commit()
                db.refresh(usr)
                
                wallet = Wallet(user_id=usr.id, balance=Decimal("0.00"))
                db.add(wallet)
                db.commit()

            c_profile = db.query(Contractor).filter(Contractor.user_id == usr.id).first()
            if not c_profile:
                c_profile = Contractor(
                    user_id=usr.id,
                    company_name=cd["company"],
                    gst_number=cd["gst"],
                    pan_number=cd["pan"],
                    kyc_status=cd["kyc"],
                    profile_picture="/uploads/kyc/company_logo.png",
                    business_license="/uploads/kyc/business_license.png"
                )
                db.add(c_profile)
                db.commit()
                print(f"Created contractor profile for: {cd['name']}")

        # 7. Seed Bookings
        db_bookings = db.query(Booking).all()
        if len(db_bookings) <= 1:
            # We seed multiple bookings across past 30 days
            # Fetch active resources
            c1, c2, c3, _ = customers
            w_plumber = workers[0]
            w_carpenter = workers[1]
            w_electrician = workers[2]

            today = date.today()
            
            # Booking list details
            b_list = [
                # Completed plumber bookings
                (c1.id, w_plumber.id, plumber_service.id, today - timedelta(days=25), BookingStatus.completed, Decimal("300.00")),
                (c2.id, w_plumber.id, plumber_service.id, today - timedelta(days=20), BookingStatus.completed, Decimal("150.00")),
                (c3.id, w_plumber.id, plumber_service.id, today - timedelta(days=15), BookingStatus.completed, Decimal("450.00")),
                (c1.id, w_plumber.id, plumber_service.id, today - timedelta(days=12), BookingStatus.completed, Decimal("150.00")),
                (c2.id, w_plumber.id, plumber_service.id, today - timedelta(days=5), BookingStatus.completed, Decimal("300.00")),
                
                # Completed electrician bookings
                (c2.id, w_electrician.id, electrician_service.id, today - timedelta(days=22), BookingStatus.completed, Decimal("540.00")),
                (c3.id, w_electrician.id, electrician_service.id, today - timedelta(days=18), BookingStatus.completed, Decimal("360.00")),
                (c1.id, w_electrician.id, electrician_service.id, today - timedelta(days=8), BookingStatus.completed, Decimal("180.00")),
                (c3.id, w_electrician.id, electrician_service.id, today - timedelta(days=2), BookingStatus.completed, Decimal("720.00")),
                
                # In progress / Active bookings
                (c1.id, w_electrician.id, electrician_service.id, today, BookingStatus.accepted, None),
                (c2.id, w_carpenter.id, carpenter_service.id, today + timedelta(days=1), BookingStatus.pending, None),
                
                # Cancelled / Rejected bookings
                (c3.id, w_plumber.id, plumber_service.id, today - timedelta(days=10), BookingStatus.cancelled, None),
                (c2.id, w_carpenter.id, carpenter_service.id, today - timedelta(days=4), BookingStatus.rejected, None)
            ]

            for cust_id, work_id, serv_id, b_date, status, amount in b_list:
                booking = Booking(
                    customer_id=cust_id,
                    worker_id=work_id,
                    service_id=serv_id,
                    booking_date=b_date,
                    preferred_time="10:00 AM",
                    status=status,
                    address="Connaught Place, New Delhi" if cust_id == c1.id else "Dwarka Sector 10, New Delhi" if cust_id == c2.id else "Saket, New Delhi",
                    total_amount=amount,
                    otp_verification="123456"
                )
                db.add(booking)
            db.commit()
            print("Successfully seeded marketplace bookings.")

        db.commit()
        print("Database Seeding Completed Successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
