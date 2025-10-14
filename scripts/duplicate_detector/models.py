"""
Data models for the duplicate logic detector.

This module contains the core data structures used throughout the duplicate detection process.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class CodeFunction:
    """Represents a function extracted from Python code."""

    name: str
    file_path: str
    line_start: int
    line_end: int
    signature: str
    body_content: str

    def __post_init__(self):
        """Validate the function data after initialization."""
        if not self.name:
            raise ValueError("Function name cannot be empty")
        if not self.file_path:
            raise ValueError("File path cannot be empty")
        if self.line_start <= 0:
            raise ValueError("Line start must be positive")
        if self.line_end < self.line_start:
            raise ValueError("Line end must be >= line start")

    @property
    def line_count(self) -> int:
        """Get the number of lines in the function."""
        return self.line_end - self.line_start + 1

    @property
    def is_small_function(self) -> bool:
        """Check if this is a small function (< 5 lines)."""
        return self.line_count < 5

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "signature": self.signature,
            "body_content": self.body_content,
            "line_count": self.line_count,
        }


@dataclass
class DuplicateMatch:
    """Represents a potential duplicate logic match between two functions."""

    new_function: CodeFunction
    existing_function: CodeFunction
    similarity_score: float

    def __post_init__(self):
        """Validate the match data after initialization."""
        if not isinstance(self.new_function, CodeFunction):
            raise TypeError("new_function must be a CodeFunction instance")
        if not isinstance(self.existing_function, CodeFunction):
            raise TypeError("existing_function must be a CodeFunction instance")
        if not (0.0 <= self.similarity_score <= 1.0):
            raise ValueError("Similarity score must be between 0.0 and 1.0")

    @property
    def confidence_level(self) -> str:
        """Get a human-readable confidence level."""
        if self.similarity_score >= 0.8:
            return "High"
        elif self.similarity_score >= 0.6:
            return "Medium"
        elif self.similarity_score >= 0.4:
            return "Low"
        else:
            return "Very Low"

    @property
    def is_high_confidence(self) -> bool:
        """Check if this is a high-confidence match."""
        return self.similarity_score >= 0.8

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "new_function": self.new_function.to_dict(),
            "existing_function": self.existing_function.to_dict(),
            "similarity_score": self.similarity_score,
            "confidence_level": self.confidence_level,
        }
