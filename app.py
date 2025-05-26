from flask import Flask, request
import requests
import os
import openai

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

def send_message(recipient_id, message_text):
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    try:
        response = requests.post(
            "https://graph.facebook.com/v13.0/me/messages",
            params=params,
            headers=headers,
            json=data
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")

@app.route('/webhook', methods=['GET'])
def verify():
    token_sent = request.args.get("hub.verify_token")
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if data and data.get('object') == 'page':
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                if messaging_event.get('message'):
                    sender_id = messaging_event['sender']['id']
                    user_message = messaging_event['message'].get('text')

                    if not user_message:
                        # إذا الرسالة ليست نصية، نتجاهلها
                        return "ok", 200

                    system_prompt = "أنت مساعد ذكي يتحدث العربية ويجيب باحترافية."

                    try:
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_message}
                            ]
                        )
                        reply = response.choices[0].message['content']
                    except Exception as e:
                        print(f"Error from OpenAI API: {e}")
                        reply = "عذراً، حدث خطأ في معالجة طلبك."

                    send_message(sender_id, reply)
    return "ok", 200

if __name__ == "__main__":
    app.run(debug=True)
