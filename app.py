import os
import time
import requests
import streamlit as st

# 1. Отключаем проблемный трекер OpenTelemetry до импорта CrewAI
os.environ["OTEL_SDK_DISABLED"] = "true"

from crewai import Agent, Task, Crew, LLM

# 2. Настройка стилей страницы Streamlit
st.set_page_config(page_title="Multi-Provider AI Dashboard", page_icon="🤖", layout="wide")

st.title("📊 Мульти-модельный Рой Агентов (Обход Лимитов)")
st.subheader("Автоматическое переключение между Gemini, Groq (Llama) и другими ИИ")

# Инициализация сессии для хранения логов агента
if "agent_logs" not in st.session_state:
    st.session_state.agent_logs = ""

# 3. Боковое меню (Твои данные Telegram уже вшиты)
st.sidebar.markdown("### 🔑 Пул ключей разных Нейросетей")
keys_input = st.sidebar.text_area(
    "Вставь сюда ВСЕ свои ключи (Gemini, Groq и др.) в любом порядке, каждый с новой строки:", 
    height=180, 
    placeholder="AIzaSy... (Gemini)\ngsk_... (Groq / Llama)\n..."
)

tg_token = st.sidebar.text_input("Telegram Bot Token:", type="password", value="7735937375:AAGX2u0Ic87mw12z1hEhGlIBYqmtiu3m-gI")
tg_chat_id = st.sidebar.text_input("Telegram Chat ID:", value="6028985531")

st.sidebar.markdown("""
---
### 💡 Какие ключи можно миксовать?
* **Gemini:** начинается на `AIzaSy...`
* **Groq (Llama 3):** начинается на `gsk_...` (брать на console.groq.com)

Система сама поймет, какой это провайдер, и переключит модель на лету без пауз!
""")

# Разделение экрана на две колонки
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 🤖 Управление Роем")
    start_button = st.button("🚀 Запустить анализ Биткоина", use_container_width=True)
    
    status_area = st.empty()
    result_area = st.empty()

with col2:
    st.markdown("### ⚙️ Внутренние мысли и шаги Агентов")
    log_area = st.empty()
    log_area.code(st.session_state.agent_logs if st.session_state.agent_logs else "Ожидание запуска агента...")

# 4. Функция для отправки сообщений в Telegram
def send_telegram_message(token, chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Ошибка отправки в Telegram: {e}")
        return False

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
        
        # Автоматически распознаем провайдера для каждого ключа
        for key in self.raw_keys:
            if key.startswith("AIzaSy"):
                self.pool.append({"provider": "gemini", "model": "gemini/gemini-2.0-flash", "key": key})
            elif key.startswith("gsk_"):
                self.pool.append({"provider": "groq", "model": "groq/llama3-70b-8192", "key": key})
            else:
                # По умолчанию, если префикс неизвестен, пробуем как Gemini
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

# 7. Логика работы при нажатии на кнопку
if start_button:
    st.session_state.agent_logs = "🚀 Запуск мульти-модельного роя...\n"
    log_area.code(st.session_state.agent_logs)

    api_keys = keys_input.split("\n") if keys_input else []
    rotator = MultiProviderRotator(api_keys)
    
    if not rotator.pool:
        st.error("❌ Сначала вставь хотя бы один API-ключ в боковое меню!")
    else:
        current = rotator.get_current()
        status_area.info(f"⏳ Агент запускается на базе [{current['provider'].upper()}] (Модель {rotator.index + 1} из {len(rotator.pool)})...")

        def run_crew_with_retry(max_attempts=5):
            for attempt in range(max_attempts):
                current_cfg = rotator.get_current()
                
                # Принудительно прописываем нужные переменные окружения для litellm
                if current_cfg["provider"] == "gemini":
                    os.environ["GEMINI_API_KEY"] = current_cfg["key"]
                elif current_cfg["provider"] == "groq":
                    os.environ["GROQ_API_KEY"] = current_cfg["key"]

                try:
                    # Инициализируем LLM с правильными параметрами под конкретного провайдера
                    custom_llm = LLM(
                        model=current_cfg["model"],
                        api_key=current_cfg["key"]
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
                    return crew.kickoff()

                except Exception as e:
                    error_msg = str(e)
                    st.session_state.agent_logs += f"❌ Ошибка на модели {current_cfg['provider'].upper()}: лимит или сбой.\n"
                    log_area.code(st.session_state.agent_logs)
                    
                    # Если есть другие провайдеры в пуле — переключаемся МГНОВЕННО, без долгих пауз!
                    if rotator.rotate():
                        next_cfg = rotator.get_current()
                        status_area.warning(f"🔄 Сбой лимитов. Мгновенно переключаюсь на сеть: [{next_cfg['provider'].upper()}]...")
                        time.sleep(2) # Чисто символическая пауза на переключение шлюза
                        continue
                    else:
                        # Если ключ всего один, то делаем стандартную паузу
                        status_area.warning("⏳ Ключи кончились. Ожидаем 30 секунд...")
                        time.sleep(30)
                        continue

        try:
            # Запуск анализа
            crew_output = run_crew_with_retry(max_attempts=len(rotator.pool) + 2)
            final_report = str(crew_output)
            
            if final_report.strip() == "" or final_report == "None":
                final_report = "🤖 Все доступные нейросети в пуле временно перегружены лимитами. Пожалуйста, добавь ключ Groq (Llama) или повтори попытку позже."
            
            status_area.success("✅ Анализ успешно завершен!")
            
            with result_area:
                st.markdown("---")
                st.markdown("### 📊 ФИНАЛЬНЫЙ ВЕРДИКТ АГЕНТА:")
                st.info(final_report)
            
            if tg_token and tg_chat_id:
                status_area.info("💬 Отправляю отчет в Telegram...")
                telegram_text = f"📊 *Финальный вердикт ИИ-Агента:*\n\n{final_report}"
                if send_telegram_message(tg_token, tg_chat_id, telegram_text):
                    status_area.success("✅ Отчет успешно отправлен в Telegram!")
                else:
                    st.warning("⚠️ Не удалось отправить в ТГ. Нажми /start в боте.")

        except Exception as e:
            status_area.error(f"❌ Критическая ошибка: {str(e)}")
