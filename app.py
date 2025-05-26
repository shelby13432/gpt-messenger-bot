from flask import Flask, request
import requests, os
from openai import OpenAI
from collections import defaultdict

app = Flask(__name__)
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

user_sessions = defaultdict(list)

def send_message(recipient_id, message_text):
    requests.post(
        "https://graph.facebook.com/v13.0/me/messages",
        params={"access_token": PAGE_ACCESS_TOKEN},
        headers={"Content-Type": "application/json"},
        json={"recipient": {"id": recipient_id}, "message": {"text": message_text}}
    )

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if data.get('object') == 'page':
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                if messaging_event.get('message'):
                    sender_id = messaging_event['sender']['id']
                    user_message = messaging_event['message'].get('text')
                    if not user_message:
                        return "ok", 200

                    system_prompt = """ 
                    ... (نفس النص اللي كتبته أنت هنا) ...
                    """

                    user_sessions[sender_id].append({"role": "user", "content": user_message})
                    messages = [{"role": "system", "content": system_prompt}] + user_sessions[sender_id]

                    try:
                        response = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=messages,
                            max_tokens=500,
                            temperature=0.7,
                            stream=False
                        )
                        reply = response.choices[0].message.content
                    except Exception:
                        reply = "عذرًا، حدث خطأ أثناء المعالجة."

                    send_message(sender_id, reply)

                    if len(user_sessions[sender_id]) > 10:
                        user_sessions[sender_id] = user_sessions[sender_id][-10:]
    return "ok", 200

if __name__ == "__main__":
    app.run(debug=True)
