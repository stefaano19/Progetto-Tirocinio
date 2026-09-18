import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class WikiLink:
    title: str
    url: str
    description: str = ""

@dataclass
class WikiCategory:
    name: str
    links: List[WikiLink]

@dataclass
class ParsedIndex:
    frontmatter: Dict[str, Any]
    categories: List[WikiCategory]


def parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """Parses the YAML frontmatter at the beginning of the Markdown file."""
    frontmatter = {}
    
    # If it doesn't start with ---, there's no frontmatter
    if not content.startswith("---"):
        return frontmatter, content
        
    parts = content.split("---", 2)
    if len(parts) >= 3:
        yaml_content = parts[1].strip()
        body = parts[2].strip()
        
        # Simple line-by-line fallback parser for flat YAML
        for line in yaml_content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                frontmatter[key] = val
        return frontmatter, body
        
    return frontmatter, content

def parse_index(content: str) -> ParsedIndex:
    """Parses the index.md returning frontmatter and a tree of categories with their links."""
    frontmatter, body = parse_frontmatter(content)
    
    categories = []
    current_category: Optional[WikiCategory] = None
    
    # Regex to match lists of links: - [Title](url) — description
    # Also supports starting asterisk
    link_pattern = re.compile(r"^[-*]\s+\[(.*?)\]\((.*?)\)(?:\s*(?:—|-)\s*(.*))?$")
    
    for line in body.split("\n"):
        line = line.strip()
        
        if line.startswith("## "):
            cat_name = line[3:].strip()
            current_category = WikiCategory(name=cat_name, links=[])
            categories.append(current_category)
            continue
            
        if current_category:
            match = link_pattern.match(line)
            if match:
                title, url, description = match.groups()
                current_category.links.append(
                    WikiLink(title=title, url=url, description=description or "")
                )
                
    return ParsedIndex(frontmatter=frontmatter, categories=categories)
