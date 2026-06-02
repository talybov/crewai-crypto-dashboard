import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime
import time
from agent_state import update_agent_status, get_all_states

# 1. КОНФИГУРАЦИЯ СТРАНИЦЫ (вызывается только один раз!)
st.set_page_config(page_title="Polymarket AI Swarm", layout="wide")

# 2. ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ
@st.cache_data(ttl=300) # Кэшируем на 5 минут, чтобы не спамить API
def get_polymarket_markets():
    """Получаем топ рынки Polymarket по объему за 24 часа"""
    url = "https://gamma-api.polymarket.com/markets"
    params = {"closed": "false", "limit": 15, "order": "volume24hr", "ascending": "false"}
    try:
        return requests.get(url, params=params).json()
    except Exception as e:
        st.error(f"Ошибка API: {e}")
        return []

def run_crew_simulation(market_question):
    """
    Эмуляция работы роя CrewAI. 
    В следующем шаге мы заменим это на реальный вызов агентов.
    """
    agents_tasks = {
        "Market Scanner": "Сканирует ликвидность и текущие odds...",
        "News Analyst": "Ищет свежие новости через DuckDuckGo...",
        "Resolution Lawyer": "Читает мелкий шрифт правил резолюции...",
        "Strategy Lead": "Считает Expected Value (EV) и ищет неэффективность..."
    }
    
    results = []
    for agent, task in agents_tasks.items():
        # Обновляем статус в твоем JSON файле
        update_agent_status(agent, "Активен", task)
        time.sleep(1.5) # Имитация задержки работы LLM
        update_agent_status(agent, "Завершен", f"Нашел инсайты по {market_question}")
        results.append(f"✅ {agent}: {task} Готово.")
    return results

# 3. ИНТЕРФЕЙС ДАШБОРДА
st.title("🦇 Polymarket AI Swarm Dashboard")

# --- БОКОВАЯ ПАНЕЛЬ (ОФИС АГЕНТОВ И НАСТРОЙКИ) ---
with st.sidebar:
    st.header("🏢 Операционный штаб")
    
    # Отображаем статусы из твоего agent_state.py
    states = get_all_states()
    if not states:
        st.info("Агенты спят. Запустите анализ!")
    else:
        for agent, info in states.items():
            icon = "🟢" if info['status'] == 'Активен' else "⚪"
            st.markdown(f"**{icon} {agent}**")
            st.caption(f"_{info['task']}_")
            st.divider()
            
    st.markdown("---")
    
    # Загрузка рынков
    markets = get_polymarket_markets()
    if not markets:
        st.stop()
        
    market_options = {m['question']: m for m in markets}
    selected_q = st.selectbox("Выберите рынок для анализа", list(market_options.keys()))
    selected_market = market_options[selected_q]
    
    run_btn = st.button("🚀 Запустить Рой Агентов", type="primary", use_container_width=True)

# --- ОСНОВНАЯ ОБЛАСТЬ ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"📊 {selected_q}")
    
    # Парсим текущие цены из API Polymarket (формат обычно "[0.65, 0.35]")
    try:
        prices = eval(selected_market.get('outcomePrices', '[]'))
        yes_price = float(prices[0]) * 100 if prices else 50.0
    except:
        yes_price = 50.0
        
    # График Plotly (Пока генерируем синтетическую историю, для реальной нужен CLOB API)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pd.date_range(end=datetime.now(), periods=24, freq='h'),
        y=[yes_price + i*0.2 - 2 for i in range(24)], 
        mode='lines+markers',
        name='Вероятность YES (%)',
        line=dict(color='#00FFFF', width=3)
    ))
    fig.update_layout(
        template="plotly_dark", 
        height=400, 
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Метрики
    m1, m2, m3 = st.columns(3)
    m1.metric("Текущая цена YES", f"{yes_price:.1f}%")
    m2.metric("Объем 24ч", f"${float(selected_market.get('volume24hr', 0)):,.0f}")
    m3.metric("Ликвидность", f"${float(selected_market.get('liquidity', 0)):,.0f}")

with col2:
    st.subheader("📋 Логи работы роя")
    
    if run_btn:
        # Используем st.status для красивой анимации выполнения
        with st.status("Рой агентов анализирует рынок...", expanded=True) as status:
            logs = run_crew_simulation(selected_q)
            for log in logs:
                st.write(log)
            status.update(label="Анализ завершен!", state="complete", expanded=False)
            
        st.balloons()
        st.success("🎯 **Вердикт Стратега**: Рынок неэффективен! ИИ оценивает вероятность в 72%, рынок дает 55%. Сигнал: **BUY YES**.")
    else:
        st.info("Выберите рынок слева и нажмите 'Запустить Рой'.")
