"""同期声对齐 API"""

import logging
import traceback
import uuid
from datetime import datetime, timezone
from typing import Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, QueueTask
from routes.auth import get_current_user, User
from utils.asr_align import align_soundbites, extract_soundbites

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/asr", tags=["asr"])


class AlignRequest(BaseModel):
    video_url: str
    manuscript: str
    model_size: str = "small"


class AlignedSegmentOut(BaseModel):
    original_text: str
    start_time: int
    end_time: int
    matched_text: str
    confidence: float
    clip_id: Optional[str] = None
    audio_url: Optional[str] = None


class AlignResponse(BaseModel):
    segments: list[AlignedSegmentOut]


@router.post("/align", response_model=AlignResponse)
async def align_soundbites_endpoint(req: AlignRequest, request: Request):
    """对新闻稿中的同期声在视频中定位起止时间。

    - video_url: 视频直链 .mp4 URL
    - manuscript: 完整新闻稿文本（含【同期声】/【正文】标签）
    - model_size: Whisper 模型大小 (tiny/base/small/medium/large-v3)
    """
    # 先快速检查有没有同期声
    stubs = extract_soundbites(req.manuscript)
    if not stubs:
        raise HTTPException(status_code=400, detail="新闻稿中未找到【同期声】标签")

    logger.info(f"Aligning {len(stubs)} soundbite(s) from video {req.video_url[:80]}...")

    try:
        segments = align_soundbites(
            video_url=req.video_url,
            manuscript=req.manuscript,
            model_size=req.model_size,
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"模型文件未找到: {e}"
                f" | 请检查: 1) 设置 HF_ENDPOINT=https://hf-mirror.com 环境变量后重试"
                f" 2) 确保服务器可访问 HuggingFace 或镜像站"
            ),
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {e}")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"视频下载失败: {e}")
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"WhisperX 依赖缺失: {e}")
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"ASR align 未预期异常:\n{tb}")
        print(f"\n[ASR ERROR] {tb}\n", flush=True)
        raise HTTPException(status_code=500, detail=f"服务内部错误: {type(e).__name__}: {e}")

    base_url = str(request.base_url).rstrip("/")
    return AlignResponse(
        segments=[
            AlignedSegmentOut(
                original_text=s.original_text,
                start_time=int(round(s.start_time)),
                end_time=int(round(s.end_time)),
                matched_text=s.matched_text,
                confidence=s.confidence,
                clip_id=s.clip_id,
                audio_url=f"{base_url}/audio/clip/{s.clip_id}" if s.clip_id else None,
            )
            for s in segments
        ]
    )


@router.post("/extract-soundbites")
async def extract_soundbites_endpoint(req: dict):
    """仅提取新闻稿中的同期声文本（调试用）。"""
    manuscript = req.get("manuscript", "")
    stubs = extract_soundbites(manuscript)
    return {"count": len(stubs), "soundbites": stubs}


@router.post("/align/async")
def submit_align_async(
    req: AlignRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """提交异步同期声对齐任务，立即返回任务 ID，后台处理。"""
    stubs = extract_soundbites(req.manuscript)
    if not stubs:
        raise HTTPException(status_code=400, detail="新闻稿中未找到【同期声】标签")

    task_id = str(uuid.uuid4())
    task = QueueTask(
        id=task_id,
        user_id=user.id,
        request_data={
            "task_type": "asr_align",
            "video_url": req.video_url,
            "manuscript": req.manuscript,
            "model_size": req.model_size,
        },
        status="pending",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(task)
    db.commit()

    pending_count = db.query(QueueTask).filter(
        QueueTask.status.in_(["pending", "processing"])
    ).count()

    return {
        "task_id": task_id,
        "status": "pending",
        "position": pending_count,
        "message": f"对齐任务已提交，排队位置: {pending_count}",
    }


@router.get("/align/status/{task_id}")
def get_align_status(
    task_id: str,
    db: Session = Depends(get_db),
):
    """查询异步对齐任务的状态和结果。"""
    task = db.query(QueueTask).filter(QueueTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    result = None
    if task.request_data and "result" in task.request_data:
        result = task.request_data["result"]

    return {
        "task_id": task.id,
        "status": task.status,
        "progress": task.progress,
        "error": task.error,
        "result": result,
        "created_at": str(task.created_at),
        "updated_at": str(task.updated_at),
    }
