import os
import sys
import streamlit as st

# Отключаем проблемную телеметрию
os.environ["OTEL_SDK_DISABLED"] = "true"

from crewai import Agent, Task, Crew

# Настройка стилей страницы
st.set_page_config(page_title="Crypto AI Agents Dashboard", page_icon="📊", layout="wide")

st.title("📊 Рой ИИ-Агентов: Финансовый Анализ Рынка")
st.subheader("Мониторинг работы и взаимодействия агентов в реальном времени")

# Ввод API-ключа
gemini_key = st.sidebar.text_input("Введи свой GEMINI_API_KEY:", type="password")

st.sidebar.markdown("""
### Как это работает?
При нажатии кнопки запуска, Агент-Аналитик начинает сканировать рынок. 
В процессе работы его лог мышления будет выводиться в интерактивное окно справа.
""")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 🤖 Управление Роем")
    start_button = st.button("🚀 Запустить анализ Биткоина", use_container_width=True)
    
    status_area = st.empty()
    result_area = st.empty()

with col2:
    st.markdown("### ⚙️ Внутренние мысли и шаги Агентов")
    log_area = st.empty()

# Класс для вывода мыслей в реальном времени
class StreamlitStdoutTrigger:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.text = ""
    def write(self, bytes_data):
        self.text += bytes_data
        self.placeholder.code(self.text)
    def flush(self):
        pass

if start_button:
    if not gemini_key:
        st.error("❌ Сначала вставь свой API-ключ Gemini в боковое меню!")
    else:
        # Устанавливаем ключ среды
        os.environ["GEMINI_API_KEY"] = gemini_key

        status_area.info("⏳ Агент просыпается и начинает анализ рынка...")

        # Инициализируем агента через правильный синтаксис Gemini
        analyst = Agent(
            role="Financial Market Analyst",
            goal="Analyze cryptocurrency market trends and provide clear trading signals",
            backstory="You are an experienced crypto trader. You analyze markets and give clear signals.",
            llm="gemini/gemini-1.5-flash",
            verbose=True
        )

        task = Task(
            description="""Проанализируй текущую ситуацию на рынке Bitcoin (BTC).
            Учти: сейчас май 2026 года.
            Дай чёткую рекомендацию: КУПИТЬ / ПРОДАТЬ / ДЕРЖАТЬ.
            Объясни своё решение в 3-4 sentences.
            ВАЖНО: Ответ должен быть полностью на РУССКОМ языке.""",
            expected_output="Trading signal with justification in Russian language",
            agent=analyst
        )

        crew = Crew(agents=[analyst], tasks=[task], verbose=True)

        # Перехватываем поток вывода терминала
        old_stdout = sys.stdout
        sys.stdout = StreamlitStdoutTrigger(log_area)
        
        try:
            # Запускаем прямым синхронным вызовом (без asyncio)
            result = crew.kickoff()
            
            # Возвращаем стандартный вывод
            sys.stdout = old_stdout
            
            status_area.success("✅ Анализ успешно завершен!")
            with result_area:
                st.markdown("---")
                st.markdown("### 📊 ФИНАЛЬНЫЙ ВЕРДИКТ:")
                st.success(str(result))
                
        except Exception as e:
            sys.stdout = old_stdout
            status_area.error(f"❌ Произошла ошибка: {str(e)}")
