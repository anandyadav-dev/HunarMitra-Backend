import os
import re

backend_dir = r"d:\Coding\mazdoor\backend\app"
crud_dir = os.path.join(backend_dir, "crud")
endpoints_dir = os.path.join(backend_dir, "api", "v1", "endpoints")

def process_file(filepath, callback):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = callback(content)
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

def update_crud(content):
    content = content.replace('id: Any', 'id: UUID')
    content = content.replace('id: int', 'id: UUID')
    content = content.replace('user_id: int', 'user_id: UUID')
    content = content.replace('worker_id: int', 'worker_id: UUID')
    content = content.replace('customer_id: int', 'customer_id: UUID')
    content = content.replace('service_id: int', 'service_id: UUID')
    content = content.replace('parent_id: int', 'parent_id: UUID')
    content = content.replace('role_id: int', 'role_id: UUID')
    
    if 'UUID' in content and 'from uuid import UUID' not in content:
        content = 'from uuid import UUID\n' + content
        
    return content

for file in os.listdir(crud_dir):
    if file.endswith('.py'):
        process_file(os.path.join(crud_dir, file), update_crud)

def update_endpoints(content):
    content = content.replace('id: int', 'id: UUID')
    content = content.replace('user_id: int', 'user_id: UUID')
    content = content.replace('worker_id: int', 'worker_id: UUID')
    content = content.replace('customer_id: int', 'customer_id: UUID')
    content = content.replace('service_id: int', 'service_id: UUID')
    content = content.replace('parent_id: int', 'parent_id: UUID')
    content = content.replace('role_id: int', 'role_id: UUID')
    
    if 'UUID' in content and 'from uuid import UUID' not in content:
        content = 'from uuid import UUID\n' + content
        
    return content

for file in os.listdir(endpoints_dir):
    if file.endswith('.py'):
        process_file(os.path.join(endpoints_dir, file), update_endpoints)

print("CRUD and Endpoints updated")
