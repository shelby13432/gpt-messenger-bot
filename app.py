from flask import Flask, request
import requests, os
import cohere
from collections import defaultdict

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

co = cohere.Client(COHERE_API_KEY)

user_sessions = defaultdict(list)

def send_message(recipient_id, message_text):
    requests.post(
        "https://graph.facebook.com/v13.0/me/messages",
        params={"access_token": PAGE_ACCESS_TOKEN},
        headers={"Content-Type": "application/json"},
        json={
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
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

                    # أضف رسالة المستخدم إلى الجلسة
                    user_sessions[sender_id].append({"role": "USER", "message": user_message})

                    # برومبت يحدد دور النموذج
                    system_prompt = {
                        "role": "SYSTEM",
                        "message": "أنت موظف لدى مكتب الأصيل. وظيفتك هي الرد على استفسارات الزبائن بكل ود واحترام، وتقديم المساعدة بأفضل شكل ممكن."
                    }

                    # دمج البرومبت مع محادثات المستخدم
                    chat_history = [system_prompt] + user_sessions[sender_id]

                    try:
                        response = co.chat(
                            chat_history=chat_history,
                            model="command-r",
                            temperature=0.7,
                            max_tokens=500
                        )
                        reply = response.text
                    except Exception as e:
                        reply = "عذرًا، حدث خطأ أثناء المعالجة."

                    # إرسال الرد للمستخدم
                    send_message(sender_id, reply)

                    # تقليل عدد الرسائل المخزنة لكل مستخدم
                    if len(user_sessions[sender_id]) > 10:
                        user_sessions[sender_id] = user_sessions[sender_id][-10:]

    return "ok", 200

if __name__ == "__main__":
    app.run(debug=True)
