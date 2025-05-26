from flask import Flask, request
import requests
import os
import cohere

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

co = cohere.Client(COHERE_API_KEY)

def send_message(recipient_id, text):
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    headers = {
        "Content-Type": "application/json"
    }
    url = f"https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    requests.post(url, json=data, headers=headers)

@app.route("/", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == VERIFY_TOKEN:
        return challenge
    return "Invalid verification token"

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    for entry in data.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            if messaging_event.get("message"):
                sender_id = messaging_event["sender"]["id"]
                message_text = messaging_event["message"].get("text")
                if message_text:
                    prompt = f"""
                    أنت بوت مساعد للرد على استفسارات الزبائن في صفحة فيسبوك. كن ودودًا ومفيدًا.

                    سؤال: {message_text}
                    جواب:
                    """

                    try:
                        response = co.generate(
                            model="command-r-plus",
                            prompt=prompt,
                            max_tokens=100,
                            temperature=0.5,
                            stop_sequences=["\n"]
                        )
                        reply = response.generations[0].text.strip()
                        if not reply:
                            reply = "عذرًا، لم أفهم سؤالك، هل يمكنك إعادة الصياغة؟"
                    except Exception as e:
                        print(f"Error calling Cohere API: {e}")
                        reply = "عذرًا، حدث خطأ داخلي. الرجاء المحاولة لاحقًا."

                    send_message(sender_id, reply)
    return "ok", 200
