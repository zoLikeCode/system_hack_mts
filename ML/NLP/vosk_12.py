import os
import sys
import json
import vosk

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

# Путь к модели. Убедитесь, что директория с моделью существует
MODEL_PATH = 'vosk-model-small-ru-0.22'  # или './vosk-model-small-ru-0.22'
SAMPLE_RATE = 16000

# Проверка модели
if not os.path.exists(MODEL_PATH):
    print("Ошибка: путь к модели не найден:", MODEL_PATH)
    sys.exit(1)

# Загружаем модель Vosk
model = vosk.Model(MODEL_PATH)

app = FastAPI()

# При желании можно отдать простую HTML-страницу для теста:
@app.get("/")
def get_root():
    # HTML для простого теста WebSocket в браузере
    return HTMLResponse(
        """
        <html>
            <head>
                <title>WebSocket Test</title>
            </head>
            <body>
                <h1>WebSocket Russian ASR Test</h1>
                <button onclick="start()">Start</button>
                <script>
                    let ws;
                    function start(){
                        ws = new WebSocket("ws://" + window.location.host + "/ws/transcribe");
                        ws.onopen = () => {
                            console.log("WebSocket open");
                            // Для примера сразу закрываем, чтобы увидеть ответ
                            ws.send("Примерный текст или аудиоданные");
                        }
                        ws.onmessage = (event) => {
                            console.log("Server says:", event.data);
                        }
                    }
                </script>
            </body>
        </html>
        """
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
