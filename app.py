import os
import time
import requests
import threading
import streamlit as st
import telebot

st.set_page_config(page_title="24/7 AI Telegram Bot", page_icon="🤖")
st.title("🤖 ИИ-Бот с индикатором прогресса")
st.write("Бот обновляет статус выполнения задачи в реальном времени.")

# 1. Чтение токенов из Secrets
TG_TOKEN = st.secrets.get("TG_TOKEN", "7735937375:AAGX2u0Ic87mw12z1hEhGlIBYqmtiu3m-gI")
TG_CHAT_ID = st.secrets.get("TG_CHAT_ID", "6028985531")
RAW_KEYS = st.secrets.get("AI_KEYS", "")

API_KEYS = [k.strip() for k in RAW_KEYS.split("\n") if k.strip()]

# Функция для отрисовки текстового прогресс-бара
def render_progress_bar(percent):
    total_blocks = 10
    filled_blocks = int(percent / 10)
    empty_blocks = total_blocks - filled_blocks
    bar = "▓" * filled_blocks + "░" * empty_blocks
    return f"⏳ *Анализ рынка:* [{bar}] {percent}%"

# 2. Функция прямого запроса к Gemini
def ask_gemini_direct(prompt, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        elif response.status_code == 429:
            return "LIMIT_EXCEEDED"
    except Exception:
        return "ERROR"
    return "ERROR"

# 3. Главный движок аналитики с обновлением процентов в ТГ
def start_light_analysis(bot, status_message_id):
    if not API_KEYS:
        return "❌ Ошибка: В Secrets не добавлены API-ключи нейросетей!"
        
    prompt_text = """Проанализируй текущую ситуацию на рынке Bitcoin (BTC).
    Учти: сейчас май 2026 года.
    Дай чёткую рекомендацию: КУПИТЬ / ПРОДАТЬ / ДЕРЖАТЬ.
    Объясни своё решение в 3-4 предложениях.
    Ответ должен быть полностью на РУССКОМ языке."""

    try:
        # 10% - Инициализация пула
        time.sleep(0.5)
        bot.edit_message_text(render_progress_bar(10), TG_CHAT_ID, status_message_id, parse_mode="Markdown")
        
        # 30% - Поиск и проверка валидных ключей
        time.sleep(0.5)
        bot.edit_message_text(render_progress_bar(30), TG_CHAT_ID, status_message_id, parse_mode="Markdown")
        
        valid_key = None
        for key in API_KEYS:
            if key.startswith("AIzaSy"):
                valid_key = key
                break
                
        if not valid_key:
            return "❌ Ошибка: Не найдено подходящих ключей Gemini (начинающихся на AIzaSy)."

        # 50% - Отправка запроса в нейросеть
        bot.edit_message_text(render_progress_bar(50), TG_CHAT_ID, status_message_id, parse_mode="Markdown")
        
        # Получаем ответ от ИИ
        res = ask_gemini_direct(prompt_text, valid_key)
        
        # 80% - Обработка ответа сервером
        bot.edit_message_text(render_progress_bar(80), TG_CHAT_ID, status_message_id, parse_mode="Markdown")
        time.sleep(0.5)
        
        if res == "LIMIT_EXCEEDED":
            return "🤖 Ключ уперся в лимиты запросов Google (429). Попробуй через пару минут."
        elif res == "ERROR":
            return "❌ Не удалось связаться с сервером ИИ. Проверь правильность ключа."
            
        # 100% - Успешное завершение
        bot.edit_message_text(render_progress_bar(100), TG_CHAT_ID, status_message_id, parse_mode="Markdown")
        time.sleep(0.3)
        return res

    except Exception as e:
        return f"❌ Ошибка в процессе генерации: {str(e)}"

# 4. Фоновый Telegram-бот
if "bot_loop_active" not in st.session_state:
    bot = telebot.TeleBot(TG_TOKEN)

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        if str(message.chat.id) == TG_CHAT_ID:
            bot.reply_to(message, "👋 Привет! Я твой автономный ИИ-агент.\n\nНапиши мне **Анализ**, и я запущу проверку рынка с индикатором прогресса!")

    @bot.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        if str(message.chat.id) == TG_CHAT_ID:
            user_text = message.text.lower()
            if "анализ" in user_text or user_text == "/analyze":
                # Отправляем стартовое сообщение, которое будем редактировать
                status_msg = bot.send_message(TG_CHAT_ID, render_progress_bar(0), parse_mode="Markdown")
                
                # Запускаем анализ и передаем туда ID сообщения для изменения процентов
                report = start_light_analysis(bot, status_msg.message_id)
                
                # Удаляем индикатор прогресса, чтобы не засорять чат, и присылаем чистый отчет
                try:
                    bot.delete_message(TG_CHAT_ID, status_msg.message_id)
                except Exception:
                    pass
                    
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

st.success("✅ Бот с анимацией прогресса успешно запущен!")
