import os
import time
import requests
import threading
import streamlit as st
import telebot

# 1. Отключаем проблемный трекер OpenTelemetry
os.environ["OTEL_SDK_DISABLED"] = "true"

from crewai import Agent, Task, Crew, LLM

st.set_page_config(page_title="24/7 AI Telegram Bot", page_icon="🤖")
st.title("🤖 Автономный Рой Агентов")
st.write("Бот настроен на круглосуточную работу через Секреты Streamlit.")

# 2. Безопасное чтение данных из Secrets
TG_TOKEN = st.secrets.get("TG_TOKEN", "7735937375:AAGX2u0Ic87mw12z1hEhGlIBYqmtiu3m-gI")
TG_CHAT_ID = st.secrets.get("TG_CHAT_ID", "6028985531")
RAW_KEYS = st.secrets.get("AI_KEYS", "")

# 3. Функция-колбэк (для логов в консоли сервера)
def console_callback(step_output):
    print(f"[AGENT STEP]: {str(step_output)[:100]}...")

# 4. Менеджер ротации РАЗНЫХ провайдеров
class MultiProviderRotator:
    def __init__(self, keys_string):
        self.raw_keys = [k.strip() for k in keys_string.split("\n") if k.strip()]
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

# 5. Функция запуска Роя Агентов
def start_agent_analysis():
    rotator = MultiProviderRotator(RAW_KEYS)
    if not rotator.pool:
        return "❌ Ошибка: В Secrets не добавлены API-ключи нейросетей!"

    max_attempts = 6
    for attempt in range(max_attempts):
        current_cfg = rotator.get_current()
        
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
                step_callback=console_callback
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
                time.sleep(2)
                continue
            else:
                time.sleep(10)
                continue
                
    return "🤖 Все шлюзы сейчас перегружены лимитами. Попробуй позже."

# 6. Инициализация и запуск фонового Telegram-бота
if "bot_loop_active" not in st.session_state:
    bot = telebot.TeleBot(TG_TOKEN)

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        if str(message.chat.id) == TG_CHAT_ID:
            bot.reply_to(message, "👋 Привет! Я твой автономный ИИ-агент.\n\nНапиши мне **Анализ**, и я запущу проверку рынка!")

    @bot.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        if str(message.chat.id) == TG_CHAT_ID:
            user_text = message.text.lower()
            if "анализ" in user_text or user_text == "/analyze":
                bot.send_message(TG_CHAT_ID, "🚀 Запрос принят! Запускаю рой агентов в облаке. Пожалуйста, подожди (это может занять до 1-2 минут)...")
                
                # Запуск анализа напрямую из сохраненных секретов
                report = start_agent_analysis()
                
                bot.send_message(TG_CHAT_ID, f"📊 *Результаты готовы:*\n\n{report}")
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

st.success("✅ Telegram-бот успешно запущен в фоновом потоке и готов к командам!")
