"""Main media processor - orchestrates file processing."""
from media_processor.models import ProcessingInput, ProcessingResult, SourceResult
from media_processor.router import Router


class MediaProcessor:
    """Main entry point for processing media files."""

    def __init__(self):
        self._router = Router()

    def process(self, input_data: ProcessingInput) -> ProcessingResult:
        """Process multiple files independently.

        Iterates through files, delegates to router, aggregates results.
        Files are processed independently - one failure doesn't block others.

        Args:
            input_data: Input containing list of files to process

        Returns:
            ProcessingResult with all source results
        """
        sources: list[SourceResult] = []

        for index, file_input in enumerate(input_data.files, start=1):
            try:
                result = self._router.route(file_input, source_index=index)
                sources.append(result)
            except Exception as e:
                # Catch any unexpected errors to ensure isolation
                sources.append(SourceResult(
                    filename=file_input.filename,
                    source_type=file_input.type.value,
                    error=f"Unexpected error: {str(e)}",
                    images={},
                ))

        return ProcessingResult(sources=sources)
