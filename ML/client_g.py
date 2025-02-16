import requests
import json

# Данные для запроса
url = "http://localhost:8000/graph/invoke"
headers = {'Content-Type': 'application/json'}

config = {"configurable": {"thread_id": "1"}}
user_input = "Статус работника 1004"

# Тело запроса
data = {
    "messages": [{"role": "user", "content": user_input}],
    "name": "Тестовый Тестович",
    "age": 20
}

# Объединяем данные
payload = {
    "input": {
        "messages": [user_input],
        "name": "Тестовый Тестович",
        "age": 20
    },
    "config": {
        "configurable": {
            "checkpoint_id": "1",  # Пример значения
            "checkpoint_ns": "",  # Пустое значение
            "thread_id": "1"  # Пример значения
        }
    },
    "kwargs": {}  # Параметры kwargs, если они не нужны — оставляем пустым
}

# Отправляем POST-запрос
response = requests.post(url, headers=headers, data=json.dumps(payload))

# Проверяем статус и выводим ответ
if response.status_code == 200:
    print("Ответ сервера:", response.json()['output']['messages'][-1])
else:
    print("Ошибка:", response.status_code, response.text)
