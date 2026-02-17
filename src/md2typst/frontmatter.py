"""YAML front matter extraction utilities.

This module provides functions to extract YAML front matter from markdown text.
Front matter is a block of YAML at the beginning of a file, delimited by `---`.
"""

from __future__ import annotations

import re
from typing import Any

import yaml


def extract_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Extract YAML front matter from markdown text.

    Front matter must be at the very beginning of the file, starting with `---`
    on its own line, followed by YAML content, and ending with `---` on its own line.

    Args:
        text: The markdown text, potentially with front matter.

    Returns:
        Tuple of (metadata_dict, remaining_markdown).
        If no front matter is found or parsing fails, returns ({}, original_text).

    Examples:
        >>> text = '''---
        ... title: My Document
        ... author: John Doe
        ... ---
        ...
        ... # Content here
        ... '''
        >>> metadata, content = extract_frontmatter(text)
        >>> metadata['title']
        'My Document'
    """
    # Pattern: starts with ---, optional YAML content, ends with ---
    # Must be at the very beginning of the file
    # The content between --- can be empty or have content
    pattern = r"^---[ \t]*\r?\n(.*?)^---[ \t]*\r?\n"
    match = re.match(pattern, text, re.DOTALL | re.MULTILINE)

    if not match:
        return {}, text

    yaml_content = match.group(1)

    try:
        metadata = yaml.safe_load(yaml_content)
        # Handle empty YAML or non-dict results
        if not isinstance(metadata, dict):
            metadata = {}
    except yaml.YAMLError:
        # If YAML parsing fails, treat as no front matter
        return {}, text

    remaining = text[match.end() :]
    return metadata, remaining
