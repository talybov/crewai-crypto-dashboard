import os
import time
import requests
import streamlit as st

# 1. Отключаем проблемный трекер OpenTelemetry до импорта CrewAI
os.environ["OTEL_SDK_DISABLED"] = "true"

from crewai import Agent, Task, Crew, LLM

# 2. Настройка стилей страницы Streamlit
st.set_page_config(page_title="Multi-Provider AI Dashboard", page_icon="🤖", layout="wide")

st.title("📊 Умный Мульти-модельный Рой Агентов")
st.subheader("Система динамического распределения нагрузки между ИИ")

# Инициализация сессии для хранения логов агента
if "agent_logs" not in st.session_state:
    st.session_state.agent_logs = ""

# 3. Боковое меню
st.sidebar.markdown("### 🔑 Пул ключей разных Нейросетей")
keys_input = st.sidebar.text_area(
    "Вставь сюда свои ключи (Gemini, Groq), каждый с новой строки:", 
    height=180, 
    placeholder="AIzaSy... (Gemini)\ngsk_... (Groq / Llama)\n..."
)

tg_token = st.sidebar.text_input("Telegram Bot Token:", type="password", value="7735937375:AAGX2u0Ic87mw12z1hEhGlIBYqmtiu3m-gI")
tg_chat_id = st.sidebar.text_input("Telegram Chat ID:", value="6028985531")

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

        def run_crew_with_retry(max_attempts=6):
            for attempt in range(max_attempts):
                current_cfg = rotator.get_current()
                status_area.info(f"⏳ Работаем через [{current_cfg['provider'].upper()}] (Шаг {attempt + 1} из {max_attempts})...")
                
                if current_cfg["provider"] == "gemini":
                    os.environ["GEMINI_API_KEY"] = current_cfg["key"]
                elif current_cfg["provider"] == "groq":
                    os.environ["GROQ_API_KEY"] = current_cfg["key"]

                try:
                    # Настройка LLM с жестким ограничением повторов (max_retries=1)
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
                    return crew.kickoff()

                except Exception as e:
                    st.session_state.agent_logs += f"❌ Сеть {current_cfg['provider'].upper()} перегружена. Даем ей остыть...\n"
                    log_area.code(st.session_state.agent_logs)
                    
                    # Делаем паузу 20 секунд, чтобы сервер провайдера обнулил счетчик запросов
                    for remaining in range(20, 0, -1):
                        status_area.warning(f"⏳ Защитная пауза для {current_cfg['provider'].upper()}. Ждем: {remaining} сек...")
                        time.sleep(1)
                    
                    if rotator.rotate():
                        next_cfg = rotator.get_current()
                        st.session_state.agent_logs += f"🔄 Переключаюсь на шлюз {next_cfg['provider'].upper()}...\n"
                        log_area.code(st.session_state.agent_logs)
                        continue
                    else:
                        continue

        try:
            # Запуск процесса
            crew_output = run_crew_with_retry(max_attempts=6)
            final_report = str(crew_output)
            
            if final_report.strip() == "" or final_report == "None":
                final_report = "🤖 Все ИИ-шлюзы на бесплатном тарифе сейчас перегружены. Пожалуйста, подожди пару минут или попробуй запустить повторно."
            
            status_area.success("✅ Процесс завершен!")
            
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
                    st.warning("⚠️ Не удалось отправить в ТГ. Проверь /start в боте.")

        except Exception as e:
            status_area.error(f"❌ Критическая ошибка: {str(e)}")
