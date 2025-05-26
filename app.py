from flask import Flask, request
import requests
import cohere
from collections import defaultdict
import json

app = Flask(__name__)  # إنشئ تطبيق Flask

# احصل على المتغيرات البيئية الضرورية من النظام
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# إنشاء عميل Cohere API
co = cohere.Client(COHERE_API_KEY)

# دالة لتخزين جلسات المحادثة لكل مستخدم
user_sessions = defaultdict(list)

def send_message(recipient_id, message):
    """
    إرسال رسالة إلى مستخدم فيسبوك.
    """
    try:
        # إرسال طلب POST إلى واجهة برمجة تطبيقات فيسبوك مع بيانات الرسالة
        response = requests.post(
            "https://graph.facebook.com/v13.0/me/messages",
            params={"access_token": PAGE_ACCESS_TOKEN},
            json=message
        )

        # التحقق من نجاح الإرسال وعودة الحالة 'DELIVERED'
        return response.json().get('status') == 'DELIVERED'

    except requests.exceptions.RequestException as e:
        # طباعة خطأ في حالة حدوث طلب غير ناجح
        print(f"Failed to send message: {e}")
        return False

def prepare_message(role, message):
    """
    إعداد رسالة بتنسيق JSON المطلوب.
    """
    return {"role": role, "message": message}

@app.route('/webhook', methods=['GET'])
def verify():
    # التحقق من رمز التحقق من فيسبوك
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    
    # إرجاع رمز غير صالح في حالة عدم المطابقة
    return 'Invalid verification token', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    # الحصول على بيانات طلب الويب من فيسبوك
    data = request.get_json()

    # التحقق مما إذا كان الطلب يتعلق بـ 'page'
    if data.get('object') == 'page':
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                # الحصول على رسالة المستخدم
                if messaging_event.get('message'):
                    sender_id = messaging_event['sender']['id']
                    user_message = messaging_event['message'].get('text')

                    if not user_message:
                        # إرسال رسالة إذا لم يرسل المستخدم أي نص
                        send_message(sender_id, {"text": "Please ask something!"})
                        continue

                    # تخزين رسالة المستخدم في سجل المحادثة
                    user_sessions[sender_id].append(prepare_message("USER", user_message))

                    # إعداد رسالة الترحيب
                    prompt = {
                        "role": "SYSTEM",
                        "message": "Welcome! I'm here to assist you. What's your query?"
                    }

                    # إعداد سجل المحادثة
                    chat_history = [prompt] + user_sessions[sender_id]

                    try:
                        # الاتصال بـ Cohere API للحصول على الرد
                        response = co.chat(
                            chat_history=chat_history,
                            model="command-r",
                            temperature=0.7,
                            max_tokens=500
                        )

                        # الحصول على النص من استجابة JSON
                        reply = response.text or "No response."

                    except cohere.exceptions.APIError as e:
                        # معالجة خطأ واجهة برمجة تطبيقات Cohere
                        reply = f"Error from Cohere API: {e}"

                    except Exception as e:
                        # معالجة أي خطأ آخر غير متوقع
                        reply = "An unexpected error occurred. Please try again."

                    # إعداد رسالة الرد وإرسالها
                    message = {"text": reply}
                    if not send_message(sender_id, message):
                        return "Failed to send response", 500

                    # تنظيف سجل المحادثة إذا كان طويلاً جداً
                    if len(user_sessions[sender_id]) > 10:
                        user_sessions[sender_id].pop(0)

    return "ok", 200

if __name__ == "__main__":
    # تشغيل تطبيق Flask في وضع التطوير
    app.run(debug=True)
