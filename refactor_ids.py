import os
import re

backend_dir = r"d:\Coding\mazdoor\backend\app"
models_dir = os.path.join(backend_dir, "models")
schemas_dir = os.path.join(backend_dir, "schemas")
crud_dir = os.path.join(backend_dir, "crud")
endpoints_dir = os.path.join(backend_dir, "api", "v1", "endpoints")

def process_file(filepath, callback):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = callback(content)
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

def update_model(content):
    # Remove autoincrement ID definition
    content = re.sub(r'^\s+id:\s*Mapped\[int\]\s*=\s*mapped_column\(Integer,\s*primary_key=True,\s*autoincrement=True\)\n', '', content, flags=re.MULTILINE)
    
    # Replace Integer FKs with Uuid
    content = content.replace('mapped_column(Integer, ForeignKey', 'mapped_column(Uuid, ForeignKey')
    content = content.replace('Mapped[int]', 'Mapped[uuid.UUID]')
    
    # Add imports
    if 'Mapped[uuid.UUID]' in content or 'Uuid' in content:
        if 'import uuid' not in content:
            content = 'import uuid\n' + content
        if 'Uuid' not in content:
            content = content.replace('from sqlalchemy import ', 'from sqlalchemy import Uuid, ')
            
    # Add slugs to User, Role, Service
    if 'class User(Base):' in content and 'slug:' not in content:
        content = content.replace('full_name: Mapped[str]', 'slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=True)\n    full_name: Mapped[str]')
    if 'class Role(Base):' in content and 'slug:' not in content:
        content = content.replace('name: Mapped[str]', 'slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)\n    name: Mapped[str]')
    if 'class Service(Base):' in content and 'slug:' not in content:
        content = content.replace('name: Mapped[str]', 'slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)\n    name: Mapped[str]')

    return content

for file in os.listdir(models_dir):
    if file.endswith('.py') and file != 'base_class.py':
        process_file(os.path.join(models_dir, file), update_model)

def update_schema(content):
    content = content.replace('id: int', 'id: UUID4')
    content = content.replace('user_id: int', 'user_id: UUID4')
    content = content.replace('worker_id: int', 'worker_id: UUID4')
    content = content.replace('customer_id: int', 'customer_id: UUID4')
    content = content.replace('service_id: int', 'service_id: UUID4')
    content = content.replace('parent_id: int', 'parent_id: UUID4')
    content = content.replace('role_id: int', 'role_id: UUID4')
    
    if 'UUID4' in content and 'from pydantic import' not in content or ('UUID4' in content and 'UUID4' not in content[:content.find('UUID4')]):
        # Add import
        if 'from pydantic import ' in content:
            content = content.replace('from pydantic import ', 'from pydantic import UUID4, ')
        else:
            content = 'from pydantic import UUID4\n' + content
            
    return content

for file in os.listdir(schemas_dir):
    if file.endswith('.py'):
        process_file(os.path.join(schemas_dir, file), update_schema)

print("Models and Schemas updated")
