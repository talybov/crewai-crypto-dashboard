import os
import time
import requests
import threading
import streamlit as st
import telebot

st.set_page_config(page_title="24/7 Smart AI Chatbot", page_icon="🤖")
st.title("🤖 Универсальный ИИ-Ассистент V2")
st.write("Сервер активен и контролирует дубликаты бота.")

# 1. Чтение токенов из Secrets
TG_TOKEN = st.secrets.get("TG_TOKEN", "7735937375:AAGX2u0Ic87mw12z1hEhGlIBYqmtiu3m-gI")
TG_CHAT_ID = st.secrets.get("TG_CHAT_ID", "6028985531")
RAW_KEYS = st.secrets.get("AI_KEYS", "")

API_KEYS = [k.strip() for k in RAW_KEYS.split("\n") if k.strip()]

# Инициализируем историю чата в оперативной памяти сервера
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Вытаскиваем первый рабочий ключ Gemini
VALID_GEMINI_KEY = None
for key in API_KEYS:
    if key.startswith("AIzaSy"):
        VALID_GEMINI_KEY = key
        break

# 2. Функция запроса к Gemini (поддерживает формат истории чата)
def ask_gemini_chat(chat_history_list, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": chat_history_list}
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

# 3. Функция быстрого анализа рынка с отправкой процентов сообщениями
def start_light_analysis(bot):
    if not VALID_GEMINI_KEY:
        return "❌ Ошибка: В Secrets нет валидного ключа Gemini (AIzaSy...)"

    prompt_text = """Проанализируй текущую ситуацию на рынке Bitcoin (BTC).
    Учти: сейчас май 2026 года.
    Дай чёткую рекомендацию: КУПИТЬ / ПРОДАТЬ / ДЕРЖАТЬ.
    Объясни своё решение в 3-4 предложениях.
    Ответ должен быть полностью на РУССКОМ языке."""

    try:
        # Отправляем статус 10%
        p_msg = bot.send_message(TG_CHAT_ID, "⏳ *Анализ запущен:* [▓░░░░░░░░░] 10%")
        time.sleep(0.5)
        
        # Меняем на 50%
        try: bot.edit_message_text("⏳ *Сбор данных ИИ:* [▓▓▓▓▓░░░░░] 50%", TG_CHAT_ID, p_msg.message_id)
        except: pass
        
        # Делаем реальный запрос к ИИ
        single_history = [{"role": "user", "parts": [{"text": prompt_text}]}]
        res = ask_gemini_chat(single_history, VALID_GEMINI_KEY)
        
        # Меняем на 100%
        try: bot.edit_message_text("✅ *Готово:* [▓▓▓▓▓▓▓▓▓▓] 100%", TG_CHAT_ID, p_msg.message_id)
        except: pass
        time.sleep(0.5)
        
        # Удаляем техническое сообщение с процентами
        try: bot.delete_message(TG_CHAT_ID, p_msg.message_id)
        except: pass
        
        return res
    except Exception as e:
        return f"❌ Ошибка анализа: {str(e)}"

# 4. Хак против дубликатов: Инициализируем бота глобально на уровне кэша Streamlit
@st.cache_resource(show_spinner=False)
def get_global_bot():
    # Создаем экземпляр бота один раз для всего сервера Streamlit
    bot_instance = telebot.TeleBot(TG_TOKEN)
    
    # Жестко удаляем старый вебхук или зависшие сессии опроса на серверах Telegram перед стартом
    try:
        bot_instance.remove_webhook()
        time.sleep(1)
    except:
        pass
        
    return bot_instance

bot = get_global_bot()

# Регистрируем обработчики сообщений заново при каждом обновлении
@bot.message_handler(commands=['start', 'clear'])
def send_welcome(message):
    if str(message.chat.id) == TG_CHAT_ID:
        st.session_state.chat_history = []
        bot.reply_to(message, "👋 Привет! Я твой обновленный ИИ-партнер.\n\n"
                              "• Напиши **Анализ**, чтобы проверить Биткоин с процентами.\n"
                              "• Пиши **любой другой текст**, чтобы просто болтать на свободные темы.")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if str(message.chat.id) == TG_CHAT_ID:
        user_text = message.text
        user_text_lower = user_text.lower().strip()
        
        # Проверяем команду Анализа
        if user_text_lower in ["анализ", "analyze", "/analyze"]:
            report = start_light_analysis(bot)
            bot.send_message(TG_CHAT_ID, f"📊 *Результаты анализа Биткоина:*\n\n{report}")
            return

        # Свободное общение
        if not VALID_GEMINI_KEY:
            bot.send_message(TG_CHAT_ID, "❌ Добавь работающий ключ Gemini в Секреты.")
            return

        bot.send_chat_action(TG_CHAT_ID, 'typing')

        st.session_state.chat_history.append({"role": "user", "parts": [{"text": user_text}]})
        if len(st.session_state.chat_history) > 20:
            st.session_state.chat_history = st.session_state.chat_history[-20:]

        ai_response = ask_gemini_chat(st.session_state.chat_history, VALID_GEMINI_KEY)

        if ai_response == "LIMIT_EXCEEDED":
            bot.send_message(TG_CHAT_ID, "⚠️ Лимит запросов. Подожди минуту.")
            st.session_state.chat_history.pop()
        elif "ERROR" in ai_response:
            bot.send_message(TG_CHAT_ID, "💥 Ошибка связи с ИИ. Попробуй еще раз.")
            st.session_state.chat_history.pop()
        else:
            st.session_state.chat_history.append({"role": "model", "parts": [{"text": ai_response}]})
            bot.send_message(TG_CHAT_ID, ai_response)

# Функция для непрерывного безопасного опроса
def run_bot_safe(bot_to_run):
    while True:
        try:
            # Прерываем опрос, если кто-то перехватил поток (закрывает ошибку 409)
            bot_to_run.polling(none_stop=True, timeout=20, long_polling_timeout=20)
        except Exception as e:
            # Если словили конфликт 409, даем серверу остыть чуть дольше
            time.sleep(3)

# Запускаем фоновый поток, только если его еще нет в текущей глобальной сессии
if "bot_thread_alive" not in st.session_state:
    t = threading.Thread(target=run_bot_safe, args=(bot,))
    t.daemon = True
    t.start()
    st.session_state.bot_thread_alive = True

st.success("✅ Контроллер бота успешно инициализирован!")
