import os
import time
import requests
import threading
import streamlit as st
import telebot

# 1. Отключаем проблемный трекер OpenTelemetry до импорта CrewAI
os.environ["OTEL_SDK_DISABLED"] = "true"

from crewai import Agent, Task, Crew, LLM

# 2. Настройка стилей страницы Streamlit
st.set_page_config(page_title="Multi-Provider AI Dashboard", page_icon="🤖", layout="wide")

st.title("📊 Рой Агентов с управлением через Telegram")
st.subheader("Система запуска анализа рынка прямо из мессенджера")

# Настройки Telegram (Твои данные зашиты по умолчанию)
TG_TOKEN = "7735937375:AAGX2u0Ic87mw12z1hEhGlIBYqmtiu3m-gI"
TG_CHAT_ID = "6028985531"

# Инициализация сессий и глобальных переменных
if "agent_logs" not in st.session_state:
    st.session_state.agent_logs = ""
if "saved_keys" not in st.session_state:
    st.session_state.saved_keys = ""

# Глобальный объект для обмена логами между потоком телеграма и streamlit
if "status_msg" not in st.session_state:
    st.session_state.status_msg = "Ожидание запуска..."

# 3. Боковое меню для ключей
st.sidebar.markdown("### 🔑 Пул ключей разных Нейросетей")
keys_input = st.sidebar.text_area(
    "Вставь сюда свои ключи (Gemini, Groq), каждый с новой строки:", 
    height=150, 
    value=st.session_state.saved_keys,
    placeholder="AIzaSy... (Gemini)\ngsk_... (Groq / Llama)\n..."
)

if st.sidebar.button("💾 Запомнить ключи", use_container_width=True):
    st.session_state.saved_keys = keys_input
    st.sidebar.success("✅ Ключи сохранены в сессии!")

# Разделение экрана на две колонки
col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("### 🤖 Управление Роем")
    start_button = st.button("🚀 Запустить анализ вручную с сайта", use_container_width=True)
    
    status_area = st.empty()
    status_area.info(st.session_state.status_msg)
    result_area = st.empty()

with col2:
    st.markdown("### ⚙️ Внутренние мысли и шаги Агентов")
    log_area = st.empty()
    log_area.code(st.session_state.agent_logs if st.session_state.agent_logs else "Ожидание команды на запуск...")

# 4. Функция для отправки сообщений в Telegram
def send_telegram_message(text):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        payload = {"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Ошибка отправки в ТГ: {e}")

# 5. Функция-колбэк для вывода шагов на экран
def streamlit_callback(step_output):
    if hasattr(step_output, 'thought'):
        thought_text = f"🤖 Мысль агента:\n{step_output.thought}\n\n"
    else:
        thought_text = f"📝 Выполнен шаг:\n{str(step_output)}\n\n"
    st.session_state.agent_logs += thought_text
    log_area.code(st.session_state.agent_logs)

# 6. Умный менеджер ротации РАЗНЫХ провайдеров
class MultiProviderRotator:
    def __init__(self, keys_list):
        self.raw_keys = [k.strip() for k in keys_list if k.strip()]
        self.pool = []
        self.index = 0
        
        for key in self.raw_keys:
            if key.startswith("AIzaSy"):
                self.pool.append({"provider": "gemini", "model": "gemini/gemini-2.0-flash", "key": key})
            elif key.startswith("gsk_"):
                self.pool.append({"provider": "groq", "model": "groq/llama3-70b-8192", "key": key})
            else:
                self.pool.append({"provider": "gemini", "model": "gemini/gemini-2.0-flash", "key": key})
                
    def get_current(self):
        if not self.pool:
            return None
        return self.pool[self.index]
    
    def rotate(self):
        if len(self.pool) > 1:
            self.index = (self.index + 1) % len(self.pool)
            return True
        return False

