"""LLM output formatter - transforms processor output to GPT-4o message format."""
import re
from typing import Any

from media_processor.models import ProcessingResult, SourceResult


def format_for_llm(result: ProcessingResult, user_message: str) -> dict[str, Any]:
    """Transform processor output into GPT-4o compatible message structure.

    Args:
        result: ProcessingResult from media processor
        user_message: User's original text message

    Returns:
        GPT-4o message dict with role and content array
    """
    content: list[dict[str, Any]] = []

    # Build text content
    text_parts = []

    if user_message:
        text_parts.append(user_message)

    # Collect all images for ordering
    all_images: dict[str, str] = {}
    image_order: list[str] = []

    for source in result.sources:
        # Skip failed sources
        if source.error is not None:
            continue

        text_parts.append("---")
        text_parts.append(f"[SOURCE: {source.filename}]")

        if source.text_content:
            text_parts.append(source.text_content)

            # Extract placeholders in order of appearance
            placeholders = re.findall(r'\[([A-Z]+_\d+_(?:IMAGE|FRAME)_\d+)\]', source.text_content)
            for placeholder in placeholders:
                if placeholder in source.images and placeholder not in image_order:
                    image_order.append(placeholder)

        # Add any images not referenced in text
        for key in source.images:
            all_images[key] = source.images[key]
            if key not in image_order:
                image_order.append(key)

    # Create text block
    full_text = "\n\n".join(text_parts)
    content.append({
        "type": "text",
        "text": full_text,
    })

    # Add images in order of appearance
    for image_key in image_order:
        if image_key in all_images:
            base64_data = all_images[image_key]
            # Detect format from key or default to jpeg
            img_format = "jpeg"
            if "PNG" in image_key.upper():
                img_format = "png"

            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{img_format};base64,{base64_data}"
                }
            })

    return {
        "role": "user",
        "content": content,
    }
