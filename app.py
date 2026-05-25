import os, time, requests, json, threading, streamlit as st, telebot, speech_recognition as sr, io
from pydub import AudioSegment
from telebot import TeleBot

MEMORY_FILE = "bot_memory.json"

# --- ЛОГИКА ---
def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"rules": "Ты — главный ИИ-Архитектор Авито-проекта.", "history": []}

def save_memory(data):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except: pass

# --- МОДУЛИ ---
def get_avito_description(image_url):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}", "Content-Type": "application/json"}
    payload = {
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": "Опиши этот товар для объявления на Авито. Сделай продающий заголовок, описание, состояние и призыв к действию."},
            {"type": "image_url", "image_url": {"url": image_url}}
        ]}]
    }
    res = requests.post(url, json=payload, headers=headers).json()
    return res['choices'][0]['message']['content']

def transcribe_voice(file_id, bot):
    file_info = bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{st.secrets['TG_TOKEN']}/{file_info.file_path}"
    audio_data = requests.get(file_url).content
    ogg_audio = AudioSegment.from_file(io.BytesIO(audio_data), format="ogg")
    wav_buffer = io.BytesIO()
    ogg_audio.export(wav_buffer, format="wav")
    wav_buffer.seek(0)
    rec = sr.Recognizer()
    with sr.AudioFile(wav_buffer) as source:
        audio = rec.record(source)
    return rec.recognize_google(audio, language="ru-RU")

# --- БОТ ---
@st.cache_resource
def start_bot():
    bot = TeleBot(st.secrets["TG_TOKEN"])
    
    @bot.message_handler(content_types=['photo'])
    def handle_photo(m):
        bot.reply_to(m, "📸 Анализирую товар для Авито...")
        file_id = m.photo[-1].file_id
        file_info = bot.get_file(file_id)
        image_url = f"https://api.telegram.org/file/bot{st.secrets['TG_TOKEN']}/{file_info.file_path}"
        ans = get_avito_description(image_url)
        bot.send_message(m.chat.id, ans)

    @bot.message_handler(content_types=['voice'])
    def handle_voice(m):
        text = transcribe_voice(m.voice.file_id, bot)
        handle_text(m, text)

    @bot.message_handler(func=lambda m: True)
    def handle_text(m, text=None):
        if str(m.chat.id) != str(st.secrets["TG_CHAT_ID"]): return
        text = text or m.text
        mem = load_memory()
        
        url = "https://api.cohere.com/v1/chat"
        headers = {"Authorization": f"Bearer {st.secrets['COHERE_API_KEY']}", "Content-Type": "application/json"}
        payload = {"model": "command-r-08-2024", "message": text, "preamble": mem["rules"], "chat_history": mem["history"][-10:]}
        
        ans = requests.post(url, json=payload, headers=headers).json().get("text", "...")
        mem["history"].append({"role": "USER", "message": text})
        mem["history"].append({"role": "CHATBOT", "message": ans})
        save_memory(mem)
        bot.send_message(m.chat.id, ans)

    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    return bot

if "TG_TOKEN" in st.secrets:
    start_bot()
    st.write("### Система Авито-Ассистент запущена.")
