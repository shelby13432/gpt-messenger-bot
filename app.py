from flask import Flask, request
import requests
import os
import cohere

app = Flask(__name__)

# تحميل المتغيرات من البيئة
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# إنشاء عميل cohere
co = cohere.Client(COHERE_API_KEY)

def send_message(recipient_id, text):
    """إرسال رسالة نصية إلى مستخدم في فيسبوك"""
    url = f"https://graph.facebook.com/v12.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")

@app.route("/", methods=["GET"])
def verify():
    """تأكيد التحقق من Webhook مع فيسبوك"""
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Invalid verification token", 403

@app.route("/", methods=["POST"])
def webhook():
    """التعامل مع الرسائل الواردة"""
    data = request.get_json()
    if not data:
        return "No data received", 400

    for entry in data.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            if messaging_event.get("message") and "text" in messaging_event["message"]:
                sender_id = messaging_event["sender"]["id"]
                message_text = messaging_event["message"]["text"]

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

if __name__ == "__main__":
    app.run(debug=True)

