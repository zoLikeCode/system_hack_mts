from fastapi import FastAPI, WebSocket, Depends, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import websockets
import asyncio
import wave
import uvicorn
from pydub import AudioSegment

from database import SessionLocal, engine

app = FastAPI()
WS_URL_MICROSERVICE_ST2 = "ws://localhost:8000"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
    expose_headers=["*"],  
)

def get_db():
    db = SessionLocal()
    try:
      yield db
    finally:
      db.close()

@app.get('/start')
async def start():
   return 'Привет';

@app.get('/ws/video/')
def wsAudio():
   asyncio.run(send_audio())
   return {'Info': 'Начало передачи информации'}



async def send_audio():
   uri = WS_URL_MICROSERVICE_ST2 + '/ws/transcribe'
   async with websockets.connect(uri) as ws:
      audio = AudioSegment.from_wav('audio_2025-02-15_16-46-37.wav')
      audio = audio.set_frame_rate(16000)
      audio.export("output_16000hz.wav", format="wav")
      with wave.open('output_16000hz.wav', 'rb') as wf:
         chunk_size = 4000
         data = wf.readframes(chunk_size)
         while data:
            await ws.send(data)
            response = await ws.recv()
            data = wf.readframes(chunk_size)
            
            print(response)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
      