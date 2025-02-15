import os
import sys
import json
import vosk

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from config import MODEL_PATH, SAMPLE_RATE
import uvicorn

from langserve import add_routes
from agent import graph

# Путь к модели. Убедитесь, что директория с моделью существует



if not os.path.exists(MODEL_PATH):
    print("Ошибка: путь к модели не найден:", MODEL_PATH)
    sys.exit(1)
model = vosk.Model(MODEL_PATH)

app = FastAPI()



add_routes(
    app,
    graph,
    path="/graph",
)



@app.websocket("/ws/transcribe")
async def transcribe_audio(websocket: WebSocket):
    """
    WebSocket-ручка для потокового распознавания речи.
    Ожидает, что клиент будет слать бинарные аудио-фреймы (bytes).
    Отдаёт текст: финальный или промежуточный (partial).
    """
    await websocket.accept()
    rec = vosk.KaldiRecognizer(model, SAMPLE_RATE)

    try:
        while True:
            # Получаем очередную порцию аудиоданных
            data = await websocket.receive_bytes()
            
            # Передаём их в распознаватель
            if rec.AcceptWaveform(data):
                # Если распознали целую фразу
                result_text = json.loads(rec.Result())
                # Отправляем финальный результат
                await websocket.send_text("Сказал: " + result_text["text"])
            else:
                # Промежуточные результаты
                partial_text = json.loads(rec.PartialResult())
                # Можно отправлять промежуточные варианты
                await websocket.send_text("Промежуточно: " + partial_text["partial"])

    except Exception as e:
        print("Ошибка при обработке аудиопотока:", e)

    finally:
        await websocket.close()


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)