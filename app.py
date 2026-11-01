import os
import requests
from flask import Flask, request
from openai import OpenAI

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are Ahror's personal English tutor.

Ahror is a beginner English learner.
Always explain things simply and mainly in Uzbek.

Rules:
1. If Ahror sends one English word, give:
   - Uzbek translation
   - simple pronunciation
   - 2 or 3 easy example sentences with Uzbek translations.
2. If Ahror writes an English sentence with a mistake:
   - show the corrected sentence
   - explain the mistake briefly in Uzbek
   - give the Uzbek translation.
3. Keep answers concise and easy to understand.
4. Do not make explanations unnecessarily complicated.
5. Ahror may write in Uzbek Cyrillic or Latin script. Understand both.
6. If he asks in Russian, you may answer in Russian when appropriate.
"""

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    # Telegram messages have a length limit, so split long replies.
    for i in range(0, len(text), 4000):
        requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text[i:i + 4000]
            },
            timeout=30
        )


@app.route("/", methods=["GET"])
def home():
    return "Ahror English Bot is running!", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    user_text = message.get("text")

    if not chat_id or not user_text:
        return "OK", 200

    try:
        response = client.responses.create(
            model="gpt-5-mini",
            instructions=SYSTEM_PROMPT,
            input=user_text
        )

        answer = response.output_text
        send_telegram_message(chat_id, answer)

    except Exception as e:
        print(f"Error: {e}")
        send_telegram_message(
            chat_id,
            "Хатолик юз берди. Бироздан кейин яна уриниб кўринг."
        )

    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
