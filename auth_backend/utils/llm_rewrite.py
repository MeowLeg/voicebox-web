import base64
import logging
from pathlib import Path

from openai import OpenAI

from config import OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        key = OPENAI_API_KEY or "no-auth"
        _client = OpenAI(base_url=OPENAI_BASE_URL, api_key=key)
    return _client


REWRITE_PROMPT = """你是一个专业的新闻编辑。请将以下文本整理改写成一篇连贯、通顺的新闻文章。

要求：
1. 修正错别字和语法错误
2. 去除重复的内容
3. 按照新闻写作规范组织段落结构
4. 为文章添加一个简洁的标题（用【标题】标注）
5. 保持原文的核心信息和数据不变
6. 语言风格：专业、客观、简洁

原始文字内容：
{ocr_text}

请输出改写后的文章："""

VISION_EXTRACT_PROMPT = """请仔细识别图片中的所有文字内容，完整输出。

要求：
1. 不要遗漏任何文字，包括标题、正文、图片说明、页码等
2. 保持原文的段落结构
3. 如果图片中有表格，请用文字描述表格内容
4. 直接输出文字，不要添加你的解释"""

VISION_EXTRACT_AND_REWRITE_PROMPT = """你是一个专业的新闻编辑。请仔细识别这些图片中的所有文字内容，然后整理改写成一篇连贯、通顺的新闻文章。

重要原则：不要缩减内容，尽量保留原文的所有信息量，只做必要的修正和润色。

要求：
1. 完整识别图片中的所有文字，包括标题、正文、图片说明等，不要遗漏任何内容
2. 仅修正明显的错别字和语法错误，不要改变原意
3. 仅去除完全重复的段落，不要删减信息
4. 按照新闻写作规范组织段落结构
5. 为文章添加一个简洁的标题（用【标题】标注）
6. 保持原文的所有核心信息、数据和引述不变
7. 语言风格：专业、客观、流畅
8. 改写后的文章长度应与原文相近，不要大幅缩短"""


def _image_to_base64(image_path: str | Path) -> str:
    path = Path(image_path)
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def extract_and_rewrite_from_images(image_paths: list[str | Path]) -> str:
    """Use vision LLM to extract text from images and rewrite as article.

    Args:
        image_paths: List of image file paths.

    Returns:
        Rewritten article text.
    """
    client = _get_client()

    content: list[dict] = [
        {"type": "text", "text": VISION_EXTRACT_AND_REWRITE_PROMPT},
    ]

    for path in image_paths:
        ext = Path(path).suffix.lower()
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(ext, "image/png")
        data_url = f"data:{mime};base64,{_image_to_base64(path)}"
        content.append({"type": "image_url", "image_url": {"url": data_url}})

    logger.info(f"Vision LLM: {len(image_paths)} images → {OPENAI_MODEL}")

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": content}],
        temperature=0.7,
        max_tokens=4096,
    )

    result = resp.choices[0].message.content or ""
    logger.info(f"Vision LLM done: {len(result)} chars")
    return result


def rewrite_article(ocr_text: str) -> str:
    """Rewrite raw OCR text into a coherent article using LLM."""
    prompt = REWRITE_PROMPT.format(ocr_text=ocr_text)
    client = _get_client()
    logger.info(f"LLM rewrite: {len(ocr_text)} chars → {OPENAI_MODEL}")

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=4096,
    )

    result = resp.choices[0].message.content or ""
    logger.info(f"LLM rewrite done: {len(result)} chars")
    return result
