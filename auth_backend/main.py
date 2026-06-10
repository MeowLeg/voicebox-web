from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routes.articles import router as articles_router
from routes.auth import router as auth_router
from routes.audio import router as audio_router
from routes.proxy import router as proxy_router
from routes.records import router as records_router
from routes.queue import router as queue_router
from routes.asr import router as asr_router
from worker import QueueWorker

app = FastAPI(title="Voicebox Auth Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles_router)
app.include_router(auth_router)
app.include_router(audio_router)
app.include_router(records_router)
app.include_router(queue_router)
app.include_router(asr_router)
app.include_router(proxy_router)

queue_worker = QueueWorker()


@app.on_event("startup")
def startup():
    init_db()
    queue_worker.start()
    # Trigger video sync in background, then every hour
    import threading
    import time as _time
    from utils.video_fetcher import sync_videos

    def _video_sync_loop():
        while True:
            try:
                sync_videos()
            except Exception:
                pass
            _time.sleep(3600)

    threading.Thread(target=_video_sync_loop, daemon=True).start()


@app.on_event("shutdown")
def shutdown():
    queue_worker.stop()


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=17494)
