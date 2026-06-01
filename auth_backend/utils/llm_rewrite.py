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


BROADCAST_REWRITE_PROMPT = """你是一个专业的新闻编辑。请将以下电视新闻稿件改写为适合语音播报的新闻稿（报纸新闻风格，直接进入正文）。

原文中用特殊标记 【同期声占位】 标注了同期声（采访原始音频）的位置。你需要：

1. 改写非同期声段落，使其更流畅紧凑，适合语音播报，禁止添加"听众朋友"、"各位听众"等广播开场词和问候语
2. 原文中的 【同期声占位】 必须原封不动地保留（包括标记本身），不要改动其前后的任何字符
3. 去掉不适合语音播报的表述（如"请看画面"、"如图"、"点击"等视觉/交互依赖用语）
4. 保持原文的核心信息和逻辑顺序，不要添加原文没有的内容
5. 直接进入正文，无需任何开场白或结尾语

原文稿件：
{manuscript}

请输出改写后的新闻稿："""


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


def rewrite_broadcast(paragraphs: list[dict]) -> list[dict]:
    """Rewrite tv news paragraphs for radio broadcast.

    Non-soundbite paragraphs are rewritten; soundbite paragraphs are preserved
    with a placeholder marker, then restored after LLM rewrite.

    Args:
        paragraphs: List of paragraph dicts with keys: text, label, asrStartTime, etc.

    Returns:
        New list of paragraph dicts with rewritten text for non-soundbite paragraphs.
    """
    PLACEHOLDER = "【同期声占位】"

    # Separate soundbite and non-soundbite paragraphs
    soundbite_texts: list[str] = []
    manuscript_parts: list[str] = []

    for p in paragraphs:
        if p.get("asrStartTime") is not None:
            soundbite_texts.append(p.get("text", ""))
            manuscript_parts.append(PLACEHOLDER)
        else:
            manuscript_parts.append(p.get("text", ""))

    # If no non-soundbite text, nothing to rewrite
    non_sb_text = "\n".join(p.get("text", "") for p in paragraphs if p.get("asrStartTime") is None)
    if not non_sb_text.strip():
        return paragraphs

    manuscript = "\n".join(manuscript_parts)
    prompt = BROADCAST_REWRITE_PROMPT.format(manuscript=manuscript)

    client = _get_client()
    logger.info(f"Broadcast rewrite: {len(manuscript)} chars → {OPENAI_MODEL}")

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=4096,
    )

    result = resp.choices[0].message.content or ""
    logger.info(f"Broadcast rewrite done: {len(result)} chars")

    # Parse result: split by placeholder
    rewritten_parts = result.split(PLACEHOLDER)

    # Rebuild paragraph list
    new_paragraphs: list[dict] = []
    sb_idx = 0
    non_sb_idx = 0

    for p in paragraphs:
        if p.get("asrStartTime") is not None:
            # Preserve original soundbite paragraph
            new_paragraphs.append(dict(p))
            sb_idx += 1
        else:
            # Replace with rewritten text
            rewritten_text = rewritten_parts[non_sb_idx].strip() if non_sb_idx < len(rewritten_parts) else p.get("text", "")
            new_p = dict(p)
            new_p["text"] = rewritten_text
            new_paragraphs.append(new_p)
            non_sb_idx += 1

    return new_paragraphs
