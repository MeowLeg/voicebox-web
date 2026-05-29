import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from config import TTS_BACKEND_URL

router = APIRouter(prefix="/proxy")


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_voicebox(request: Request, path: str):
    url = f"{TTS_BACKEND_URL}/{path}"
    if request.query_params:
        url += f"?{request.query_params}"

    body = await request.body() if request.method in ("POST", "PUT", "PATCH") else None

    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers={k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")},
            data=body,
            stream=True,
            timeout=300,
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Voicebox unreachable: {e}")

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text[:500])

    return StreamingResponse(
        resp.iter_content(chunk_size=65536),
        status_code=resp.status_code,
        headers={k: v for k, v in resp.headers.items() if k.lower() not in ("content-encoding", "transfer-encoding", "connection")},
    )
