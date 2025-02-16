import os
import sys
import json
import vosk
import uvicorn
import wave
import websockets

from fastapi import FastAPI, Response
from fastapi.responses import FileResponse, HTMLResponse
from config import MODEL_PATH, SAMPLE_RATE
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from langserve import add_routes
from agent.agent import graph
import asyncio

#Путь к модели. Убедитесь, что директория с моделью существует

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

app.mount('/hls', StaticFiles(directory='hls_content'), name='hls')


@app.get('/test')
async def test():
    return 'Test is good'


@app.get("/transcribe")
async def transcribe_audio():
    wf = wave.open('hls_content/output_000.wav', 'rb')
    rec = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    results = []

    while True:          
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            results.append(rec.Result())
    results.append(rec.FinalResult())
    wf.close()
    parsed_data = [json.loads(item) for item in results]
    return parsed_data



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
                