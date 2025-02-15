import asyncio
import websockets
import json
import wave
from pydub import AudioSegment



WS_URL = "ws://localhost:8000/ws/transcribe"
MP3_FILE_PATH = "audio.mp3"


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

asyncio.run(send_audio())


