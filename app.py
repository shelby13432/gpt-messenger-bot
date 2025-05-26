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

# لتتبع حالة المحادثة لكل مستخدم
user_states = {}
# ممكن يكون شكل الحالة مثلا:
# user_states[user_id] = {
#     "step": "waiting_for_device" / "waiting_for_contact" / None,
#     "device_name": None,
#     "contact_info": None,
# }

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

                    user_message_lower = user_message.lower()

                    # الحالة الحالية للمستخدم
                    state = user_states.get(sender_id, {"step": None, "device_name": None, "contact_info": None})

                    # 1. إذا المستخدم في خطوة انتظار اسم الجهاز (بعد طلب الحجز)
                    if state["step"] == "waiting_for_device":
                        device_name = None
                        for dname in DEVICES:
                            if dname.lower() in user_message_lower:
                                device_name = dname
                                break
                        if device_name:
                            # وجد الجهاز
                            user_states[sender_id] = {"step": "waiting_for_contact", "device_name": device_name, "contact_info": None}
                            send_message(sender_id, f"الجهاز {device_name} متوفر للحجز.\nرجاءً أرسل رقم هاتفك وعنوانك لإتمام الحجز.")
                        else:
                            send_message(sender_id, "عذرًا، هذا الجهاز غير متوفر في مكتب الأصيل. الرجاء إرسال اسم جهاز آخر أو اكتب 'خروج' للخروج من الحجز.")
                        return "ok", 200

                    # 2. إذا المستخدم في خطوة انتظار بيانات الاتصال (رقم هاتف وعنوان)
                    elif state["step"] == "waiting_for_contact":
                        # نفترض أي رسالة ليست أمر خروج تعتبر بيانات الاتصال
                        if user_message_lower == "خروج":
                            user_states[sender_id] = {"step": None, "device_name": None, "contact_info": None}
                            send_message(sender_id, "تم إلغاء الحجز. إذا احتجت أي مساعدة أخرى، أنا هنا.")
                        else:
                            # خزّن البيانات وأكد الحجز
                            user_states[sender_id] = {"step": None, "device_name": state["device_name"], "contact_info": user_message}
                            send_message(sender_id, f"تم تسجيل حجز جهاز {state['device_name']} بنجاح.\nسنتواصل معك قريبًا عبر الرقم والعنوان: {user_message}\nشكرًا لتواصلك مع مكتب الأصيل.")
                        return "ok", 200

                    # 3. إذا المستخدم طلب الحجز (يحتوي على كلمة حجز)
                    elif "حجز" in user_message_lower or "أريد أحجز" in user_message_lower or "أريد احجز" in user_message_lower or "أريد أشتري" in user_message_lower:
                        user_states[sender_id] = {"step": "waiting_for_device", "device_name": None, "contact_info": None}
                        send_message(sender_id, "مرحبًا! لتتمكن من الحجز، من فضلك اذكر اسم الجهاز الذي تريد حجزه.")
                        return "ok", 200

                    # 4. أي رسالة أخرى: رد باستخدام OpenAI مع معرفة بيانات الجهاز إذا ذُكر اسم جهاز
                    matched_device = None
                    for device_name in DEVICES:
                        if device_name.lower() in user_message_lower:
                            matched_device = device_name
                            break

                    if matched_device:
                        device_info = format_device_info(matched_device, DEVICES[matched_device])
                        system_prompt = (
                            f"أنت موظف مبيعات في مكتب الأصيل ترد على الزبائن بأسلوب مهذب واحترافي.\n"
                            f"هذه معلومات عن الجهاز:\n{device_info}\n"
                            f"أجب على السؤال التالي بناءً على هذه المعلومات."
                        )
                    else:
                        system_prompt = "أنت موظف مبيعات في مكتب الأصيل ترد على الزبائن بأسلوب مهذب واحترافي."

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
