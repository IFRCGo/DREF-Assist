"""
Input builders for the DREF Assist LLM test suite.

Provides five builder functions producing pre-extracted text that bypasses the
media processing pipeline. Each function documents what kind of real-world input
it mimics so tests are self-describing.

All inputs are plain strings passed directly to handle_message() as user_message.
The media processor is NOT involved — these tests isolate the LLM handler's
reasoning over text.
"""

from typing import Dict


def structured_input(text: str) -> str:
    """Clean, labelled field data as from a well-formatted situation report.

    Use for tests where input quality is not the variable being tested.
    The LLM should have no trouble parsing this format.

    Example:
        structured_input(
            "Disaster type: Flood\\n"
            "Country: Bangladesh\\n"
            "Affected population: 5,000 persons"
        )
    """
    return text


def pdf_input(filename: str, sections: Dict[str, str]) -> str:
    """Mimics text extracted from a PDF situation report.

    Adds [SOURCE: filename] markers matching the format the media-processor
    formatter produces, plus headed sections with dividers.

    Args:
        filename: The PDF filename (e.g., "situation_report.pdf")
        sections: Dict mapping section headings to body text

    Example:
        pdf_input("sitrep_march.pdf", {
            "Impact Summary": "Total affected population: 5,000 persons.",
            "Response Actions": "Red Cross deployed 50 volunteers.",
        })
    """
    lines = [f"[SOURCE: {filename}]", ""]
    for heading, body in sections.items():
        lines.append(heading.upper())
        lines.append("-" * len(heading))
        lines.append(body)
        lines.append("")
    return "\n".join(lines)


def voice_input(text: str) -> str:
    """Mimics realistic Whisper transcription output.

    The caller provides the noisy text. It should include:
    - Filler words: uh, um, like, you know, so
    - [inaudible] markers where words were lost
    - No punctuation or inconsistent punctuation
    - Run-on sentences without clear boundaries
    - Informal speech patterns

    Example:
        voice_input(
            "uh the flood hit um bangladesh and like five thousand "
            "[inaudible] people were affected and the date was um march the tenth"
        )
    """
    return text


def ocr_input(text: str) -> str:
    """Mimics realistic OCR output from a scanned/photographed document.

    The caller provides the garbled text. It should include:
    - Character confusion: 0↔O, 1↔l↔I, 5↔S, 8↔B
    - Split words mid-character
    - Inconsistent spacing
    - [illegible] markers where text could not be read
    - Missing or garbled punctuation

    Example:
        ocr_input("FIood - 4OOO fami1ies - [illegible] - March [illegible]")
    """
    return text


def unstructured_input(text: str) -> str:
    """Mimics a stream-of-consciousness message from a stressed surveyor.

    The caller provides the raw text. It should include:
    - No structure or formatting
    - Vague quantities ("many", "a lot", "some")
    - Self-corrections mid-sentence
    - Informal language, possibly non-native English patterns
    - Missing context or ambiguous references

    Example:
        unstructured_input(
            "so yeah there was this flood and like it happened last week "
            "I think... maybe 5000 or was it 7000... bangladesh I forgot "
            "to mention... need 200000 or something..."
        )
    """
    return text
