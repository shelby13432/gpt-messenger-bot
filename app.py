from flask import Flask, request
import requests
import os
import openai

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# قاعدة بيانات الأجهزة - يمكن توسعتها حسب الحاجة
DEVICES = {
    "S22 Ultra 128GB": {
        "السعر": "515 ألف",
        "المعالج": "Snapdragon 8 Gen 1",
        "الكاميرا": "108MP رباعية",
        "البطارية": "5000mAh"
    },
    "S22 Ultra 512GB": {
        "السعر": "575 ألف",
        "المعالج": "Snapdragon 8 Gen 1",
        "الكاميرا": "108MP رباعية",
        "البطارية": "5000mAh"
    },
    "S23 Ultra 256GB": {
        "السعر": "725 ألف",
        "المعالج": "Snapdragon 8 Gen 2",
        "الكاميرا": "200MP رباعية",
        "البطارية": "5000mAh"
    },
    "iPhone 14 128GB": {
        "السعر": "550 ألف",
        "المعالج": "A15 Bionic",
        "الكاميرا": "12MP مزدوجة",
        "البطارية": "3279mAh"
    },
    # أضف باقي الأجهزة بنفس النمط...
}

def format_device_info(device_name, info):
    return (f"الجهاز: {device_name}\n"
            f"السعر: {info['السعر']}\n"
            f"المعالج: {info['المعالج']}\n"
            f"الكاميرا: {info['الكاميرا']}\n"
            f"البطارية: {info['البطارية']}")

def send_message(recipient_id, message_text):
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    requests.post("https://graph.facebook.com/v13.0/me/messages", params=params, headers=headers, json=data)

@app.route('/webhook', methods=['GET'])
def verify():
    token_sent = request.args.get("hub.verify_token")
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if data['object'] == 'page':
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                if messaging_event.get('message'):
                    sender_id = messaging_event['sender']['id']
                    user_message = messaging_event['message'].get('text')
                    if not user_message:
                        return "ok", 200

                    matched_device = None
                    for device_name in DEVICES:
                        if device_name.lower() in user_message.lower():
                            matched_device = device_name
                            break

                    if matched_device:
                        device_info = format_device_info(matched_device, DEVICES[matched_device])
                        system_prompt = (
                            f"أنت مساعد ذكي يتحدث العربية ويجيب باحترافية.\n"
                            f"هذه معلومات عن الجهاز الذي سأذكره:\n{device_info}\n"
                            f"أجب على السؤال التالي بناءً على هذه المعلومات."
                        )
                    else:
                        system_prompt = "أنت مساعد ذكي يتحدث العربية ويجيب باحترافية."

                    response = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ]
                    )
                    reply = response.choices[0].message.content
                    send_message(sender_id, reply)
    return "ok", 200

if __name__ == "__main__":
    app.run(debug=True)
