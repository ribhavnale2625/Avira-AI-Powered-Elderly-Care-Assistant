import requests
import json
import time

url = "http://127.0.0.1:5000/api/process"

# Wait/retry for server to start
print("Waiting for server to start...")
for i in range(15):
    try:
        r = requests.get("http://127.0.0.1:5000/health", timeout=2)
        if r.status_code == 200:
            print("Server is up and running!")
            break
    except Exception:
        pass
    print(f"Server not ready, retrying ({i+1}/15)...")
    time.sleep(2)

test_payloads = [
    {"text": "turn on all the lights", "language": "en"},
    {"text": "switch off the bedroom fan", "language": "en"},
    {"text": "lock the door", "language": "en"},
    {"text": "is the bedroom light on?", "language": "en"},
    {"text": "I feel so lonely and sad today", "language": "en"},
    {"text": "can you make me dinner and coffee?", "language": "en"},
]

for p in test_payloads:
    print(f"Sending payload: {p}")
    try:
        r = requests.post(url, json=p)
        print(f"Status Code: {r.status_code}")
        print(f"Response JSON: {json.dumps(r.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 50)
