import os
import time
import requests
import threading
import streamlit as st
import telebot
import speech_recognition as sr
from pydub import AudioSegment
import io

st.set_page_config(page_title="24/7 Dual AI Bot", page_icon="🤖")
st.title("🤖 Умный ИИ-Ассистент")

TG_TOKEN = st.secrets.get("TG_TOKEN", "")
TG_CHAT_ID = str(st.secrets.get("TG_CHAT_ID", "")).strip()
OR_KEY = st.secrets.get("OPENROUTER_API_KEY", "")
COHERE_KEY = st.secrets.get("COHERE_API_KEY", "")

cohere_history = []
history_lock = threading.Lock()


def ask_cohere_chat(user_message):
    global cohere_history
    if not COHERE_KEY:
        return "❌ Нет COHERE_API_KEY!"
    url = "https://api.cohere.com/v1/chat"
    headers = {"Authorization": f"Bearer {COHERE_KEY}", "Content-Type": "application/json"}
    with history_lock:
        current_history = list(cohere_history)
    payload = {
        "model": "command-r-08-2024",
        "message": user_message,
        "chat_history": current_history,
        "preamble": "Ты — умный универсальный ИИ-ассистент. Отвечай на русском языке, дружелюбно, развёрнуто и по делу. Всегда добавляй своё мнение или полезную информацию."
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            ai_text = response.json().get("text", "Нет ответа")
            with history_lock:
                cohere_history.append({"role": "USER", "message": user_message})
                cohere_history.append({"role": "CHATBOT", "message": ai_text})
                if len(cohere_history) > 20:
                    cohere_history = cohere_history[-20:]
            return ai_text
        else:
            return f"⚠️ Ошибка Cohere: {response.status_code} — {response.text[:200]}"
    except Exception as e:
        return f"💥 Исключение: {str(e)}"


def ask_openrouter_analysis():
    if not OR_KEY:
        return "❌ Нет OPENROUTER_API_KEY"
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OR_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [{"role": "user", "content": "Проанализируй рынок Bitcoin. Дай рекомендацию КУПИТЬ/ПРОДАТЬ/ДЕРЖАТЬ, объясни в 3-4 предложениях на русском."}]
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=20)
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content']
        return f"⚠️ Ошибка OpenRouter: {res.status_code}"
    except Exception as e:
        return f"💥 Ошибка: {str(e)}"


def transcribe_voice(file_id, bot_instance):
    try:
        file_info = bot_instance.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TG_TOKEN}/{file_info.file_path}"
        audio_data = requests.get(file_url).content
        ogg_audio = AudioSegment.from_file(io.BytesIO(audio_data), format="ogg")
        wav_buffer = io.BytesIO()
        ogg_audio.export(wav_buffer, format="wav")
        wav_buffer.seek(0)
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_buffer) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio, language="ru-RU")
    except Exception:
        return None


def start_bot_thread():
    global cohere_history
    bot_instance = telebot.TeleBot(TG_TOKEN)
    try:
        bot_instance.remove_webhook()
    except Exception:
        pass

    @bot_instance.message_handler(commands=['start', 'clear'])
    def send_welcome(message):
        if str(message.chat.id) == TG_CHAT_ID:
            with history_lock:
                cohere_history.clear()
            bot_instance.send_message(message.chat.id,
                "👋 Привет! Я на связи.\n\n"
                "• Напиши Анализ — сигнал по BTC\n"
                "• Голосовое — отвечу сразу\n"
                "• Любой текст — поговорим\n"
                "• /clear — очистить историю")

    @bot_instance.message_handler(content_types=['voice'])
    def handle_voice(message):
        if str(message.chat.id) != TG_CHAT_ID:
            return
        try:
            bot_instance.send_chat_action(message.chat.id, 'typing')
            text = transcribe_voice(message.voice.file_id, bot_instance)
            if text:
                ai_response = ask_cohere_chat(text)
                bot_instance.send_message(message.chat.id, ai_response)
            else:
                bot_instance.send_message(message.chat.id, "❌ Не смог распознать голос.")
        except Exception as e:
            bot_instance.send_message(message.chat.id, f"💥 Ошибка голос: {str(e)}")

    @bot_instance.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        if str(message.chat.id) != TG_CHAT_ID:
            return
        try:
            user_text = message.text or ""
            user_text_lower = user_text.lower().strip()
            if user_text_lower in ["анализ", "analyze", "/analyze"]:
                p_msg = bot_instance.send_message(message.chat.id, "⏳ Анализирую рынок...")
                report = ask_openrouter_analysis()
                try:
                    bot_instance.delete_message(message.chat.id, p_msg.message_id)
                except Exception:
                    pass
                bot_instance.send_message(message.chat.id, f"📊 Анализ Bitcoin:\n\n{report}")
                return
            bot_instance.send_chat_action(message.chat.id, 'typing')
            ai_response = ask_cohere_chat(user_text)
            bot_instance.send_message(message.chat.id, ai_response)
        except Exception as e:
            bot_instance.send_message(message.chat.id, f"💥 Ошибка: {str(e)}")

    def run_polling():
        while True:
            try:
                bot_instance.polling(none_stop=True, timeout=20)
            except Exception:
                time.sleep(3)

    t = threading.Thread(target=run_polling)
    t.daemon = True
    t.start()


if TG_TOKEN:
    if "bot_started" not in st.session_state:
        start_bot_thread()
        st.session_state.bot_started = True
    st.success("✅ Бот запущен!")
else:
    st.error("❌ Не найден TG_TOKEN!")