# 7. ЯДРО СИСТЕМЫ: Функция запуска Роя Агентов
def start_agent_analysis(raw_keys_string):
    global log_area, status_area, result_area
    
    api_keys = raw_keys_string.split("\n") if raw_keys_string else []
    rotator = MultiProviderRotator(api_keys)
    
    if not rotator.pool:
        return "❌ Ошибка: В пуле нет доступных API-ключей нейросетей! Добавь их на сайте."

    max_attempts = 8
    for attempt in range(max_attempts):
        current_cfg = rotator.get_current()
        print(f"Попытка через {current_cfg['provider'].upper()}")
        
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("GROQ_API_KEY", None)

        if current_cfg["provider"] == "gemini":
            os.environ["GEMINI_API_KEY"] = current_cfg["key"]
        elif current_cfg["provider"] == "groq":
            os.environ["GROQ_API_KEY"] = current_cfg["key"]

        try:
            custom_llm = LLM(
                model=current_cfg["model"],
                api_key=current_cfg["key"],
                max_retries=1
            )

            analyst = Agent(
                role="Financial Market Analyst",
                goal="Analyze cryptocurrency market trends and provide clear trading signals",
                backstory="You are an experienced crypto trader. You analyze markets and give clear signals.",
                llm=custom_llm,
                verbose=True,
                step_callback=streamlit_callback
            )

            task = Task(
                description="""Проанализируй текущую ситуацию на рынке Bitcoin (BTC).
                Учти: сейчас май 2026 года.
                Дай чёткую рекомендацию: КУПИТЬ / ПРОДАТЬ / ДЕРЖАТЬ.
                Объясни своё решение в 3-4 предложениях.
                ВАЖНО: Ответ должен быть полностью на РУССКОМ языке.""",
                expected_output="Trading signal with justification in Russian language",
                agent=analyst
            )

            crew = Crew(agents=[analyst], tasks=[task], verbose=True)
            return str(crew.kickoff())

        except Exception as e:
            if rotator.rotate():
                time.sleep(1)
                continue
            else:
                time.sleep(5)
                continue
                
    return "🤖 Все шлюзы сейчас перегружены. Попробуй запустить еще раз через пару минут."

# 8. ЗАПУСК ИЗ ИНТЕРФЕЙСА САЙТА
if start_button:
    st.session_state.agent_logs = "🚀 Запуск мульти-модельного роя...\n"
    log_area.code(st.session_state.agent_logs)
    st.session_state.status_msg = "⏳ Агенты работают над анализом рынка..."
    status_area.info(st.session_state.status_msg)
    
    report = start_agent_analysis(keys_input)
    
    st.session_state.status_msg = "✅ Процесс успешно завершен!"
    status_area.success(st.session_state.status_msg)
    result_area.info(report)
    send_telegram_message(f"📊 *Финальный вердикт ИИ-Агента (Запущено с сайта):*\n\n{report}")


# 9. ФОНОВЫЙ ТЕЛЕГРАМ-БОТ (Слушатель команд)
# Используем синглтон, чтобы поток запускался строго один раз на сервере
if "bot_thread_started" not in st.session_state:
    bot = telebot.TeleBot(TG_TOKEN)

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        if str(message.chat.id) == TG_CHAT_ID:
            bot.reply_to(message, "👋 Привет! Я твой торговый ИИ-агент.\n\nНапиши мне слово **Анализ** или отправь команду `/analyze`, и я запущу рой агентов на сервере для проверки Биткоина!")

    @bot.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        # Реагируем только на твои сообщения для безопасности
        if str(message.chat.id) == TG_CHAT_ID:
            user_text = message.text.lower()
            if "анализ" in user_text or "analyze" in user_text or user_text == "/analyze":
                bot.send_message(TG_CHAT_ID, "🚀 Запрос принят! Запускаю рой агентов на сервере. Это займет некоторое время, собираю мысли...")
                
                # Запускаем сборку отчета (берем текущие сохраненные ключи из сессии)
                report = start_agent_analysis(st.session_state.saved_keys)
                
                # Отправляем результат обратно в ТГ
                bot.send_message(TG_CHAT_ID, f"📊 *Анализ Биткоина готов!*\n\n{report}")
            else:
                bot.send_message(TG_CHAT_ID, "❓ Я умею выполнять только анализ. Напиши слово **Анализ**, чтобы запустить процесс.")

    # Функция для непрерывного фонового опроса Telegram
    def run_bot():
        while True:
            try:
                bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
            except Exception as e:
                time.sleep(5)

    # Запускаем бота в отдельном независимом потоке Python
    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()
    st.session_state.bot_thread_started = True
