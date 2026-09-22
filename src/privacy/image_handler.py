"""
MedGuard - In-Memory Image Handler & Privacy Safeguard
Ensures that uploaded or camera-captured images remain strictly in volatile RAM.
Images are never persisted to disk, temporary files, databases, or logs.
"""
import io
from dataclasses import dataclass
from typing import Optional, Union
from PIL import Image

PRIVACY_STATEMENT = "Your image is processed locally and is not uploaded to a server."


@dataclass
class ImageBuffer:
    """
    Ephemeral in-memory image container.
    Guarantees no file system persistence and exposes an explicit release method.
    """
    image: Image.Image
    format: str
    size: tuple[int, int]
    _cleared: bool = False

    def release(self) -> None:
        """Explicitly close and release the image from memory."""
        if not self._cleared and self.image is not None:
            try:
                self.image.close()
            except Exception:
                pass
            self.image = None
            self._cleared = True

    @property
    def is_released(self) -> bool:
        return self._cleared


def load_image_into_memory(
    source: Union[bytes, io.BytesIO, Image.Image]
) -> tuple[Optional[ImageBuffer], Optional[str]]:
    """
    Safely loads an image into an in-memory buffer without writing to disk.

    Returns:
        tuple (ImageBuffer | None, error_message | None)
    """
    if source is None:
        return None, "No image data provided."

    try:
        if isinstance(source, Image.Image):
            # Already a PIL Image, create an in-memory copy
            img = source.copy()
            fmt = (source.format or "PNG").upper()
            return ImageBuffer(image=img, format=fmt, size=img.size), None

        if isinstance(source, io.BytesIO):
            source.seek(0)
            img = Image.open(source)
            img.load()  # Force load pixel data into memory
            fmt = (img.format or "JPEG").upper()
            return ImageBuffer(image=img.copy(), format=fmt, size=img.size), None

        if isinstance(source, (bytes, bytearray)):
            if len(source) == 0:
                return None, "Provided image byte stream is empty."
            bio = io.BytesIO(source)
            img = Image.open(bio)
            img.load()
            fmt = (img.format or "JPEG").upper()
            return ImageBuffer(image=img.copy(), format=fmt, size=img.size), None

        import numpy as np
        if isinstance(source, np.ndarray):
            import cv2
            if len(source.shape) == 3 and source.shape[2] == 3:
                rgb = cv2.cvtColor(source, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
            else:
                img = Image.fromarray(source)
            return ImageBuffer(image=img, format="PNG", size=img.size), None

        return None, f"Unsupported image source type: {type(source)}"

    except Exception as e:
        return None, f"Failed to decode image in memory: {str(e)}"


def validate_image_buffer(buffer: ImageBuffer) -> tuple[bool, Optional[str]]:
    """
    Validates dimensions and state of an in-memory image buffer.
    """
    if buffer.is_released or buffer.image is None:
        return False, "Image buffer has already been released from memory."

    w, h = buffer.size
    if w <= 0 or h <= 0:
        return False, "Invalid image dimensions."

    return True, None
