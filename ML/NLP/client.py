import asyncio
import websockets
import json
import wave
from pydub import AudioSegment

# URL вашего WebSocket-сервера
WS_URL = "ws://localhost:8000/ws/transcribe"

# Путь к MP3-файлу, который будем отправлять
MP3_FILE_PATH = "audio.mp3"

# Функция для конвертации MP3 в WAV с нужными параметрами
def convert_mp3_to_wav(mp3_path, wav_path):
    audio = AudioSegment.from_mp3(mp3_path)
    audio = audio.set_channels(1).set_frame_rate(16000)  # Vosk ожидает моно 16kHz
    audio.export(wav_path, format="wav")

# Функция для отправки аудио в WebSocket
async def send_audio():
    # Конвертируем MP3 в WAV
    WAV_FILE_PATH = "converted_audio.wav"
    convert_mp3_to_wav(MP3_FILE_PATH, WAV_FILE_PATH)

    # Открываем WAV-файл и читаем по кускам
    with wave.open(WAV_FILE_PATH, "rb") as wf:
        async with websockets.connect(WS_URL) as websocket:
            print("Подключение к WebSocket...")
            chunk_size = 4000  # Размер фрагмента (примерно 0.25 секунды)

            while True:
                chunk = wf.readframes(chunk_size)
                if not chunk:
                    break  # Конец файла

                await websocket.send(chunk)  # Отправляем фрагмент

                # Получаем ответ от сервера
                response = await websocket.recv()
                print("Сервер:", response)

            print("Аудио отправлено, закрываем соединение.")

# Запуск асинхронного клиента
asyncio.run(send_audio())
