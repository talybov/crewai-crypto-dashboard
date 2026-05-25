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
st.title("🤖 Изолированный ИИ-Ассистент")
st.write("Свободное общение + голосовые сообщения через Cohere Command.")

TG_TOKEN = st.secrets.get("TG_TOKEN", "")
TG_CHAT_ID = str(st.secrets.get("TG_CHAT_ID", "")).strip()
OR_KEY = st.secrets.get("OPENROUTER_API_KEY", "")
COHERE_KEY = st.secrets.get("COHERE_API_KEY", "")

if "cohere_history" not in st.session_state:
    st.session_state.cohere_history = []

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
    except:
        pass
    return "🤖 Лимиты OpenRouter заняты. Попробуй позже!"

def ask_cohere_chat(user_message):
    if not COHERE_KEY:
        return "❌ Нет COHERE_API_KEY!"
    url = "https://api.cohere.com/v1/chat"
    headers = {"Authorization": f"Bearer {COHERE_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "command-r",
        "message": user_message,
        "chat_history": st.session_state.cohere_history,
        "preamble": "Ты — продвинутый ИИ-инженер и партнёр пользователя. Вы вместе разрабатываете систему ИИ-агентов. Отвечай кратко, дружелюбно, только на русском языке."
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=25)
        if response.status_code == 200:
            result = response.json()
            ai_text = result.get("text", "")
            st.session_state.cohere_history.append({"role": "USER", "message": user_message})
            st.session_state.cohere_history.append({"role": "CHATBOT", "message": ai_text})
            if len(st.session_state.cohere_history) > 15:
                st.session_state.cohere_history = st.session_state.cohere_history[-15:]
            return ai_text
        else:
            return f"⚠️ Ошибка Cohere (Код {response.status_code})"
    except Exception as e:
        return f"💥 Сбой сети: {str(e)}"

def transcribe_voice(file_id, bot_instance):
    try:
        file_info = bot_instance.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TG_TOKEN}/{file_info.file_path}"
        audio_data = requests.get(file_url).content
        ogg_audio = AudioSegment.from_ogg(io.BytesIO(audio_data))
        wav_buffer = io.BytesIO()
        ogg_audio.export(wav_buffer, format="wav")
        wav_buffer.seek(0)
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_buffer) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language="ru-RU")
        return text
    except Exception as e:
        return None

@st.cache_resource(show_spinner=False)
def get_global_bot():
    bot_instance = telebot.TeleBot(TG_TOKEN)
    try:
        bot_instance.remove_webhook()
    except:
        pass
    return bot_instance

if TG_TOKEN:
    bot = get_global_bot()

    @bot.message_handler(commands=['start', 'clear'])
    def send_welcome(message):
        if str(message.chat.id) == TG_CHAT_ID:
            st.session_state.cohere_history = []
            bot.reply_to(message, "👋 Привет! Я на связи.\n\n"
                                  "• Напиши Анализ — получишь сигнал по BTC\n"
                                  "• Отправь голосовое — распознаю и отвечу\n"
                                  "• Любой текст — свободное общение")

    @bot.message_handler(content_types=['voice'])
    def handle_voice(message):
        if str(message.chat.id) != TG_CHAT_ID:
            return
        bot.send_chat_action(message.chat.id, 'typing')
        bot.send_message(message.chat.id, "🎙 Распознаю голосовое...")
        text = transcribe_voice(message.voice.file_id, bot)
        if text:
            bot.send_message(message.chat.id, f"🗣 Ты сказал: {text}")
            ai_response = ask_cohere_chat(text)
            bot.send_message(message.chat.id, ai_response)
        else:
            bot.send_message(message.chat.id, "❌ Не смог распознать. Попробуй ещё раз!")

    @bot.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        if str(message.chat.id) != TG_CHAT_ID:
            return
        user_text = message.text
        user_text_lower = user_text.lower().strip()
        if user_text_lower in ["анализ", "analyze", "/analyze"]:
            p_msg = bot.send_message(message.chat.id, "⏳ Анализ запущен: [▓▓▓▓░░░░░░] 40%")
            report = ask_openrouter_analysis()
            try:
                bot.delete_message(message.chat.id, p_msg.message_id)
            except:
                pass
            bot.send_message(message.chat.id, f"📊 Анализ Bitcoin:\n\n{report}")
            return
        bot.send_chat_action(message.chat.id, 'typing')
        ai_response = ask_cohere_chat(user_text)
        bot.send_message(message.chat.id, ai_response)

    def run_bot_safe(bot_to_run):
        while True:
            try:
                bot_to_run.polling(none_stop=True, timeout=20)
            except:
                time.sleep(3)

    if "bot_thread_alive" not in st.session_state:
        t = threading.Thread(target=run_bot_safe, args=(bot,))
        t.daemon = True
        t.start()
        st.session_state.bot_thread_alive = True

    st.success("✅ Бот запущен! Голосовые сообщения поддерживаются 🎙")
