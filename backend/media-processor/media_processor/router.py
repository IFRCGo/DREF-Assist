"""Routes files to appropriate handlers based on type."""
from media_processor.models import FileInput, FileType, SourceResult
from media_processor.handlers import (
    ImageHandler,
    AudioHandler,
    VideoHandler,
    PDFHandler,
    DOCXHandler,
)


class Router:
    """Routes files to the appropriate handler based on file type."""

    def __init__(self):
        self._handlers = {
            FileType.IMAGE: ImageHandler(),
            FileType.AUDIO: AudioHandler(),
            FileType.VIDEO: VideoHandler(),
            FileType.PDF: PDFHandler(),
            FileType.DOCX: DOCXHandler(),
        }

    def route(self, file_input: FileInput, source_index: int) -> SourceResult:
        """Route a file to its handler.

        Args:
            file_input: The file to process
            source_index: Index for namespacing

        Returns:
            SourceResult from the appropriate handler
        """
        handler = self._handlers.get(file_input.type)

        if handler is None:
            return SourceResult(
                filename=file_input.filename,
                source_type=file_input.type.value,
                error=f"No handler available for file type: {file_input.type.value}",
                images={},
            )

        return handler.process(file_input, source_index)
