import requests
import json
import sys

BASE_URL = "http://localhost:8000"

print("1. Testing Registration")
r = requests.post(f"{BASE_URL}/auth/register", json={
    "email": "test2@pala.com",
    "password": "TestPassword123"
})
if r.status_code != 201:
    print(f"Failed! {r.status_code} {r.text}")
    sys.exit(1)
data = r.json()
access_token = data['data']['tokens']['access_token']
print(f"Success! Access Token: {access_token[:20]}...")

print("\n2. Testing /auth/me")
headers = {"Authorization": f"Bearer {access_token}"}
r = requests.get(f"{BASE_URL}/auth/me", headers=headers)
print(f"{r.status_code} {r.json()}")

print("\n3. Testing POST /expenses")
r = requests.post(f"{BASE_URL}/expenses", headers=headers, json={
    "amount": 250.50,
    "currency": "INR",
    "category": "Food & Dining",
    "description": "Lunch",
    "expense_at": "2026-04-26T12:00:00Z"
})
print(f"{r.status_code} {r.json()}")

print("\n4. Testing GET /insights (Daily)")
r = requests.get(f"{BASE_URL}/insights/today", headers=headers)
print(f"{r.status_code} {r.json()}")

print("\n5. Testing POST /query")
r = requests.post(f"{BASE_URL}/query", headers=headers, json={
    "question": "How much did I spend today?"
})
print(f"{r.status_code} {r.json()}")
