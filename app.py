from flask import Flask, request
import requests, os, openai
from collections import defaultdict

app = Flask(__name__)
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

openai.api_key = DEEPSEEK_API_KEY
openai.base_url = "https://api.deepseek.com/v1"

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
                    أنت موظف مبيعات في مكتب الأصيل ترد على الزبائن بأسلوب مهذب واحترافي.
                    الاجهزة المتوفرة مع اسعارهم ومواصفاتهم هم 📱 سامسونج:

                    - S22 Ultra 128GB - 515 ألف  
                      معالج: Snapdragon 8 Gen 1  
                      كاميرا: 108MP رباعية  
                      بطارية: 5000mAh  

                    - S22 Ultra 512GB - 575 ألف  
                      نفس المواصفات مع زيادة التخزين  

                    - S23 Ultra 256GB - 725 ألف  
                      معالج: Snapdragon 8 Gen 2  
                      كاميرا: 200MP رباعية  
                      بطارية: 5000mAh  

                    - S23 Ultra 512GB - 765 ألف  
                      نفس المواصفات مع زيادة التخزين  

                    - Note 20 Ultra 128GB - 415 ألف  
                      معالج: Exynos 990  
                      كاميرا: 108MP ثلاثية  
                      بطارية: 4500mAh  

                    - S23 Plus 256GB - 525 ألف  
                      معالج: Snapdragon 8 Gen 2  
                      كاميرا: 50MP ثنائية  
                      بطارية: 4700mAh  

                    - S23 Plus 512GB - 570 ألف  
                      نفس المواصفات مع زيادة التخزين  

                    - A54 128GB - 260 ألف  
                      معالج: Exynos 1380  
                      كاميرا: 50MP ثلاثية  
                      بطارية: 5000mAh  

                    - A71 128GB - 190 ألف  
                      معالج: Snapdragon 730  
                      كاميرا: 64MP رباعية  
                      بطارية: 4500mAh  

                    - Flip 5 512GB - 575 ألف  
                      معالج: Snapdragon 8 Gen 2  
                      كاميرا: 12MP مزدوجة  
                      بطارية: 3700mAh  

                    - Flip 4 128GB - 390 ألف  
                      معالج: Snapdragon 8+ Gen 1  
                      كاميرا: 12MP مزدوجة  
                      بطارية: 3700mAh  


                    سوني:

                    - Xperia 1 Mark 4 256GB - 375 ألف  
                      معالج: Snapdragon 8 Gen 1  
                      كاميرا: 12MP ثلاثية  
                      بطارية: 5000mAh  

                    - Xperia 5 Mark 4 128GB - 250 ألف  
                      معالج: Snapdragon 8 Gen 1  
                      كاميرا: 12MP ثلاثية  
                      بطارية: 5000mAh  

                    - Xperia 5 Mark 3 128GB - 215 ألف  
                      معالج: Snapdragon 888  
                      كاميرا: 12MP ثلاثية  
                      بطارية: 4500mAh  

                    - Xperia 1 Mark 4 (شاشة طابعة) 256GB - 290 ألف  
                      نفس المواصفات مع تركيز على الشاشة  


                    لايكا:

                    - Leica Phone 2 512GB - 350 ألف  
                      معالج: Snapdragon 888  
                      كاميرا: Leica 20MP مزدوجة  
                      بطارية: 4500mAh  

                    - Leica Phone 1 256GB - 195 ألف  
                      معالج: Snapdragon 765G  
                      كاميرا: Leica 20MP مزدوجة  
                      بطارية: 4300mAh  


                    آيباد Apple:

                    - iPad Air 4 64GB - 400 ألف  
                      معالج: A14 Bionic  
                      كاميرا: 12MP خلفية  
                      بطارية: حتى 10 ساعات استخدام  

                    - iPad Mini 6 64GB - 460 ألف  
                      معالج: A15 Bionic  
                      كاميرا: 12MP خلفية  
                      بطارية: حتى 10 ساعات استخدام  

                    - iPad Pro 2016 (9.7 إنش) 128GB - 125 ألف  
                      معالج: A9X  
                      كاميرا: 12MP خلفية  
                      بطارية: حتى 10 ساعات استخدام  

                    - iPad Air 3 64GB - 225 ألف  
                      معالج: A12 Bionic  
                      كاميرا: 8MP خلفية  
                      بطارية: حتى 10 ساعات استخدام  


                    Google Pixel:

                    - Pixel 8 Pro 128GB - 600 ألف  
                      معالج: Google Tensor G3  
                      كاميرا: 50MP ثلاثية  
                      بطارية: 5000mAh  

                    - Pixel 8 Pro 256GB - 650 ألف  
                      نفس المواصفات مع زيادة التخزين  

                    - Pixel 8 Pro 512GB - 690 ألف  
                      نفس المواصفات مع زيادة التخزين  

                    - Pixel 7 Pro 256GB - 450 ألف  
                      معالج: Google Tensor G2  
                      كاميرا: 50MP ثلاثية  
                      بطارية: 5000mAh  

                    - Pixel 7 Pro 128GB - 400 ألف  
                      نفس المواصفات مع تخزين أقل  

                    - Pixel 6 Pro 256GB - 315 ألف  
                      معالج: Google Tensor  
                      كاميرا: 50MP ثلاثية  
                      بطارية: 5000mAh  

                    - Pixel Fold 1 256GB - 625 ألف  
                      معالج: Google Tensor G2  
                      كاميرا: 48MP مزدوجة  
                      بطارية: 4400mAh  


                    ون بلس:

                    - OnePlus 9 128GB - 225 ألف  
                      معالج: Snapdragon 888  
                      كاميرا: 48MP مزدوجة  
                      بطارية: 4500mAh  

                    - OnePlus 10 Pro 128GB - 400 ألف  
                      معالج: Snapdragon 8 Gen 1  
                      كاميرا: 48MP رباعية  
                      بطارية: 5000mAh  

                    - OnePlus Nord 1 128GB - 190 ألف  
                      معالج: Snapdragon 765G  
                      كاميرا: 48MP مزدوجة  
                      بطارية: 4115mAh  


                    آيفونات:

                    - iPhone XS Max 256GB - 300 ألف  
                      معالج: A12 Bionic  
                      كاميرا: 12MP مزدوجة  
                      بطارية: 3174mAh  

                    - iPhone 14 128GB - 550 ألف  
                      معالج: A15 Bionic  
                      كاميرا: 12MP مزدوجة  
                      بطارية: 3279mAh  

                    - iPhone 13 128GB - 450 ألف  
                      معالج: A15 Bionic  
                      كاميرا: 12MP مزدوجة  
                      بطارية: 3240mAh  

                    رجاءً أجب على سؤال العميل بناءً على هذه المعلومات بأسلوب مهذب واحترافي.

 """

                    user_sessions[sender_id].append({"role": "user", "content": user_message})
                    messages = [{"role": "system", "content": system_prompt}] + user_sessions[sender_id]

                    try:
                        response = openai.chat.completions.create(
                            model="deepseek-chat",
                            messages=messages,
                            max_tokens=500,
                            temperature=0.7
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
