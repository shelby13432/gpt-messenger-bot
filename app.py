from flask import Flask, request
import requests
import os
from cohere import ClientV2

app = Flask(__name__)

# تحميل المتغيرات من البيئة
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# إنشاء عميل cohere V2
client = ClientV2(api_key=COHERE_API_KEY)

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

@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Invalid verification token", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data:
        return "No data received", 400

    for entry in data.get("entry", []):
        for messaging_event in entry.get("messaging", []):
            if messaging_event.get("message") and "text" in messaging_event["message"]:
                sender_id = messaging_event["sender"]["id"]
                message_text = messaging_event["message"]["text"]

                messages = [
                    {
                        "role": "system",
                        "content": "أنت مساعد ذكي يعمل لدى مكتب الأصيل للإلكترونيات، وظيفتك الرد على استفسارات الزبائن حول الأجهزة المتوفرة، مواصفاتها وأسعارها بالدينار العراقي."
                    },
                    {
                        "role": "user",
                        "content": message_text
                    },
                    {
                        "role": "assistant",
                        "content": """
مرحباً! إليك قائمة الأجهزة المتوفرة حالياً مع الأسعار والمواصفات 📱:

🔹 **سامسونج:**
- S22 Ultra 128GB - 515 ألف
  - Snapdragon 8 Gen 1 | 108MP | بطارية 5000mAh
- S22 Ultra 512GB - 575 ألف
  - نفس المواصفات مع زيادة التخزين
- S23 Ultra 256GB - 725 ألف
  - Snapdragon 8 Gen 2 | 200MP | بطارية 5000mAh
- S23 Ultra 512GB - 765 ألف
- Note 20 Ultra 128GB - 415 ألف
  - Exynos 990 | 108MP | بطارية 4500mAh
- S23 Plus 256GB - 525 ألف
  - Snapdragon 8 Gen 2 | 50MP | بطارية 4700mAh
- S23 Plus 512GB - 570 ألف
- A54 128GB - 260 ألف
  - Exynos 1380 | 50MP | بطارية 5000mAh
- A71 128GB - 190 ألف
  - Snapdragon 730 | 64MP | بطارية 4500mAh
- Flip 5 512GB - 575 ألف
  - Snapdragon 8 Gen 2 | 12MP | بطارية 3700mAh
- Flip 4 128GB - 390 ألف
  - Snapdragon 8+ Gen 1 | 12MP | بطارية 3700mAh

🔹 **سوني:**
- Xperia 1 Mark 4 256GB - 375 ألف
  - Snapdragon 8 Gen 1 | 12MP | بطارية 5000mAh
- Xperia 5 Mark 4 128GB - 250 ألف
- Xperia 5 Mark 3 128GB - 215 ألف
  - Snapdragon 888 | 12MP | بطارية 4500mAh
- Xperia 1 Mark 4 (شاشة طابعة) 256GB - 290 ألف

🔹 **لايكا:**
- Leica Phone 2 512GB - 350 ألف
  - Snapdragon 888 | Leica 20MP | بطارية 4500mAh
- Leica Phone 1 256GB - 195 ألف
  - Snapdragon 765G | Leica 20MP | بطارية 4300mAh

🔹 **آيباد Apple:**
- iPad Air 4 64GB - 400 ألف
  - A14 Bionic | 12MP | حتى 10 ساعات استخدام
- iPad Mini 6 64GB - 460 ألف
  - A15 Bionic
- iPad Pro 2016 (9.7") 128GB - 125 ألف
  - A9X
- iPad Air 3 64GB - 225 ألف
  - A12 Bionic | 8MP | حتى 10 ساعات

🔹 **Google Pixel:**
- Pixel 8 Pro 128GB - 600 ألف
- Pixel 8 Pro 256GB - 650 ألف
- Pixel 8 Pro 512GB - 690 ألف
  - Google Tensor G3 | 50MP | بطارية 5000mAh
- Pixel 7 Pro 256GB - 450 ألف
- Pixel 7 Pro 128GB - 400 ألف
  - Google Tensor G2
- Pixel 6 Pro 256GB - 315 ألف
  - Google Tensor | 50MP
- Pixel Fold 1 256GB - 625 ألف
  - Google Tensor G2 | 48MP | بطارية 4400mAh

🔹 **ون بلس:**
- OnePlus 9 128GB - 225 ألف
  - Snapdragon 888 | 48MP | بطارية 4500mAh
- OnePlus 10 Pro 128GB - 400 ألف
  - Snapdragon 8 Gen 1 | 48MP رباعية
- OnePlus Nord 1 128GB - 190 ألف
  - Snapdragon 765G | بطارية 4115mAh

🔹 **آيفون:**
- iPhone XS Max 256GB - 300 ألف
  - A12 Bionic | 12MP | بطارية 3174mAh
- iPhone 14 128GB - 550 ألف
  - A15 Bionic | 12MP | بطارية 3279mAh
- iPhone 13 128GB - 450 ألف
  - A15 Bionic | بطارية 3240mAh

📦 إذا كنت تبحث عن جهاز معين أو تريد مقارنة بين جهازين، أخبرني بذلك!
"""
                    }
                ]

                try:
                    response = client.chat(
                        model="command-r",
                        messages=messages,
                        temperature=0.5,
                        max_tokens=300
                    )
                    reply = response.message.content[0].text.strip()

                    if not reply:
                        reply = "عذرًا، لم أفهم سؤالك، هل يمكنك إعادة الصياغة؟"
                except Exception as e:
                    print(f"Error calling Cohere API: {e}")
                    reply = "عذرًا، حدث خطأ داخلي. الرجاء المحاولة لاحقًا."

                send_message(sender_id, reply)

    return "ok", 200

if __name__ == "__main__":
    app.run(debug=True, port=10000)
