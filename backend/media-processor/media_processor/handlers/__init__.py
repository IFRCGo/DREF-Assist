"""File type handlers."""
from media_processor.handlers.image import ImageHandler
from media_processor.handlers.audio import AudioHandler
from media_processor.handlers.video import VideoHandler
from media_processor.handlers.pdf import PDFHandler
from media_processor.handlers.docx import DOCXHandler

__all__ = ["ImageHandler", "AudioHandler", "VideoHandler", "PDFHandler", "DOCXHandler"]
