import requests
import json

BASE = "http://localhost:8000/api"

# Test predict
payload = {
    "Train_id": "R1",
    "Train_name": "Rajdhani Express",
    "Train_no": "12301",
    "Source": "Howrah",
    "Destitnation": "New Delhi",
    "Distance_Km": 1450.0,
    "Sc_arr__time": "10:00:00",
    "Season": "Winter",
    "Run_frequency": "Daliy",
    "Date": "2026-01-15"
}
r = requests.post(f"{BASE}/predict", json=payload)
pred = r.json()
print("Predict result:", json.dumps(pred, indent=2))

# Test chat
chat_payload = {"message": "What are the cancellation rules for trains?"}
r = requests.post(f"{BASE}/chat", json=chat_payload)
chat = r.json()
print("\nChat success:", chat.get("success"))
if chat.get("message"):
    print("Chat response (first 300 chars):", chat["message"][:300])
else:
    print("Chat error:", chat.get("error"))
