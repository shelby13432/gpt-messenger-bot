from flask import Flask, request
import requests
import cohere
from collections import defaultdict
import json

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

co = cohere.Client(COHERE_API_KEY)

user_sessions = defaultdict(list)

def send_message(recipient_id, message):
    try:
        response = requests.post(
            "https://graph.facebook.com/v13.0/me/messages",
            params={"access_token": PAGE_ACCESS_TOKEN},
            json={
                "recipient": {"id": recipient_id},
                "message": json.dumps(message)
            }
        )

        return response.json().get('status') == 'DELIVERED'

    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {e}")
        return False

def prepare_message(role, message):
    return {"role": role, "message": message}

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token', 403

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
                        send_message(sender_id, {"text": "Please ask something!"})
                        continue

                    user_sessions[sender_id].append(prepare_message("USER", user_message))

                    prompt = {
                        "role": "SYSTEM",
                        "message": "Welcome! I'm here to assist you. What's yourquery?"
                    }

                    chat_history = [prompt] + user_sessions[sender_id]

                    try:
                        response = co.chat(
                            chat_history=chat_history,
                            model="command-r",
                            temperature=0.7,
                            max_tokens=500
                        )
                        reply = response.text

                    except cohere.exceptions.APIError as e:
                        reply = f"Error communicating with API: {e}"

                    except Exception as e:
                        reply = "An unexpected error occurred."

                    message = {"text": reply}

                    if not send_message(sender_id, message):
                        return "Failed to send response", 500

                    if len(user_sessions[sender_id]) > 10:
                        user_sessions[sender_id] = user_sessions[sender_id][-10:]

    return "ok", 200

if __name__ == "__main__":
    app.run(debug=True)
