import os
import sys
import json
import vosk
import uvicorn
import wave
from pydub import AudioSegment
import websockets

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from config import MODEL_PATH, SAMPLE_RATE
from fastapi.middleware.cors import CORSMiddleware

from langserve import add_routes
from agent import graph
import asyncio

WS_URL = "ws://localhost:8000/ws/transcribe"
MP3_FILE_PATH = "audio.mp3"

# Путь к модели. Убедитесь, что директория с моделью существует

if not os.path.exists(MODEL_PATH):
    print("Ошибка: путь к модели не найден:", MODEL_PATH)
    sys.exit(1)
model = vosk.Model(MODEL_PATH)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_routes(
    app,
    graph,
    path="/graph",
)

@app.get('/test')
async def test():
    return 'Test is good'

@app.get('/test_client')
def test_client():
    asyncio.run(send_audio())

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
                await websocket.send_text(result_text["text"] + ' 1')
            else:
                # Промежуточные результаты
                partial_text = json.loads(rec.PartialResult())
                # Можно отправлять промежуточные варианты
                await websocket.send_text(partial_text["partial"] + ' 0')

    except Exception as e:
        print("Ошибка при обработке аудиопотока:", e)


@app.websocket("/ws/video")
async def video_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # Открываем видеофайл в бинарном режиме
        with open("video.mp4", "rb") as video_file:
            while True:
                chunk = video_file.read(4000)  # читаем чанками по 4КБ (можно настроить размер)
                if not chunk:
                    break
                # Отправляем бинарные данные через WebSocket
                await websocket.send_bytes(chunk)
                # Добавляем небольшую задержку, если необходимо контролировать скорость передачи
                await asyncio.sleep(0.01)
        # После отправки всех чанков можно отправить специальное сообщение, сигнализирующее об окончании потока
        await websocket.send_text("EOF")
    except WebSocketDisconnect:
        print("Клиент отключился")
    except Exception as e:
        print("Ошибка при передаче видео:", e)
    finally:
        await websocket.close()


def convert_mp3_to_wav(mp3_path, wav_path):
    audio = AudioSegment.from_mp3(mp3_path)
    audio = audio.set_channels(1).set_frame_rate(16000)  # Vosk ожидает моно 16kHz
    audio.export(wav_path, format="wav")


async def send_audio():
    WAV_FILE_PATH = "converted_audio.wav"
    convert_mp3_to_wav(MP3_FILE_PATH, WAV_FILE_PATH)

    with wave.open(WAV_FILE_PATH, "rb") as wf:
        async with websockets.connect(WS_URL) as websocket:
            print("Подключение к WebSocket...")
            chunk_size = 4000  # Размер фрагмента (примерно 0.25 секунды)

            while True:
                chunk = wf.readframes(chunk_size)
                if not chunk:
                    break  

                await websocket.send(chunk)  
                response = await websocket.recv()
                print("Сервер:", response)

            print("Аудио отправлено, закрываем соединение.")

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)