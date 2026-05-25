import os
import time
import requests
import threading
import streamlit as st
import telebot

st.set_page_config(page_title="24/7 AI Telegram Bot", page_icon="🤖")
st.title("🤖 Легкий Автономный Рой Агентов")
st.write("Бот переведен на ультра-легкие прямые запросы для обхода лимитов IP.")

# 1. Чтение токенов из Secrets
TG_TOKEN = st.secrets.get("TG_TOKEN", "7735937375:AAGX2u0Ic87mw12z1hEhGlIBYqmtiu3m-gI")
TG_CHAT_ID = st.secrets.get("TG_CHAT_ID", "6028985531")
RAW_KEYS = st.secrets.get("AI_KEYS", "")

# Получаем список чистых ключей
API_KEYS = [k.strip() for k in RAW_KEYS.split("\n") if k.strip()]

# 2. Функция прямого запроса к Gemini (без CrewAI)
def ask_gemini_direct(prompt, api_key):
    # Используем стабильный эндпоинт для gemini-2.0-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        try:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        except Exception:
            return "ERROR_PARSE"
    elif response.status_code == 429:
        return "LIMIT_EXCEEDED"
    else:
        return "ERROR_UNKNOWN"

# 3. Главный движок аналитики с ротацией
def start_light_analysis():
    if not API_KEYS:
        return "❌ Ошибка: В Secrets не добавлены API-ключи нейросетей!"
        
    prompt_text = """Проанализируй текущую ситуацию на рынке Bitcoin (BTC).
    Учти: сейчас май 2026 года.
    Дай чёткую рекомендацию: КУПИТЬ / ПРОДАТЬ / ДЕРЖАТЬ.
    Объясни своё решение в 3-4 предложениях.
    Ответ должен быть полностью на РУССКОМ языке."""

    # Проходим по кругу по всем твоим ключам
    for index, key in enumerate(API_KEYS):
        # Проверяем только ключи Gemini (начинаются на AIzaSy)
        if not key.startswith("AIzaSy"):
            continue
            
        print(f"Пробуем ключ Gemini №{index + 1}")
        res = ask_gemini_direct(prompt_text, key)
        
        if res == "LIMIT_EXCEEDED":
            print(f"Ключ №{index + 1} превысил лимит, берем следующий...")
            time.sleep(1)
            continue
        elif res in ["ERROR_PARSE", "ERROR_UNKNOWN"]:
            print(f"Сбой ключа №{index + 1}, пробуем дальше...")
            continue
        else:
            # Если получили нормальный текст ответа — возвращаем его
            return res
            
    return "🤖 К сожалению, абсолютно все бесплатные ключи и IP-адрес сервера сейчас заблокированы Google. Пожалуйста, повтори попытку через 5-10 минут, когда сбросятся квоты."

# 4. Фоновый Telegram-бот
if "bot_loop_active" not in st.session_state:
    bot = telebot.TeleBot(TG_TOKEN)

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        if str(message.chat.id) == TG_CHAT_ID:
            bot.reply_to(message, "👋 Привет! Я твой легкий автономный ИИ-агент.\n\nНапиши мне **Анализ**, и я запущу прямую проверку рынка!")

    @bot.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        if str(message.chat.id) == TG_CHAT_ID:
            user_text = message.text.lower()
            if "анализ" in user_text or user_text == "/analyze":
                bot.send_message(TG_CHAT_ID, "🚀 Запрос принят! Делаю прямой запрос к ИИ в обход блокировок...")
                
                # Запуск легкого анализа
                report = start_light_analysis()
                
                bot.send_message(TG_CHAT_ID, f"📊 *Результаты анализа Биткоина:*\n\n{report}")
            else:
                bot.send_message(TG_CHAT_ID, "❓ Напиши слово **Анализ**, чтобы запустить процесс.")

    def run_bot():
        while True:
            try:
                bot.polling(none_stop=True, timeout=60)
            except Exception:
                time.sleep(5)

    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()
    st.session_state.bot_loop_active = True

st.success("✅ Облегченный бот успешно запущен и ждет команд в Telegram!")
