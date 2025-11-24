# =============================================================================
# FILE: file_writer_tool.py
# PURPOSE:
#   This module defines a single tool function, `write_to_file`, which saves
#   the provided content to a file with a customizable name and extension inside
#   an output directory. This is used by agents to persist any type of generated
#   content (HTML, JSON, text, CSV, etc.).
# =============================================================================

# Import the `datetime` module to generate a unique timestamp for the filename.
import datetime

# Import `Path` from `pathlib` for convenient and safe file/directory handling.
from pathlib import Path

# -----------------------------------------------------------------------------
# TOOL FUNCTION: write_to_file
# -----------------------------------------------------------------------------
def write_to_file(content: str, filename: str = None, extension: str = "txt") -> dict:
    """
    Writes the given content to a file with a specified name and extension.

    Args:
        content (str): Content to be saved to disk.
        filename (str, optional): Name for the file (without extension).
                                 If not provided, uses a timestamp.
        extension (str, optional): File extension (without the dot).
                                  Defaults to "txt".

    Returns:
        dict: A dictionary containing the status and generated file path.
    """

    # If no filename is provided, generate one using the current timestamp.
    # Example: "250611_142317"
    if filename is None:
        timestamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        filename = f"{timestamp}_generated_file"

    # Ensure the extension doesn't have a leading dot, then construct the full filename.
    extension = extension.lstrip(".")
    full_filename = f"output/{filename}.{extension}"

    # Ensure the "output" directory exists. If it doesn't, create it.
    # `exist_ok=True` prevents an error if the directory already exists.
    Path("output").mkdir(exist_ok=True)

    # Write the content to the constructed file.
    # `encoding='utf-8'` ensures proper character encoding.
    Path(full_filename).write_text(content, encoding="utf-8")

    # Return a dictionary indicating success, and the file path that was written.
    return {
        "status": "success",
        "file": full_filename
    }