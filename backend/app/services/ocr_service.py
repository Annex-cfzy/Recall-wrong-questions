"""OCR service — PaddleOCR-VL with a graceful offline fallback.

In mock mode (no PaddleOCR installed or MOCK_EXTERNAL=true) we return the
uploaded image's placeholder text so the upload → preview flow is exercisable
end to end without the multi-GB model.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import AppException

_ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
_PADDLE_AVAILABLE = None


def _paddle_available() -> bool:
    global _PADDLE_AVAILABLE
    if _PADDLE_AVAILABLE is None:
        try:
            import paddle  # noqa: F401
            import paddleocr  # noqa: F401

            _PADDLE_AVAILABLE = True
        except Exception:
            _PADDLE_AVAILABLE = False
    return _PADDLE_AVAILABLE


def validate_image(filename: str, content_type: str, size: int) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in _ALLOWED_EXT or content_type not in settings.allowed_image_types:
        raise AppException(3001, "不支持的图片格式，请上传 JPG/PNG/WEBP 格式")
    if size > settings.max_upload_size:
        raise AppException(3002, "图片过大，请压缩后上传（最大 10MB）")


async def recognize(image_bytes: bytes, filename: str) -> str:
    """Return OCR text for the given image bytes."""
    if settings.mock_external or not _paddle_available():
        # Offline placeholder: simulates OCR output so the flow is testable.
        return (
            "1. 已知函数 f(x) = x³ - 3x，求 f(x) 的极值。\n"
            "2. 计算 ∫₀¹ 2x dx 的值。\n"
            "3. 求 lim(x→0) (sin x) / x 的值。"
        )
    # Real PaddleOCR-VL path.
    from paddleocr import PaddleOCR

    import numpy as np
    from PIL import Image
    import io

    ocr = PaddleOCR(use_angle_cls=True, lang="ch")
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    arr = np.array(img)
    result = ocr.ocr(arr, cls=True)
    lines = []
    for line in result:
        for item in line:
            lines.append(item[1][0])
    return "\n".join(lines)
