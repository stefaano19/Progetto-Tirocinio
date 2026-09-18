from pathlib import Path
from typing import List, Dict, Any, Tuple

from utils.markdown_parser import parse_index, parse_frontmatter, ParsedIndex
from utils.file_utils import atomic_copy

SUPPORTED_EXTENSIONS = [".pdf", ".md", ".txt", ".rst", ".docx"]

class WikiModel:
    """Logic for Knowledge Base management.
    Stateless operations as per project guidelines.
    """
    
    def parse_index(self, workspace_path: str) -> ParsedIndex | None:
        """Reads and parses the workspace index.md file."""
        index_path = Path(workspace_path) / "knowledge-base" / "index.md"
        if not index_path.exists():
            return None
            
        try:
            content = index_path.read_text(encoding="utf-8")
            return parse_index(content)
        except Exception:
            return None

    def list_pages(self, workspace_path: str) -> List[str]:
        """Lists all Markdown files in the knowledge-base folders."""
        kb_path = Path(workspace_path) / "knowledge-base"
        if not kb_path.exists():
            return []
            
        pages = []
        for file_path in kb_path.rglob("*.md"):
            # Exclude special files like index.md and log.md or system folders
            if file_path.name in ("index.md", "log.md") or ".agents" in file_path.parts:
                continue
            
            # Relative path from the knowledge-base folder
            rel_path = file_path.relative_to(kb_path)
            pages.append(str(rel_path))
            
        return sorted(pages)

    def read_page(self, workspace_path: str, page_rel_path: str) -> str:
        """Reads the full content of a page."""
        page_path = Path(workspace_path) / "knowledge-base" / page_rel_path
        if not page_path.exists():
            raise FileNotFoundError(f"Page not found: {page_rel_path}")
            
        if page_path.is_dir():
            # If a directory is linked, try to load its index.md
            index_file = page_path / "index.md"
            if index_file.exists():
                return index_file.read_text(encoding="utf-8")
            else:
                return f"# Directory: {page_rel_path}\n\nThis is a directory, not a markdown file. It contains no `index.md`."
            
        return page_path.read_text(encoding="utf-8")

    def get_page_frontmatter(self, workspace_path: str, page_rel_path: str) -> Dict[str, Any]:
        """Extracts only the YAML frontmatter of a page."""
        try:
            content = self.read_page(workspace_path, page_rel_path)
            frontmatter, _ = parse_frontmatter(content)
            return frontmatter
        except FileNotFoundError:
            return {}

    def import_document(self, workspace_path: str, source_path: str) -> str:
        """Imports a raw document into the raw/ folder of the Knowledge Base.
        Only supports extensions in SUPPORTED_EXTENSIONS.
        """
        src = Path(source_path)
        if not src.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
            
        if src.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported extension: {src.suffix}")
            
        raw_dir = Path(workspace_path) / "knowledge-base" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        dst = raw_dir / src.name
        
        # If the file already exists, avoid conflicts or use atomic_copy
        # For now we use atomic_copy which will overwrite if it exists
        atomic_copy(src, dst)
        
        return str(dst)
