import json
import os

STATE_FILE = "agent_states.json"

def update_agent_status(agent_name, status, task):
    """Обновляет состояние агента в JSON файле."""
    data = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
        except:
            data = {}
    
    data[agent_name] = {"status": status, "task": task}
    
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)

def get_all_states():
    """Считывает все состояния агентов."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}
