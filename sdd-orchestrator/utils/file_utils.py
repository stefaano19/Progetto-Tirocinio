import os
import shutil
import tempfile
from pathlib import Path

def safe_write(file_path: str | Path, content: str, encoding: str = "utf-8") -> None:
    """Writes to file atomically using a temporary file."""
    path = Path(file_path)
    # Ensure parent folder exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a temporary file in the same directory
    fd, temp_path = tempfile.mkstemp(dir=path.parent, prefix="._tmp_")
    
    try:
        with os.fdopen(fd, 'w', encoding=encoding) as f:
            f.write(content)
        # Atomic rename
        os.replace(temp_path, path)
    except Exception as e:
        # Clean up temporary file on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

def backup_file(file_path: str | Path) -> Path | None:
    """Creates a file backup by adding the .bak extension."""
    path = Path(file_path)
    if not path.exists():
        return None
        
    backup_path = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup_path)
    return backup_path

def atomic_copy(src: str | Path, dst: str | Path) -> None:
    """Atomically copies a file to the destination."""
    src_path = Path(src)
    dst_path = Path(dst)
    
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    
    fd, temp_path = tempfile.mkstemp(dir=dst_path.parent, prefix="._tmp_")
    os.close(fd)
    
    try:
        shutil.copy2(src_path, temp_path)
        os.replace(temp_path, dst_path)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e
