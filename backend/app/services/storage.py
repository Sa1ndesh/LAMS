import os
import uuid
import logging
from typing import Tuple

from fastapi import HTTPException, status, UploadFile

logger = logging.getLogger("lams.storage")

# ============================================================
# ROOT STORAGE DIRECTORY
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

STORAGE_ROOT = os.environ.get(
    "LAMS_STORAGE_PATH",
    os.path.join(BASE_DIR, "storage")
)

# ============================================================
# SECURITY CONSTANTS
# ============================================================

# Maximum file size: 10 MB
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".png",
    ".jpg",
    ".jpeg",
}

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/png",
    "image/jpeg",
    "image/jpg",
}

# ============================================================
# DOCUMENT CATEGORY → STORAGE FOLDER
# ============================================================

CATEGORY_FOLDER_MAP = {
    "PROPOSAL": "proposal",
    "LAND_RECORDS": "land-records",
    "SURVEY": "survey",
    "NOTIFICATIONS": "notifications",
    "AWARD": "award",
    "COMPENSATION": "compensation",
    "RR": "rr",
}


# ============================================================
# CATEGORY HELPER
# ============================================================

def get_category_folder(category_str: str) -> str:
    """
    Converts a document category into a safe storage folder name.
    """

    cat_upper = category_str.upper()

    return CATEGORY_FOLDER_MAP.get(
        cat_upper,
        "general"
    )


# ============================================================
# FILE VALIDATION
# ============================================================

def validate_file(
    file: UploadFile,
    contents: bytes
) -> None:
    """
    Validates uploaded document.

    Checks:
    1. File size
    2. Empty file
    3. File extension
    4. MIME type
    """

    # --------------------------------------------------------
    # 1. FILE SIZE VALIDATION
    # --------------------------------------------------------

    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=(
                "File size exceeds maximum limit of 10 MB "
                f"({len(contents) / (1024 * 1024):.2f} MB uploaded)."
            ),
        )

    # --------------------------------------------------------
    # 2. EMPTY FILE VALIDATION
    # --------------------------------------------------------

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content cannot be empty (0 bytes).",
        )

    # --------------------------------------------------------
    # 3. EXTENSION VALIDATION
    # --------------------------------------------------------

    filename = file.filename or "file"

    _, ext = os.path.splitext(
        filename.lower()
    )

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File extension '{ext}' is not allowed. "
                "Supported formats: PDF, DOC, DOCX, PNG, JPG, JPEG."
            ),
        )

    # --------------------------------------------------------
    # 4. MIME TYPE VALIDATION
    # --------------------------------------------------------

    content_type = (
        file.content_type or ""
    ).lower()

    if content_type and content_type not in ALLOWED_MIME_TYPES:

        # Allow generic browser/application uploads
        # when the extension is explicitly allowed.
        if not (
            content_type == "application/octet-stream"
            and ext in ALLOWED_EXTENSIONS
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"File MIME type '{content_type}' "
                    "is not supported."
                ),
            )


# ============================================================
# SAVE UPLOADED FILE
# ============================================================

def save_uploaded_file(
    project_id: str,
    category: str,
    file: UploadFile,
    contents: bytes,
    storage_root: str = STORAGE_ROOT,
) -> Tuple[str, str, str, int]:
    """
    Saves uploaded file securely.

    Storage structure:

    storage/
        projects/
            {project_id}/
                {category}/
                    {uuid}.{extension}

    Returns:

    (
        stored_file_name,
        full_file_path,
        extension,
        file_size
    )
    """

    # --------------------------------------------------------
    # Validate file first
    # --------------------------------------------------------

    validate_file(
        file,
        contents
    )

    # --------------------------------------------------------
    # Determine category folder
    # --------------------------------------------------------

    category_folder = get_category_folder(
        category
    )

    # --------------------------------------------------------
    # Build target directory
    # --------------------------------------------------------

    target_dir = os.path.join(
        storage_root,
        "projects",
        project_id,
        category_folder,
    )

    os.makedirs(
        target_dir,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Get safe extension
    # --------------------------------------------------------

    original_filename = (
        file.filename or "document.pdf"
    )

    _, ext = os.path.splitext(
        original_filename.lower()
    )

    if not ext:
        ext = ".pdf"

    # --------------------------------------------------------
    # Generate UUID filename
    # --------------------------------------------------------

    stored_file_name = (
        f"{uuid.uuid4().hex}{ext}"
    )

    full_file_path = os.path.abspath(
        os.path.join(
            target_dir,
            stored_file_name
        )
    )

    # ========================================================
    # PATH TRAVERSAL PROTECTION
    # ========================================================

    abs_storage_root = os.path.abspath(
        storage_root
    )

    # Use commonpath instead of simple startswith.
    # This prevents paths such as:
    #
    # C:\storage
    # C:\storage-malicious
    #
    # from incorrectly passing validation.

    try:
        common_path = os.path.commonpath(
            [
                abs_storage_root,
                full_file_path
            ]
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path detected.",
        )

    if common_path != abs_storage_root:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid file path detected "
                "(path traversal protection)."
            ),
        )

    # ========================================================
    # WRITE FILE
    # ========================================================

    try:
        with open(
            full_file_path,
            "wb"
        ) as f:
            f.write(contents)

    except OSError as exc:
        logger.exception(
            "Failed to store uploaded file."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to store uploaded file.",
        ) from exc

    # --------------------------------------------------------
    # File size
    # --------------------------------------------------------

    file_size = len(contents)

    logger.info(
        "File stored securely: %s (%d bytes)",
        full_file_path,
        file_size,
    )

    return (
        stored_file_name,
        full_file_path,
        ext,
        file_size,
    )


# ============================================================
# DELETE PHYSICAL FILE
# ============================================================

def delete_physical_file(
    file_path: str
) -> None:
    """
    Safely deletes a physical document file.
    """

    if not file_path:
        return

    abs_path = os.path.abspath(
        file_path
    )

    if not os.path.exists(abs_path):
        logger.warning(
            "File does not exist during deletion: %s",
            abs_path,
        )
        return

    try:
        os.remove(
            abs_path
        )

        logger.info(
            "Deleted physical file: %s",
            abs_path,
        )

    except OSError as exc:
        logger.error(
            "Failed to delete file %s: %s",
            abs_path,
            exc,
        )