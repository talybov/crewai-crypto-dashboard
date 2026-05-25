import os
import time
import requests
import streamlit as st

# 1. Отключаем проблемный трекер OpenTelemetry до импорта CrewAI
os.environ["OTEL_SDK_DISABLED"] = "true"

from crewai import Agent, Task, Crew, LLM

# 2. Настройка стилей страницы Streamlit
st.set_page_config(page_title="Multi-Key Crypto AI Dashboard", page_icon="📊", layout="wide")

st.title("📊 Рой ИИ-Агентов с автоматической отправкой в ТГ")
st.subheader("Автоматический анализ рынка Биткоина")

# Инициализация сессии для хранения логов агента
if "agent_logs" not in st.session_state:
    st.session_state.agent_logs = ""

# 3. Боковое меню (Твои данные Telegram уже вшиты по умолчанию!)
st.sidebar.markdown("### 🔑 Настройки API и Telegram")
keys_input = st.sidebar.text_area(
    "1. Вставь API-ключи Gemini (каждый с новой строки):", 
    height=120, 
    placeholder="AIzaSy...\nAIzaSy..."
)

tg_token = st.sidebar.text_input("2. Telegram Bot Token:", type="password", value="7735937375:AAGX2u0Ic87mw12z1hEhGlIBYqmtiu3m-gI")
tg_chat_id = st.sidebar.text_input("3. Telegram Chat ID:", value="6028985531")

st.sidebar.markdown("""
---
### 💡 Напоминание:
Твой Bot Token и Chat ID уже сохранены в коде. 
Если ты еще не нажал **/start** в своем боте в Telegram, сделай это прямо сейчас, чтобы он смог прислать тебе отчет!
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
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
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

# 6. Менеджер ротации ключей
class KeyRotator:
    def __init__(self, keys_list):
        self.keys = [k.strip() for k in keys_list if k.strip()]
        self.index = 0
    def get_current_key(self):
        if not self.keys:
            return None
        return self.keys[self.index]
    def rotate(self):
        if len(self.keys) > 1:
            self.index = (self.index + 1) % len(self.keys)
            return True
        return False

# 7. Логика работы при нажатии на кнопку
if start_button:
    st.session_state.agent_logs = "🚀 Запуск роя агентов...\n"
    log_area.code(st.session_state.agent_logs)

    api_keys = keys_input.split("\n") if keys_input else []
    rotator = KeyRotator(api_keys)
    
    if not rotator.keys:
        st.error("❌ Сначала вставь хотя бы один API-ключ Gemini в боковое меню!")
    else:
        current_key = rotator.get_current_key()
        os.environ["GEMINI_API_KEY"] = current_key

        status_area.info(f"⏳ Агент начинает анализ рынка (Ключ {rotator.index + 1} из {len(rotator.keys)})...")

        def run_crew_with_retry(max_attempts=5):
            for attempt in range(max_attempts):
                try:
                    active_key = rotator.get_current_key()
                    os.environ["GEMINI_API_KEY"] = active_key
                    
                    custom_llm = LLM(
                        model="gemini/gemini-2.0-flash",
                        api_key=active_key
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
                    if "429" in error_msg or "Quota exceeded" in error_msg:
                        st.session_state.agent_logs += f"⚠️ Ключ №{rotator.index + 1} поймал лимит. Ждем 10 сек...\n"
                        log_area.code(st.session_state.agent_logs)
                        time.sleep(10)
                        if rotator.rotate():
                            st.toast(f"🔄 Переключились на ключ №{rotator.index + 1}")
                        continue
                    else:
                        raise e

        try:
            # Запуск анализа
            crew_output = run_crew_with_retry(max_attempts=5)
            final_report = str(crew_output)
            
            status_area.success("✅ Анализ успешно завершен!")
            
            # Отображаем результат на экране
            with result_area:
                st.markdown("---")
                st.markdown("### 📊 ФИНАЛЬНЫЙ ВЕРДИКТ АГЕНТА:")
                st.info(final_report)
            
            # Отправка отчета в Telegram
            if tg_token and tg_chat_id:
                status_area.info("💬 Отправляю отчет в Telegram...")
                telegram_text = f"📊 *Финальный вердикт ИИ-Агента:*\n\n{final_report}"
                if send_telegram_message(tg_token, tg_chat_id, telegram_text):
                    status_area.success("✅ Анализ завершен, отчет успешно отправлен в Telegram!")
                else:
                    st.warning("⚠️ Анализ готов, но не удалось отправить в ТГ. Проверь, нажал ли ты /start в боте.")

        except Exception as e:
            status_area.error(f"❌ Произошла ошибка: {str(e)}")
