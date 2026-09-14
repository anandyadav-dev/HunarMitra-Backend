import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.models.base_class import Base
from app.models.user import User
from app.models.worker import Worker
from app.models.contractor import Contractor
from app.models.role import Role
from app.models.booking import Booking
from app.models.wallet import Wallet
from app.models.work_proof import WorkProof
from app.models.service import Service

def recreate_database():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Done!")

if __name__ == "__main__":
    recreate_database()
