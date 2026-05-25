import os
import time
import requests
import threading
import streamlit as st
import telebot

st.set_page_config(page_title="24/7 Smart AI Chatbot", page_icon="🤖")
st.title("🤖 Универсальный ИИ-Ассистент")
st.write("Бот поддерживает свободный диалог, хранит память общения и выполняет задачи.")

# 1. Чтение токенов из Secrets
TG_TOKEN = st.secrets.get("TG_TOKEN", "7735937375:AAGX2u0Ic87mw12z1hEhGlIBYqmtiu3m-gI")
TG_CHAT_ID = st.secrets.get("TG_CHAT_ID", "6028985531")
RAW_KEYS = st.secrets.get("AI_KEYS", "")

API_KEYS = [k.strip() for k in RAW_KEYS.split("\n") if k.strip()]

# Инициализируем историю чата в оперативной памяти сервера (для контекста)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Вытаскиваем первый рабочий ключ Gemini
VALID_GEMINI_KEY = None
for key in API_KEYS:
    if key.startswith("AIzaSy"):
        VALID_GEMINI_KEY = key
        break

# Функция для отрисовки текстового прогресс-бара
def render_progress_bar(percent):
    total_blocks = 10
    filled_blocks = int(percent / 10)
    empty_blocks = total_blocks - filled_blocks
    bar = "▓" * filled_blocks + "░" * empty_blocks
    return f"⏳ *Анализ рынка:* [{bar}] {percent}%"

# 2. Функция запроса к Gemini (поддерживает формат истории чата)
def ask_gemini_chat(chat_history_list, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    # Формируем структуру запроса, которую требует Google для ведения диалога
    payload = {
        "contents": chat_history_list
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        elif response.status_code == 429:
            return "LIMIT_EXCEEDED"
    except Exception as e:
        return f"ERROR: {str(e)}"
    return "ERROR_UNKNOWN"

# 3. Функция быстрого анализа рынка
def start_light_analysis(bot, status_message_id):
    if not VALID_GEMINI_KEY:
        return "❌ Ошибка: В Secrets нет валидного ключа Gemini (AIzaSy...)"

    prompt_text = """Проанализируй текущую ситуацию на рынке Bitcoin (BTC).
    Учти: сейчас май 2026 года.
    Дай чёткую рекомендацию: КУПИТЬ / ПРОДАТЬ / ДЕРЖАТЬ.
    Объясни своё решение в 3-4 предложениях.
    Ответ должен быть полностью на РУССКОМ языке."""

    try:
        bot.edit_message_text(render_progress_bar(20), TG_CHAT_ID, status_message_id, parse_mode="Markdown")
        time.sleep(0.3)
        bot.edit_message_text(render_progress_bar(60), TG_CHAT_ID, status_message_id, parse_mode="Markdown")
        
        # Передаем одиночный запрос в структурированном виде
        single_history = [{"role": "user", "parts": [{"text": prompt_text}]}]
        res = ask_gemini_chat(single_history, VALID_GEMINI_KEY)
        
        bot.edit_message_text(render_progress_bar(90), TG_CHAT_ID, status_message_id, parse_mode="Markdown")
        time.sleep(0.3)
        return res
    except Exception as e:
        return f"❌ Ошибка анализа: {str(e)}"

# 4. Фоновый Telegram-бот с логикой свободного общения
if "bot_loop_active" not in st.session_state:
    bot = telebot.TeleBot(TG_TOKEN)

    @bot.message_handler(commands=['start', 'clear'])
    def send_welcome(message):
        if str(message.chat.id) == TG_CHAT_ID:
            st.session_state.chat_history = [] # Сброс памяти по команде /clear
            bot.reply_to(message, "👋 Привет! Теперь я твой полноценный ИИ-партнер.\n\n"
                                  "• Напиши **Анализ**, чтобы запустить трекинг Биткоина.\n"
                                  "• Пиши **любые другие сообщения**, чтобы просто общаться, обсуждать код, ИИ-агентов или строить планы.\n"
                                  "• Команда `/clear` очистит память нашего диалога.")

    @bot.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        if str(message.chat.id) == TG_CHAT_ID:
            user_text = message.text
            user_text_lower = user_text.lower().strip()
            
            # Проверяем триггер на аналитику
            if user_text_lower in ["анализ", "analyze", "/analyze"]:
                status_msg = bot.send_message(TG_CHAT_ID, render_progress_bar(0), parse_mode="Markdown")
                report = start_light_analysis(bot, status_msg.message_id)
                try:
                    bot.delete_message(TG_CHAT_ID, status_msg.message_id)
                except Exception:
                    pass
                bot.send_message(TG_CHAT_ID, f"📊 *Результаты анализа Биткоина:*\n\n{report}")
                return

            # Если это обычный текст — включаем режим свободного общения
            if not VALID_GEMINI_KEY:
                bot.send_message(TG_CHAT_ID, "❌ Добавь работающий ключ Gemini в Secrets на Streamlit, чтобы я мог отвечать.")
                return

            # Отправляем индикатор того, что ИИ "печатает" сообщение
            bot.send_chat_action(TG_CHAT_ID, 'typing')

            # Добавляем реплику пользователя в историю сессии
            st.session_state.chat_history.append({
                "role": "user",
                "parts": [{"text": user_text}]
            })

            # Ограничиваем память последними 20 сообщениями, чтобы не перегружать контекст
            if len(st.session_state.chat_history) > 20:
                st.session_state.chat_history = st.session_state.chat_history[-20:]

            # Получаем ответ от ИИ с учетом контекста беседы
            ai_response = ask_gemini_chat(st.session_state.chat_history, VALID_GEMINI_KEY)

            if ai_response == "LIMIT_EXCEEDED":
                bot.send_message(TG_CHAT_ID, "⚠️ Мой ключ уперся в лимиты частоты запросов Google. Дай мне минуту перевести дух.")
                # Удаляем последнее сообщение пользователя, раз ИИ на него не ответил
                st.session_state.chat_history.pop()
            elif "ERROR" in ai_response:
                bot.send_message(TG_CHAT_ID, f"💥 Произошла техническая заминка. Попробуй еще раз.")
                st.session_state.chat_history.pop()
            else:
                # Запоминаем ответ самого ИИ
                st.session_state.chat_history.append({
                    "role": "model",
                    "parts": [{"text": ai_response}]
                })
                # Отправляем ответ пользователю в Telegram
                bot.send_message(TG_CHAT_ID, ai_response)

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

st.success("✅ Бот-собеседник успешно запущен и готов к свободному диалогу!")
