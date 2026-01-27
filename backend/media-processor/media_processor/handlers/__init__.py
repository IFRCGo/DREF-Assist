"""File type handlers."""
from media_processor.handlers.image import ImageHandler
from media_processor.handlers.audio import AudioHandler
from media_processor.handlers.video import VideoHandler
from media_processor.handlers.pdf import PDFHandler

__all__ = ["ImageHandler", "AudioHandler", "VideoHandler", "PDFHandler"]
