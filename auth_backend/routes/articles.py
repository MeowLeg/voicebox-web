import asyncio
import shutil
import tempfile
import uuid
from pathlib import Path

import re
import requests

import fitz  # pymupdf
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from utils.ftp_upload import upload_to_ftp
from utils.llm_rewrite import extract_and_rewrite_from_images
from routes.auth import has_permission
from database import AudioRecord, User, get_db

router = APIRouter(prefix="/articles", tags=["articles"])


def _pdf_to_images(pdf_path: Path, output_dir: Path) -> list[Path]:
    doc = fitz.open(pdf_path)
    paths = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=200)
        img_path = output_dir / f"page_{i + 1}.png"
        pix.save(img_path)
        paths.append(img_path)
    doc.close()
    return paths


@router.post("/ocr-rewrite")
async def ocr_and_rewrite(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一个文件")

    tmp_dir = Path(tempfile.mkdtemp(prefix="ocr_"))
    image_paths: list[Path] = []

    try:
        for f in files:
            if not f.filename:
                continue
            ext = Path(f.filename).suffix.lower()
            safe_name = f"{uuid.uuid4().hex}{ext}"
            filepath = tmp_dir / safe_name
            content = await f.read()
            filepath.write_bytes(content)

            if ext == ".pdf":
                pdf_images = await asyncio.to_thread(_pdf_to_images, filepath, tmp_dir)
                image_paths.extend(pdf_images)
            else:
                image_paths.append(filepath)

        if not image_paths:
            raise HTTPException(status_code=400, detail="没有有效的图片或PDF文件")

        article = await asyncio.to_thread(extract_and_rewrite_from_images, image_paths)

        return {"article": article}

    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@router.post("/push-ftp/{generation_id}")
async def push_to_ftp(
    generation_id: str,
    user: User = Depends(has_permission("broadcast")),
    db: Session = Depends(get_db),
):
    remote_name = ""
    record = db.query(AudioRecord).filter_by(voicebox_generation_id=generation_id).first()
    if record and record.title:
        safe_title = re.sub(r'[^\w\u4e00-\u9fff\-_. ]', '', record.title).strip()[:100]
        if safe_title:
            remote_name = safe_title

    try:
        remote_path = await asyncio.to_thread(upload_to_ftp, generation_id, remote_name)
        return {"status": "ok", "remote_path": remote_path}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


class VideoSearchRequest(BaseModel):
    title: str


VIDEO_SEARCH_URL = "http://61.153.213.238:4029/searchMahNews"


@router.post("/search-video")
async def search_video(req: VideoSearchRequest):
    try:
        resp = requests.post(
            VIDEO_SEARCH_URL,
            json={"title": req.title},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"视频搜索服务不可用: {e}")
