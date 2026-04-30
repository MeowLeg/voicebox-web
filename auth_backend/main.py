from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routes.auth import router as auth_router
from routes.records import router as records_router
from routes.queue import router as queue_router
from worker import QueueWorker

app = FastAPI(title="Voicebox Auth Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(records_router)
app.include_router(queue_router)

queue_worker = QueueWorker()


@app.on_event("startup")
def startup():
    init_db()
    queue_worker.start()


@app.on_event("shutdown")
def shutdown():
    queue_worker.stop()


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=17494)
