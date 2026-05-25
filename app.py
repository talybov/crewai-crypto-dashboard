import os
import time
import streamlit as st

# 1. Отключаем проблемный трекер OpenTelemetry до импорта CrewAI
os.environ["OTEL_SDK_DISABLED"] = "true"

from crewai import Agent, Task, Crew, LLM

# 2. Настройка стилей страницы Streamlit
st.set_page_config(page_title="Multi-Key Crypto AI Dashboard", page_icon="📊", layout="wide")

st.title("📊 Рой ИИ-Агентов с ротацией и паузами")
st.subheader("Система обхода лимитов для бесплатного тарифа Gemini")

# Инициализация сессии для хранения логов агента, чтобы они не пропадали
if "agent_logs" not in st.session_state:
    st.session_state.agent_logs = ""

# 3. Боковое меню для ввода НЕСКОЛЬКИХ ключей
st.sidebar.markdown("### 🔑 Пул API-ключей Gemini")
keys_input = st.sidebar.text_area(
    "Вставь сюда свои API-ключи (каждый ключ с новой строки):", 
    height=150, 
    placeholder="AIzaSy...\nAIzaSy...\nAIzaSy..."
)

st.sidebar.markdown("""
### 💡 Как это работает?
Программа создаст из ключей очередь. Если один ключ или IP-адрес упрется в лимит, система сделает паузу 10 секунд, переключится на следующий ключ и продолжит работу без вылета!
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
    # Сразу показываем текущие логи (или пустоту)
    log_area.code(st.session_state.agent_logs if st.session_state.agent_logs else "Ожидание запуска агента...")

# 4. Функция-колбэк, которая вызывается СТРОГО на каждом шаге агента
def streamlit_callback(step_output):
    # Извлекаем текст мысли агента
    if hasattr(step_output, 'thought'):
        thought_text = f"🤖 Мысль агента:\n{step_output.thought}\n\n"
    else:
        thought_text = f"📝 Выполнен шаг:\n{str(step_output)}\n\n"
    
    # Добавляем в историю и мгновенно обновляем интерфейс
    st.session_state.agent_logs += thought_text
    log_area.code(st.session_state.agent_logs)

# 5. Менеджер ротации ключей
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

# 6. Логика работы при нажатии на кнопку
if start_button:
    # Очищаем логи перед новым запуском
    st.session_state.agent_logs = "🚀 Запуск роя агентов...\n"
    log_area.code(st.session_state.agent_logs)

    # Разбираем введенные ключи по строкам
    api_keys = keys_input.split("\n") if keys_input else []
    rotator = KeyRotator(api_keys)
    
    if not rotator.keys:
        st.error("❌ Сначала вставь хотя бы один API-ключ Gemini в боковое меню!")
    else:
        current_key = rotator.get_current_key()
        os.environ["GEMINI_API_KEY"] = current_key

        status_area.info(f"⏳ Агент начинает анализ рынка (Используется ключ {rotator.index + 1} из {len(rotator.keys)})...")

        # Функция для запуска Crew с возможностью перезапуска при ошибке 429
        def run_crew_with_retry(max_attempts=5):
            for attempt in range(max_attempts):
                try:
                    active_key = rotator.get_current_key()
                    os.environ["GEMINI_API_KEY"] = active_key
                    
                    custom_llm = LLM(
                        model="gemini/gemini-2.0-flash",
                        api_key=active_key
                    )

                    # Передаем streamlit_callback в step_callback агента
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
                        
                        status_area.warning(f"⚠️ Ключ №{rotator.index + 1} уперся в лимиты. Ждем 10 секунд для сброса квот...")
                        time.sleep(10)
                        
                        if rotator.rotate():
                            st.toast(f"🔄 Переключились на ключ №{rotator.index + 1}")
                        continue
                    else:
                        raise e

        try:
            # Запускаем процесс
            result = run_crew_with_retry(max_attempts=5)
            
            status_area.success("✅ Анализ успешно завершен!")
            with result_area:
                st.markdown("---")
                st.markdown("### 📊 ФИНАЛЬНЫЙ ВЕРДИКТ:")
                st.success(str(result))
                
        except Exception as e:
            status_area.error(f"❌ Произошла ошибка после нескольких попыток: {str(e)}")
