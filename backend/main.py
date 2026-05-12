from contextlib import asynccontextmanager
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from starlette.concurrency import run_in_threadpool

from backend.api_client import predict_delay, send_chat_message, get_train_options, warm_knowledge_base


def _warm_knowledge_base_in_background() -> None:
    """Build chat knowledge base once so chat doesn't block train-options/other routes."""
    try:
        warm_knowledge_base()
    except Exception as e:
        print(f"[startup] Knowledge base warmup failed (chat may be slow on first message): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=_warm_knowledge_base_in_background, daemon=True).start()
    yield


app = FastAPI(title="Rail-Drishti API", lifespan=lifespan)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictRequest(BaseModel):
    Train_id: str
    Train_name: str
    Train_no: str
    Source: str
    Destitnation: str
    Distance_Km: float
    Sc_arr__time: str
    Season: str
    Run_frequency: str
    Date: str

class ChatRequest(BaseModel):
    message: str

@app.get("/api/train-options")
async def api_train_options():
    """Return unique train options for the dropdown."""
    options = await run_in_threadpool(get_train_options)
    return {"success": True, "trains": options}

@app.post("/api/predict")
async def api_predict(request: PredictRequest):
    # Map back the dictionary key for distance
    input_data = request.model_dump()
    input_data['Distance(Km)'] = input_data.pop('Distance_Km')
    
    result = await run_in_threadpool(predict_delay, input_data)
    return result

@app.post("/api/chat")
async def api_chat(request: ChatRequest):
    result = await run_in_threadpool(send_chat_message, request.message)
    return result

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
