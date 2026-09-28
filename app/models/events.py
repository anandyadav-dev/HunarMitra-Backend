from sqlalchemy import event
from slugify import slugify
from app.models.user import User
from app.models.role import Role
from app.models.service import Service
import uuid

def generate_slug(target, value, oldvalue, initiator):
    if value:
        base_slug = slugify(value)
        if not base_slug:
            base_slug = "unknown"
            
        if isinstance(target, User):
            target.slug = f"{base_slug}-{str(uuid.uuid4())[:6]}"
        else:
            target.slug = base_slug

event.listen(User.full_name, 'set', generate_slug)
event.listen(Role.name, 'set', generate_slug)
event.listen(Service.name, 'set', generate_slug)
