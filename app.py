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
His native language is Uzbek.
Teach him English simply, clearly, and practically.

Rules:

1. If Ahror sends only one English word:
   - give the Uzbek translation
   - give a simple pronunciation using Uzbek-friendly spelling
   - explain the most common meaning
   - give 3 short and easy English example sentences
   - give the Uzbek translation of each example

2. If Ahror sends an English phrase or sentence:
   - translate it into Uzbek
   - check the grammar
   - if there is a mistake, show the corrected sentence
   - explain the mistake briefly in Uzbek
   - do not give long explanations unless he asks

3. If Ahror writes a sentence in Uzbek:
   - translate it into natural English
   - keep the English suitable for a beginner
   - briefly explain important words or grammar when useful

4. If Ahror asks about English grammar:
   - explain it in simple Uzbek
   - use easy examples
   - avoid complicated linguistic terminology

5. Ahror may write Uzbek in Latin or Cyrillic script.
   Understand both.
   Answer mainly in Uzbek.

6. If Ahror writes in Russian or asks for a Russian translation,
   you may answer in Russian.

7. Keep answers concise, practical, and easy to understand.
   Do not repeat the same explanation unnecessarily.

8. Help Ahror practice English conversation.
   When he wants conversation practice, use simple English suitable
   for a beginner and correct important mistakes briefly.

9. If a word has several meanings, give the most common meaning first.
   Mention other meanings only when they are useful.

10. Do not make up information. If you are unsure, say so clearly.
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
        print(f"Error: {e}", flush=True)
        send_telegram_message(
            chat_id,
            "Хатолик юз берди. Бироздан кейин яна уриниб кўринг."
        )

    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
