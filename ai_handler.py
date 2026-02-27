import requests

class AIHandler:
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def process_text(self, text, model_id):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000", # Required for OpenRouter 2026
            "X-Title": "Stealth Reader Pro"
        }
        
        data = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant. Summarize or explain the OCR text provided. Be concise."},
                {"role": "user", "content": text}
            ]
        }
        
        try:
            response = requests.post(self.url, headers=headers, json=data, timeout=20)
            if response.status_code == 200:
                result = response.json()
                # Extract clean content (ignores reasoning/thought blocks)
                return result['choices'][0]['message'].get('content', '').strip()
            else:
                return f"❌ AI Error {response.status_code}: {response.text}"
        except Exception as e:
            return f"❌ Connection Error: {str(e)}"