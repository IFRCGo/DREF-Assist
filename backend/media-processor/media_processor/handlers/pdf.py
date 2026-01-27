"""PDF file handler - text and image extraction with positional interleaving."""
import base64
import io
from dataclasses import dataclass

import fitz  # PyMuPDF

from media_processor.models import FileInput, SourceResult


@dataclass
class ContentBlock:
    """A block of content (text or image) with position."""
    page: int
    y_position: float
    content_type: str  # "text" or "image"
    text: str = ""
    image_key: str = ""


class PDFHandler:
    """Handler for PDF files."""

    MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50MB
    MAX_PAGES = 50
    MIN_CHARS_PER_PAGE = 100  # Threshold for scanned document detection

    def process(self, file_input: FileInput, source_index: int) -> SourceResult:
        """Process a PDF file.

        Pipeline:
        1. Extract text blocks with coordinates
        2. Extract embedded images with bounding boxes
        3. Sort by page and vertical position
        4. Insert [IMAGE_N] placeholders at correct positions
        5. Fallback to page rendering if text yield is low

        Args:
            file_input: The file input containing base64 data
            source_index: Index for namespacing (PDF_N_IMAGE_M)

        Returns:
            SourceResult with text and images
        """
        try:
            # Decode base64
            pdf_bytes = base64.b64decode(file_input.data)

            # Check size limit
            if len(pdf_bytes) > self.MAX_SIZE_BYTES:
                return SourceResult(
                    filename=file_input.filename,
                    source_type="pdf",
                    error=f"File exceeds size limit of 50MB",
                    images={},
                )

            # Open PDF
            try:
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            except Exception as e:
                return SourceResult(
                    filename=file_input.filename,
                    source_type="pdf",
                    error=f"Failed to parse PDF: file corrupted or invalid",
                    images={},
                )

            try:
                # Check page limit
                if len(doc) > self.MAX_PAGES:
                    return SourceResult(
                        filename=file_input.filename,
                        source_type="pdf",
                        error=f"PDF exceeds maximum of {self.MAX_PAGES} pages",
                        images={},
                    )

                # Check if scanned document
                total_text = ""
                for page in doc:
                    total_text += page.get_text()

                avg_chars_per_page = len(total_text) / max(len(doc), 1)

                if avg_chars_per_page < self.MIN_CHARS_PER_PAGE:
                    # Scanned document - render pages as images
                    return self._process_scanned(doc, file_input.filename, source_index)

                # Normal PDF - extract text and images
                return self._process_normal(doc, file_input.filename, source_index)

            finally:
                doc.close()

        except Exception as e:
            return SourceResult(
                filename=file_input.filename,
                source_type="pdf",
                error=f"Failed to process PDF: {str(e)}",
                images={},
            )

    def _process_normal(
        self, doc: fitz.Document, filename: str, source_index: int
    ) -> SourceResult:
        """Process a normal (text-based) PDF."""
        content_blocks: list[ContentBlock] = []
        images: dict[str, str] = {}
        image_counter = 0

        for page_num, page in enumerate(doc):
            page_height = page.rect.height

            # Extract text blocks
            text_blocks = page.get_text_blocks()
            for block in text_blocks:
                # block: (x0, y0, x1, y1, text, block_no, block_type)
                if len(block) >= 5 and block[4].strip():
                    content_blocks.append(ContentBlock(
                        page=page_num,
                        y_position=block[1],  # y0
                        content_type="text",
                        text=block[4].strip(),
                    ))

            # Extract images
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                try:
                    # Get image position
                    rects = page.get_image_rects(xref)
                    y_pos = rects[0].y0 if rects else page_height / 2

                    # Extract image data
                    img_data = doc.extract_image(xref)
                    if img_data:
                        image_counter += 1
                        image_key = f"PDF_{source_index}_IMAGE_{image_counter}"
                        images[image_key] = base64.b64encode(img_data["image"]).decode()

                        content_blocks.append(ContentBlock(
                            page=page_num,
                            y_position=y_pos,
                            content_type="image",
                            image_key=image_key,
                        ))
                except Exception:
                    continue  # Skip problematic images

        # Sort by page, then y position
        content_blocks.sort(key=lambda b: (b.page, b.y_position))

        # Build text with placeholders
        text_parts = []
        for block in content_blocks:
            if block.content_type == "text":
                text_parts.append(block.text)
            else:
                text_parts.append(f"[{block.image_key}]")

        text_content = "\n\n".join(text_parts)

        return SourceResult(
            filename=filename,
            source_type="pdf",
            text_content=text_content,
            images=images,
            processing_notes=f"Extracted {image_counter} embedded images" if image_counter else None,
        )

    def _process_scanned(
        self, doc: fitz.Document, filename: str, source_index: int
    ) -> SourceResult:
        """Process a scanned PDF by rendering pages as images."""
        images: dict[str, str] = {}
        text_parts = []

        for page_num, page in enumerate(doc):
            # Render page at reasonable resolution
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for readability
            pixmap = page.get_pixmap(matrix=mat)

            image_key = f"PDF_{source_index}_IMAGE_{page_num + 1}"
            images[image_key] = base64.b64encode(pixmap.tobytes("png")).decode()
            text_parts.append(f"[{image_key}]")

        text_content = "\n\n".join(text_parts)

        return SourceResult(
            filename=filename,
            source_type="pdf",
            text_content=text_content,
            images=images,
            processing_notes=f"Scanned document: rendered {len(doc)} pages as images",
        )
