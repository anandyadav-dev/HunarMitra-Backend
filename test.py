import urllib.request
import json
import urllib.error

req = urllib.request.Request(
    'http://localhost:8000/api/v1/auth/admin-login',
    data=json.dumps({'phone_number': '+919999999900', 'password': 'admin123'}).encode(),
    headers={'Content-Type': 'application/json'}
)
try:
    response = urllib.request.urlopen(req)
    print(response.status, response.read().decode())
except urllib.error.HTTPError as e:
    print(e.code, e.read().decode())
