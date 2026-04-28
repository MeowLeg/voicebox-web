from datetime import datetime
from typing import Optional
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db, AudioRecord
from routes.auth import get_current_user, User

router = APIRouter(prefix="/records", tags=["records"])


class AudioRecordRequest(BaseModel):
    voicebox_generation_id: Optional[str] = None
    profile_id: Optional[str] = None
    profile_name: Optional[str] = None
    text: str
    language: Optional[str] = None
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    seed: Optional[int] = None
    instruct: Optional[str] = None
    engine: Optional[str] = None
    model_size: Optional[str] = None
    status: str = "completed"


class AudioRecordResponse(BaseModel):
    id: str
    user_id: str
    voicebox_generation_id: Optional[str]
    profile_id: Optional[str]
    profile_name: Optional[str]
    text: str
    language: Optional[str]
    audio_url: Optional[str]
    duration: Optional[float]
    seed: Optional[int]
    instruct: Optional[str]
    engine: Optional[str]
    model_size: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=AudioRecordResponse)
def create_audio_record(
    req: AudioRecordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    import uuid
    record = AudioRecord(
        id=str(uuid.uuid4()),
        user_id=user.id,
        voicebox_generation_id=req.voicebox_generation_id,
        profile_id=req.profile_id,
        profile_name=req.profile_name,
        text=req.text,
        language=req.language,
        audio_url=req.audio_url,
        duration=req.duration,
        seed=req.seed,
        instruct=req.instruct,
        engine=req.engine,
        model_size=req.model_size,
        status=req.status,
        created_at=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("")
def list_audio_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    profile_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(AudioRecord).filter(AudioRecord.user_id == user.id)

    if status:
        query = query.filter(AudioRecord.status == status)
    if profile_id:
        query = query.filter(AudioRecord.profile_id == profile_id)

    total = query.count()
    records = query.order_by(AudioRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    pages = ceil(total / page_size) if page_size > 0 else 0

    return {
        "items": [AudioRecordResponse.model_validate(r) for r in records],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


@router.get("/{record_id}", response_model=AudioRecordResponse)
def get_audio_record(
    record_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = db.query(AudioRecord).filter(
        AudioRecord.id == record_id,
        AudioRecord.user_id == user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


@router.delete("/{record_id}")
def delete_audio_record(
    record_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = db.query(AudioRecord).filter(
        AudioRecord.id == record_id,
        AudioRecord.user_id == user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return {"message": "已删除"}
