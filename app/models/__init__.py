from app.models.base_class import Base
from app.models.role import Role
from app.models.user_role import user_roles
from app.models.user import User
from app.models.worker import Worker
from app.models.contractor import Contractor
from app.models.service import Service
from app.models.booking import Booking, BookingStatus
from app.models.wallet import Wallet
from app.models.work_proof import WorkProof
from app.models.notification import Notification

from app.models.legal_document import LegalDocument

__all__ = [
    "Base",
    "Role",
    "user_roles",
    "User",
    "Worker",
    "Contractor",
    "Service",
    "Booking",
    "BookingStatus",
    "Wallet",
    "WorkProof",
    "Notification",
    "LegalDocument",
]

import app.models.events
