import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse

from config import VOICEBOX_DATA_DIR
from utils.speed_effects import get_speed_range, stream_speed_from_file

router = APIRouter(prefix="/audio", tags=["audio"])


@router.get("/clip/{clip_id}")
async def serve_clip(clip_id: str, download: bool = Query(False)):
    """播放/下载同期声裁剪音频片段。

    - clip_id: 片段唯一标识
    - download: 设为 true 触发浏览器下载，否则内联播放
    """
    clips_dir = Path(
        os.getenv("VOICEBOX_DATA_DIR", os.path.expanduser("~/Documents/GitHub/voicebox/data"))
    ) / "clips"
    for ext in (".wav", ".mp3"):
        clip_path = clips_dir / f"{clip_id}{ext}"
        if clip_path.exists():
            break
    else:
        raise HTTPException(status_code=404, detail="Clip not found")

    is_mp3 = clip_path.suffix == ".mp3"
    headers = {"Cache-Control": "public, max-age=86400"}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="clip_{clip_id}{clip_path.suffix}"'
    else:
        headers["Content-Disposition"] = "inline"

    return FileResponse(
        clip_path,
        media_type="audio/mpeg" if is_mp3 else "audio/wav",
        headers=headers,
    )


@router.get("/{generation_id}")
async def serve_audio(generation_id: str):
    for ext in (".mp3", ".wav"):
        filepath = Path(VOICEBOX_DATA_DIR) / "generations" / f"{generation_id}{ext}"
        if filepath.exists():
            return FileResponse(
                filepath,
                media_type="audio/mpeg" if ext == ".mp3" else "audio/wav",
                headers={"Cache-Control": "public, max-age=86400"},
            )
    raise HTTPException(status_code=404, detail="Audio not found")


@router.get("/download/{generation_id}")
async def download_audio(
    generation_id: str,
    speed: float = Query(1.0, ge=0.25, le=4.0, description="Speed multiplier (0.5=half, 2.0=double)"),
):
    source_file = Path(VOICEBOX_DATA_DIR) / "generations" / f"{generation_id}.mp3"
    if not source_file.exists():
        source_file = Path(VOICEBOX_DATA_DIR) / "generations" / f"{generation_id}.wav"
    if not source_file.exists():
        raise HTTPException(status_code=404, detail="Source audio not found")

    is_mp3 = source_file.suffix == ".mp3"

    if speed == 1.0:
        return FileResponse(
            source_file,
            media_type="audio/mpeg" if is_mp3 else "audio/wav",
            headers={"Cache-Control": "public, max-age=3600"},
        )

    try:
        proc = stream_speed_from_file(source_file, speed)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return StreamingResponse(
        proc.stdout,
        media_type="audio/wav",
        headers={
            "Content-Disposition": f'inline; filename="{generation_id}.wav"',
        },
    )


@router.get("/speed-range")
def speed_range():
    return get_speed_range()
