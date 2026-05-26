import os, time, requests, json, threading, streamlit as st, telebot
from telebot import TeleBot

# --- ВИЗУАЛЬНЫЕ КОНСТАНТЫ (ASCII-анимация) ---
ICONS = {
    "idle": "💤",   # Спит
    "think": "🌀",  # Думает
    "done": "✅",   # Готово
    "error": "❌",  # Ошибка
    "core": "🧠"    # Главный ИИ
}

# --- КЛАСС АГЕНТА (С симуляцией визуализации) ---
class VisualAgent:
    def __init__(self, name, task_desc):
        self.name = name
        self.task_desc = task_desc
        self.status = "idle"  # Начинаем в статусе "Спит"

    def get_status_line(self):
        """Возвращает строку состояния для Дашборда."""
        icon = ICONS.get(self.status, "❓")
        return f"{icon} **{self.name}**: {self.task_desc}"

# --- ИНИЦИАЛИЗАЦИЯ РОЯ (Симуляция) ---
swarm_agents = [
    VisualAgent("Крипто-Аналитик", "Мониторинг BTC/ETH"),
    VisualAgent("Авито-Менеджер", "Генерация описаний"),
    VisualAgent("Метеоролог", "Прогноз wttr.in")
]

# --- БОТ-ОРКЕСТРАТОР ---
@st.cache_resource
def start_bot():
    bot = TeleBot(st.secrets["TG_TOKEN"])
    
    def get_swarm_dashboard():
        """Генерирует текст полного Дашборда."""
        dashboard = f"{ICONS['core']} **ЦЕНТР УПРАВЛЕНИЯ РОЕМ V1.0**\n"
        dashboard += "─" * 20 + "\n"
        for agent in swarm_agents:
            dashboard += agent.get_status_line() + "\n"
        dashboard += "─" * 20 + "\n"
        dashboard += f"⏳ *Последнее обновление:* {time.strftime('%H:%M:%S')}"
        return dashboard

    @bot.message_handler(commands=['swarm_demo'])
    def swarm_demo(m):
        if str(m.chat.id) != str(st.secrets["TG_CHAT_ID"]): return
        
        # 1. Отправляем начальный Дашборд
        dash_msg = bot.send_message(m.chat.id, get_swarm_dashboard(), parse_mode="Markdown")
        
        # 2. Симуляция деятельности (анимация через редактирование)
        time.sleep(2)
        
        # --- Агент 1 начинает работу ---
        swarm_agents[0].status = "think"
        bot.edit_message_text(chat_id=m.chat.id, message_id=dash_msg.message_id, text=get_swarm_dashboard(), parse_mode="Markdown")
        time.sleep(3) # Симуляция долгого запроса
        
        swarm_agents[0].status = "done"
        bot.edit_message_text(chat_id=m.chat.id, message_id=dash_msg.message_id, text=get_swarm_dashboard(), parse_mode="Markdown")
        time.sleep(2)
        
        # --- Агент 2 начинает работу ---
        swarm_agents[1].status = "think"
        bot.edit_message_text(chat_id=m.chat.id, message_id=dash_msg.message_id, text=get_swarm_dashboard(), parse_mode="Markdown")
        time.sleep(4)
        
        swarm_agents[1].status = "done"
        bot.edit_message_text(chat_id=m.chat.id, message_id=dash_msg.message_id, text=get_swarm_dashboard(), parse_mode="Markdown")

    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    return bot

if "TG_TOKEN" in st.secrets:
    start_bot()
    st.write("### Визуальный движок роя запущен.")
