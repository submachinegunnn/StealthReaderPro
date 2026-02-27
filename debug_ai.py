import requests
import json

# Replace with your FRESHLY generated key
API_KEY = "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" 
MODEL = "openrouter/free" # Example model, change as needed

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:3000",
    "X-Title": "DebugScript"
}

data = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "Test connection. Reply with 'OK'."}]
}

response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, data=json.dumps(data))

print(f"Status Code: {response.status_code}")
print(f"Full Response: {response.text}")