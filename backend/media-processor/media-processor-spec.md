# Media Processor Architecture Specification

## Purpose

Transforms multimodal inputs (images, video, audio, PDFs, DOCX) into a standardized format consumable by GPT-4o: extracted text and/or images.

## Input/Output Contract

**Input:** Array of files, each with base64 data + file type + filename

```json
{
  "files": [
    { "data": "base64...", "type": "pdf", "filename": "situation_report.pdf" },
    { "data": "base64...", "type": "video", "filename": "field_survey.mp4" },
    { "data": "base64...", "type": "image", "filename": "damage_photo.jpg" }
  ]
}
```

**Output:** Aggregated results from all files, namespaced by source

```json
{
  "sources": [
    {
      "filename": "situation_report.pdf",
      "source_type": "pdf",
      "text_content": "...flooding in district. [PDF_1_IMAGE_1] Water level...",
      "images": {
        "PDF_1_IMAGE_1": "base64...",
        "PDF_1_IMAGE_2": "base64..."
      },
      "processing_notes": "Extracted 2 embedded images"
    },
    {
      "filename": "field_survey.mp4",
      "source_type": "video",
      "text_content": "transcript from audio...",
      "images": {
        "VIDEO_1_FRAME_1": "base64...",
        "VIDEO_1_FRAME_2": "base64..."
      },
      "processing_notes": "Selected 8 frames from 120"
    },
    {
      "filename": "damage_photo.jpg",
      "source_type": "image",
      "text_content": null,
      "images": {
        "IMAGE_1": "base64..."
      },
      "processing_notes": null
    }
  ],
  "processing_summary": {
    "total_files": 3,
    "successful": 3,
    "failed": 0
  }
}
```

**Processing:** Router iterates through each file, applies the matching pipeline, aggregates results. Files processed independently — one failure doesn't block others.

**Image namespacing:** Image keys are prefixed by source type and index (e.g., `PDF_1_IMAGE_1`, `VIDEO_2_FRAME_3`) to avoid collisions and maintain traceability.

---

## LLM Output Formatter

The Media Processor output is not directly LLM-compatible. A `format_for_llm()` function transforms processed results into the message structure expected by GPT-4o.

**Input:**
- Media Processor output (`sources` array)
- User's text message

**Output:**
```json
{
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "string"
    },
    {
      "type": "image_url",
      "image_url": { "url": "data:image/{format};base64,{encoded_data}" }
    }
  ]
}
```

**Formatting logic:**
1. Start with user's original text message
2. Append `---` separator
3. For each source, append `[SOURCE: {filename}]` header followed by `text_content`
4. Collect all images across all sources into separate `image_url` content blocks
5. Images ordered to match placeholder appearance in text (`[PDF_1_IMAGE_1]`, `[VIDEO_1_FRAME_1]`, etc.)

**Example — PDF + DOCX input:**

```json
{
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "Here's the situation report from yesterday's survey\n\n---\n\n[SOURCE: situation_report.pdf]\nSevere flooding observed in eastern district. [PDF_1_IMAGE_1] Water level reached 1.2 meters. [PDF_1_IMAGE_2] Approximately 200 households affected.\n\n---\n\n[SOURCE: damage_assessment.docx]\nEvacuation initiated at 14:00. [DOCX_1_IMAGE_1] Community center sheltered 85 families."
    },
    {
      "type": "image_url",
      "image_url": { "url": "data:image/jpeg;base64,/9j/4AAQSkZJRg..." }
    },
    {
      "type": "image_url",
      "image_url": { "url": "data:image/png;base64,iVBORw0KGgo..." }
    },
    {
      "type": "image_url",
      "image_url": { "url": "data:image/jpeg;base64,/9j/4AAQSkZJRg..." }
    }
  ]
}
```

**Note:** GPT-4o decodes base64 back to original image bytes before processing — no semantic loss from encoding.

---

## Processing Pipelines by Type

### Image
- Validate format (JPEG, PNG, WebP, GIF) and size (≤20MB)
- Pass through directly as vision input
- **Output:** `images: [original_image]`, `text_content: null`

### Video
1. **Frame extraction:** 1 frame per second (OpenCV/FFmpeg)
2. **Deduplication:** Remove near-duplicates via perceptual hashing (>90% similarity threshold)
3. **Frame selection:** `X = clamp(deduplicated_frames × 0.10, min=5, max=20)`, uniformly sampled
4. **Audio extraction:** Strip audio track, transcribe via Whisper API
5. **Output:** `images: [selected_frames]`, `text_content: transcript`

**Supported formats:** MP4, MOV, AVI | **Max size:** 100MB

### Audio
- Transcribe via Whisper API
- **Output:** `images: []`, `text_content: transcript`

**Supported formats:** MP3, WAV, M4A, OGG | **Max size:** 50MB

### PDF
1. **Text extraction:** PyMuPDF (fitz) — extract text blocks with coordinates
2. **Image extraction:** PyMuPDF — extract embedded images with bounding boxes
3. **Positional interleaving:** Sort text blocks and images by page, then vertical position. Insert `[IMAGE_N]` placeholders into text at corresponding positions
4. **Fallback:** If text yield < 100 chars/page, render pages as images (assume scanned document)
5. **Output:** `images: {IMAGE_1: ..., IMAGE_2: ...}`, `text_content: extracted_text with placeholders`

**Max size:** 50MB | **Max pages:** 50

**Limitation:** Images in margins/headers anchored to nearest preceding text block.

### DOCX
1. **Text extraction:** python-docx — iterate paragraphs and tables in document order
2. **Image extraction:** Insert `[IMAGE_N]` placeholder when `InlineShape` encountered during iteration
3. **Output:** `images: {IMAGE_1: ..., IMAGE_2: ...}`, `text_content: extracted_text with placeholders`

**Max size:** 25MB

---

## Component Structure

```
media_processor/
├── processor.py       # Main entry: iterates files, delegates to router, aggregates results
├── router.py          # Routes single file to appropriate handler by file type
├── formatter.py       # format_for_llm(): transforms output to GPT-4o message structure
├── handlers/
│   ├── image.py       # Validation + passthrough
│   ├── video.py       # Frame extraction, dedup, selection, audio
│   ├── audio.py       # Whisper transcription
│   ├── pdf.py         # Text + image extraction, fallback rendering
│   └── docx.py        # Text + image extraction
├── utils/
│   ├── perceptual_hash.py   # Image similarity detection
│   ├── frame_sampler.py     # Bounded proportional sampling
│   └── transcription.py     # Whisper API wrapper
└── models.py          # Input/output data models
```

---

## Error Handling

**Per-file isolation:** Each file processes independently. Failures are captured in the file's result object without blocking other files.

| Error | Behavior |
|-------|----------|
| Unsupported format | Mark file as failed, list supported formats in error |
| File exceeds size limit | Mark file as failed with limit in error |
| Corrupted file | Mark file as failed, log for debugging |
| Whisper timeout/failure | Return partial result with warning, include frames without transcript |
| PDF text extraction fails | Fall back to page rendering |

**Failed file output:**
```json
{
  "filename": "corrupted.pdf",
  "source_type": "pdf",
  "error": "Failed to parse PDF: file corrupted",
  "text_content": null,
  "images": {}
}
```

---

## Technology

- **Video/Frame processing:** OpenCV, FFmpeg
- **Audio transcription:** OpenAI Whisper API
- **PDF processing:** PyMuPDF (fitz)
- **DOCX processing:** python-docx
- **Image hashing:** imagehash (perceptual)
- **Image handling:** Pillow
