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
st.title("🤖 Бессмертный ИИ-Ассистент")

# Чтение токенов из Secrets
TG_TOKEN = st.secrets.get("TG_TOKEN", "")
TG_CHAT_ID = str(st.secrets.get("TG_CHAT_ID", "")).strip()
OR_KEY = st.secrets.get("OPENROUTER_API_KEY", "")
COHERE_KEY = st.secrets.get("COHERE_API_KEY", "")

# Глобальная история и лок для потоков
if "global_cohere_history" not in st.experimental_singleton if hasattr(st, "experimental_singleton") else globals():
    cohere_history = []
else:
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
        print(f"[SYSTEM] Отправка запроса в Cohere...")
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
            print(f"[ERROR] Код Cohere: {response.status_code} — {response.text}")
            return f"⚠️ Ошибка Cohere: {response.status_code}"
    except Exception as e:
        print(f"[CRASH] Ошибка сети Cohere: {str(e)}")
        return f"💥 Исключение Cohere: {str(e)}"

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
        print(f"[SYSTEM] Отправка запроса в OpenRouter...")
        res = requests.post(url, json=payload, headers=headers, timeout=20)
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content']
        return f"⚠️ Ошибка OpenRouter: {res.status_code}"
    except Exception as e:
        return f"💥 Ошибка OpenRouter: {str(e)}"

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
    except Exception as e:
        print(f"[VOICE ERROR] {str(e)}")
        return None

# ГЛОБАЛЬНЫЙ ЗАПУСК БОТА ЧЕРЕЗ КЭШ СЕРВЕРА (Защита от засыпания и дубликатов)
@st.cache_resource(show_spinner=False)
def init_and_run_bot():
    bot_instance = telebot.TeleBot(TG_TOKEN)
    try:
        bot_instance.remove_webhook()
        time.sleep(1)
    except:
        pass

    @bot_instance.message_handler(commands=['start', 'clear'])
    def send_welcome(message):
        if str(message.chat.id) == TG_CHAT_ID:
            global cohere_history
            with history_lock:
                cohere_history.clear()
            bot_instance.send_message(message.chat.id,
                "👋 Привет! Я переведён на стабильный серверный режим.\n\n"
                "• Напиши 'Анализ' — сигнал по BTC\n"
                "• Отправь Голосовое — отвечу текстом\n"
                "• Любой текст — свободное общение\n"
                "• /clear — очистить историю диалога")

    @bot_instance.message_handler(content_types=['voice'])
    def handle_voice(message):
        if str(message.chat.id) != TG_CHAT_ID:
            return
        try:
            bot_instance.send_chat_action(message.chat.id, 'typing')
            text = transcribe_voice(message.voice.file_id, bot_instance)
            if text:
                print(f"[VOICE] Распознано: {text}")
                ai_response = ask_cohere_chat(text)
                bot_instance.send_message(message.chat.id, ai_response)
            else:
                bot_instance.send_message(message.chat.id, "❌ Не смог распознать голос.")
        except Exception as e:
            bot_instance.send_message(message.chat.id, f"💥 Ошибка в обработке голоса: {str(e)}")

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
                try: bot_instance.delete_message(message.chat.id, p_msg.message_id)
                except: pass
                bot_instance.send_message(message.chat.id, f"📊 Анализ Bitcoin:\n\n{report}")
                return
                
            bot_instance.send_chat_action(message.chat.id, 'typing')
            ai_response = ask_cohere_chat(user_text)
            bot_instance.send_message(message.chat.id, ai_response)
        except Exception as e:
            bot_instance.send_message(message.chat.id, f"💥 Ошибка: {str(e)}")

    # Запуск бесконечного цикла в демоническом потоке
    def run_polling():
        print("[SYSTEM] Фоновый поток бота успешно запущен!")
        while True:
            try:
                bot_instance.polling(none_stop=True, timeout=20, long_polling_timeout=20)
            except Exception as e:
                print(f"[POLLING ERROR] Конфликт или сбой сети: {str(e)}")
                time.sleep(5)

    t = threading.Thread(target=run_polling)
    t.daemon = True
    t.start()
    return bot_instance

# Главный пуск
if TG_TOKEN:
    bot = init_and_run_bot()
    st.success("✅ Бот успешно привязан к серверу и работает 24/7!")
else:
    st.error("❌ Заполните TG_TOKEN в Secrets!")
