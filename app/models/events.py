from sqlalchemy import event
from slugify import slugify
from app.models.user import User
from app.models.role import Role
from app.models.service import Service
import uuid

def generate_slug(target, value, oldvalue, initiator):
    if value:
        # Generate slug and append a short uuid to ensure uniqueness if needed
        # Or just simple slugify
        target.slug = slugify(value)
        if not target.slug:
            target.slug = str(uuid.uuid4())[:8]

event.listen(User.full_name, 'set', generate_slug)
event.listen(Role.name, 'set', generate_slug)
event.listen(Service.name, 'set', generate_slug)
