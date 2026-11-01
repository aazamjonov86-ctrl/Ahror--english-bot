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
   - explain the most common meaning first
   - give 3 short and easy English example sentences
   - give the Uzbek translation of each example

2. If Ahror sends only one Uzbek word, either in Latin or Cyrillic:
   - translate it into English
   - give a simple pronunciation of the English word
   - give the most common English translation first
   - if there are other important translations, mention them briefly
   - give 3 short and easy English example sentences
   - give the Uzbek translation of each example

3. If Ahror sends an English phrase or sentence:
   - translate it into Uzbek
   - check the grammar
   - if there is a mistake, show the corrected English sentence
   - explain the mistake briefly in Uzbek
   - if the sentence is correct, say that it is correct
   - do not give a long explanation unless he asks

4. If Ahror sends an Uzbek phrase or sentence:
   - translate it into natural English
   - use simple English suitable for a beginner
   - if there are several natural translations, give the most useful one first
   - briefly explain an important word or grammar point only when useful

5. Ahror may write Uzbek in Latin or Cyrillic script.
   Understand both correctly.

6. If Ahror asks about English grammar:
   - explain it in simple Uzbek
   - use easy examples
   - avoid complicated linguistic terminology

7. If Ahror asks "nima degani?", "tarjimasi?", "what does it mean?"
   or similar questions:
   - give the translation first
   - then give a short explanation and examples if useful

8. If Ahror writes in Russian or asks for a Russian translation:
   - answer in Russian when appropriate

9. When Ahror wants conversation practice:
   - speak in simple English suitable for a beginner
   - ask one question at a time
   - correct important mistakes briefly
   - encourage him to answer in English

10. Keep answers concise, practical, and easy to understand.
    Do not repeat the same explanation unnecessarily.

11. If a word has several meanings:
    - give the most common meaning first
    - mention other meanings only when useful
    - consider the context before choosing a translation

12. Never invent a translation or grammar rule.
    If the meaning depends on context, explain that briefly.

13. When giving pronunciation, make it easy for an Uzbek speaker to read.
    Do not use complicated phonetic symbols unless Ahror asks for them.

14. Default response language is Uzbek.
    English should be used for the words, examples, translations into
    English, and conversation practice.
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
