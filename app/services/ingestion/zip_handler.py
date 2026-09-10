from pathlib import Path
from zipfile import ZipFile, BadZipFile

def extract_zip(zip_path: Path, extract_dir: Path) -> list[Path]:
    """Safely extracts the ZIP file and returns the paths of extracted files."""

    try:
        with ZipFile(zip_path, "r") as zip_file:
            members = zip_file.infolist()

            for member in members:
                member_path = Path(member.filename)

                """Prevents files from being extracted outside the target directory."""
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise ValueError(
                        f"Unsafe file path detected: {member.filename}"
                    )

            zip_file.extractall(extract_dir)

            return [
                    extract_dir / member.filename for member in zip_file.infolist() if not member.is_dir()
            ]
        
    except BadZipFile:
        raise ValueError("Invalid or corrupted ZIP file.")