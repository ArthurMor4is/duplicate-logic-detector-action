"""
Duplicate Logic Detector Package

A modular package for detecting duplicate logic in Python code.
"""

__version__ = "1.0.0"

# Main exports for easy importing
from .detector import DuplicateLogicDetector
from .models import CodeFunction, DuplicateMatch
from .similarity import SimilarityAnalyzer
from .extractor import PythonFunctionExtractor
from .reporters import MultiFormatReporter

__all__ = [
    "DuplicateLogicDetector",
    "CodeFunction", 
    "DuplicateMatch",
    "SimilarityAnalyzer",
    "PythonFunctionExtractor", 
    "MultiFormatReporter",
]
