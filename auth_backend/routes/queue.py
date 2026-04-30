import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, QueueTask
from routes.auth import get_current_user
from database import User

router = APIRouter(prefix="/queue", tags=["queue"])


class QueueSubmitRequest(BaseModel):
    profile_id: Optional[str] = None
    voice_id: Optional[str] = None
    text: str
    language: Optional[str] = None
    seed: Optional[int] = None
    instruct: Optional[str] = None
    engine: Optional[str] = None
    model_size: Optional[str] = None
    max_chunk_chars: Optional[int] = None
    speed: Optional[float] = None


@router.post("/submit")
def submit_task(
    req: QueueSubmitRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task_id = str(uuid.uuid4())
    task = QueueTask(
        id=task_id,
        user_id=user.id,
        request_data=req.model_dump(exclude_none=True),
        status="pending",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    pending_count = db.query(QueueTask).filter(
        QueueTask.status.in_(["pending", "processing"])
    ).count()

    return {
        "id": task_id,
        "status": "pending",
        "position": pending_count,
        "message": f"任务已加入队列，排队位置: {pending_count}",
    }


@router.get("/tasks")
def list_tasks(
    status: str = None,
    limit: int = 50,
    user_id: str = None,
    db: Session = Depends(get_db),
):
    query = db.query(QueueTask)
    if status:
        query = query.filter(QueueTask.status == status)
    if user_id:
        query = query.filter(QueueTask.user_id == user_id)
    tasks = (
        query.order_by(QueueTask.created_at.asc())
        .limit(limit)
        .all()
    )

    total = db.query(QueueTask).filter(
        QueueTask.status.in_(["pending", "processing"])
    ).count()

    # Calculate position for each pending task
    pending_tasks = db.query(QueueTask).filter(
        QueueTask.status == "pending"
    ).order_by(QueueTask.created_at.asc()).all()
    pending_positions = {t.id: i + 1 for i, t in enumerate(pending_tasks)}
    processing_count = db.query(QueueTask).filter(
        QueueTask.status == "processing"
    ).count()

    return {
        "tasks": [
            {
                "id": t.id,
                "user_id": t.user_id,
                "status": t.status,
                "position": pending_positions.get(t.id, 0) + (1 if t.status == "pending" and processing_count > 0 else 0),
                "progress": t.progress,
                "text": t.request_data.get("text", "")[:100] if t.request_data else "",
                "error": t.error,
                "audio_url": t.audio_url,
                "duration": t.duration,
                "created_at": str(t.created_at),
                "updated_at": str(t.updated_at),
            }
            for t in tasks
        ],
        "active_count": total,
    }


@router.get("/tasks/{task_id}")
def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
):
    task = db.query(QueueTask).filter(QueueTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    pending_count = 0
    if task.status == "pending":
        before = db.query(QueueTask).filter(
            QueueTask.status == "pending",
            QueueTask.id != task_id,
            QueueTask.created_at < task.created_at,
        ).count()
        processing = db.query(QueueTask).filter(
            QueueTask.status == "processing"
        ).count()
        pending_count = before + processing + 1

    return {
        "id": task.id,
        "user_id": task.user_id,
        "status": task.status,
        "position": pending_count,
        "progress": task.progress,
        "error": task.error,
        "audio_url": task.audio_url,
        "duration": task.duration,
        "voicebox_generation_id": task.voicebox_generation_id,
        "request_data": task.request_data,
        "created_at": str(task.created_at),
        "updated_at": str(task.updated_at),
    }


@router.delete("/tasks/{task_id}")
def cancel_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(QueueTask).filter(QueueTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权操作此任务")
    if task.status not in ("pending",):
        raise HTTPException(status_code=400, detail="只能取消排队中的任务")

    task.status = "cancelled"
    task.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"id": task_id, "status": "cancelled", "message": "任务已取消"}


@router.get("/status")
def queue_overview(db: Session = Depends(get_db)):
    pending = db.query(QueueTask).filter(QueueTask.status == "pending").count()
    processing = db.query(QueueTask).filter(QueueTask.status == "processing").first()

    return {
        "pending_count": pending,
        "processing": {
            "id": processing.id,
            "progress": processing.progress,
            "text": processing.request_data.get("text", "")[:100] if processing.request_data else "",
            "created_at": str(processing.created_at),
        } if processing else None,
    }
