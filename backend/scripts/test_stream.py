import requests
import json
import sys

url = "http://localhost:8000/research/stream"
payload = {"query": "Test Query", "max_papers": 1}

print(f"Testing stream: {url} with {payload}...")

try:
    with requests.post(url, json=payload, stream=True) as r:
        if r.status_code != 200:
            print(f"Error: {r.status_code} - {r.text}")
            sys.exit(1)
            
        print("Connected! Waiting for events...")
        for line in r.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                print(decoded_line)
                
                # Check for specific event types
                if "data:" in decoded_line:
                    try:
                        data = json.loads(decoded_line.replace("data: ", ""))
                        status = data.get("status")
                        print(f"-> Status: {status}")
                        if status == "complete":
                            print("\nSUCCESS: Stream completed successfully!")
                            sys.exit(0)
                        if status == "error":
                            print(f"\nFAILURE: Stream returned error: {data.get('message')}")
                            sys.exit(1)
                    except:
                        pass
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)
