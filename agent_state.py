import sys
import os

# Добавляем текущую директорию в системный путь, чтобы импорты работали всегда
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Теперь импорт сработает, даже если есть проблемы с путями в облаке
try:
    from agent_state import get_all_states
except ModuleNotFoundError:
    # Создаем заглушку, чтобы приложение не падало, если файла физически нет
    def get_all_states():
        return {}
    st.error("Файл agent_state.py не найден. Убедитесь, что он загружен в репозиторий.")
