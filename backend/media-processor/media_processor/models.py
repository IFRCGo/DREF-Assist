"""Data models for media processor input/output contracts."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field


class FileType(str, Enum):
    """Supported file types for processing."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    PDF = "pdf"
    DOCX = "docx"


class FileInput(BaseModel):
    """Single file input for processing."""
    data: str = Field(..., description="Base64-encoded file data")
    type: FileType = Field(..., description="File type")
    filename: str = Field(..., description="Original filename")


class ProcessingInput(BaseModel):
    """Input contract for media processor."""
    files: list[FileInput] = Field(default_factory=list)


class SourceResult(BaseModel):
    """Result from processing a single source file."""
    filename: str
    source_type: str
    text_content: Optional[str] = None
    images: dict[str, str] = Field(default_factory=dict)
    processing_notes: Optional[str] = None
    error: Optional[str] = None


class ProcessingSummary(BaseModel):
    """Summary statistics for processing run."""
    total_files: int
    successful: int
    failed: int


class ProcessingResult(BaseModel):
    """Output contract for media processor."""
    sources: list[SourceResult] = Field(default_factory=list)

    @computed_field
    @property
    def processing_summary(self) -> ProcessingSummary:
        """Compute processing summary from sources."""
        total = len(self.sources)
        failed = sum(1 for s in self.sources if s.error is not None)
        return ProcessingSummary(
            total_files=total,
            successful=total - failed,
            failed=failed,
        )
