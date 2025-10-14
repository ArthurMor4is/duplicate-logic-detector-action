"""
Similarity analysis module for detecting duplicate logic.

This module provides different algorithms for calculating similarity between code functions.
Based on experimental results from the research phase.
"""

import re
from abc import ABC, abstractmethod
from difflib import SequenceMatcher
from typing import Dict, Type

from .models import CodeFunction


class SimilarityCalculator(ABC):
    """Abstract base class for similarity calculation methods."""

    @abstractmethod
    def calculate(self, func1: CodeFunction, func2: CodeFunction) -> float:
        """
        Calculate similarity between two functions.
        
        Args:
            func1: First function to compare
            func2: Second function to compare
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this similarity method."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Get a description of this similarity method."""
        pass


class JaccardTokensSimilarity(SimilarityCalculator):
    """
    Jaccard similarity based on code tokens.
    
    Fast and reliable method that tokenizes code and computes Jaccard coefficient.
    Best for: General purpose, balanced speed/accuracy.
    """

    def __init__(self):
        self._token_re = re.compile(
            r"[A-Za-z_]\w*|\d+|==|!=|<=|>=|[\(\)\[\]\{\}\.,:;\+\-\*/%<>]"
        )

    @property
    def name(self) -> str:
        return "jaccard_tokens"

    @property
    def description(self) -> str:
        return "Token-based Jaccard similarity coefficient"

    def calculate(self, func1: CodeFunction, func2: CodeFunction) -> float:
        """Calculate Jaccard similarity based on code tokens."""
        tokens_a = set(self._token_re.findall(func1.body_content))
        tokens_b = set(self._token_re.findall(func2.body_content))

        if not tokens_a and not tokens_b:
            return 1.0

        intersection = len(tokens_a & tokens_b)
        union = len(tokens_a | tokens_b)

        return intersection / max(1, union)


class SequenceMatcherSimilarity(SimilarityCalculator):
    """
    Similarity using Python's difflib.SequenceMatcher.
    
    Balanced approach that considers sequence similarity.
    Best for: Structural similarity detection.
    """

    @property
    def name(self) -> str:
        return "sequence_matcher"

    @property
    def description(self) -> str:
        return "Python's difflib.SequenceMatcher algorithm"

    def calculate(self, func1: CodeFunction, func2: CodeFunction) -> float:
        """Calculate similarity using SequenceMatcher."""
        return SequenceMatcher(
            None, func1.body_content, func2.body_content
        ).ratio()


class LevenshteinNormSimilarity(SimilarityCalculator):
    """
    Normalized Levenshtein distance similarity.
    
    Most thorough analysis with highest precision.
    Best for: Catching subtle duplicates, strict duplicate detection.
    """

    @property
    def name(self) -> str:
        return "levenshtein_norm"

    @property
    def description(self) -> str:
        return "Normalized Levenshtein distance"

    def calculate(self, func1: CodeFunction, func2: CodeFunction) -> float:
        """Calculate similarity using normalized Levenshtein distance."""
        a, b = func1.body_content, func2.body_content

        if a == b:
            return 1.0

        len_a, len_b = len(a), len(b)
        if len_a == 0 or len_b == 0:
            return 0.0

        # Calculate Levenshtein distance using dynamic programming
        prev = list(range(len_b + 1))
        for i in range(1, len_a + 1):
            curr = [i] + [0] * len_b
            ca = a[i - 1]
            for j in range(1, len_b + 1):
                cb = b[j - 1]
                cost = 0 if ca == cb else 1
                curr[j] = min(
                    prev[j] + 1,       # deletion
                    curr[j - 1] + 1,   # insertion
                    prev[j - 1] + cost # substitution
                )
            prev = curr

        distance = prev[len_b]
        max_len = max(len_a, len_b)
        return 1.0 - (distance / max_len)


class SimilarityAnalyzer:
    """
    Main similarity analyzer that manages different similarity methods.
    
    This class provides a unified interface for different similarity calculation methods
    and handles method selection and validation.
    """

    # Registry of available similarity methods
    _METHODS: Dict[str, Type[SimilarityCalculator]] = {
        "jaccard_tokens": JaccardTokensSimilarity,
        "sequence_matcher": SequenceMatcherSimilarity,
        "levenshtein_norm": LevenshteinNormSimilarity,
    }

    def __init__(self, method: str = "jaccard_tokens"):
        """
        Initialize the similarity analyzer.
        
        Args:
            method: Name of the similarity method to use
            
        Raises:
            ValueError: If the specified method is not available
        """
        if method not in self._METHODS:
            available = ", ".join(self._METHODS.keys())
            raise ValueError(
                f"Unknown similarity method '{method}'. "
                f"Available methods: {available}"
            )

        self.method_name = method
        self._calculator = self._METHODS[method]()

    @classmethod
    def get_available_methods(cls) -> Dict[str, str]:
        """Get a dictionary of available methods and their descriptions."""
        methods = {}
        for name, calculator_class in cls._METHODS.items():
            # Create a temporary instance to get the description
            temp_calc = calculator_class()
            methods[name] = temp_calc.description
        return methods

    @property
    def current_method(self) -> str:
        """Get the name of the currently selected method."""
        return self.method_name

    @property
    def current_method_description(self) -> str:
        """Get the description of the currently selected method."""
        return self._calculator.description

    def calculate_similarity(self, func1: CodeFunction, func2: CodeFunction) -> float:
        """
        Calculate similarity between two functions.
        
        Args:
            func1: First function to compare
            func2: Second function to compare
            
        Returns:
            Similarity score between 0.0 and 1.0
            
        Raises:
            TypeError: If the inputs are not CodeFunction instances
        """
        if not isinstance(func1, CodeFunction):
            raise TypeError("func1 must be a CodeFunction instance")
        if not isinstance(func2, CodeFunction):
            raise TypeError("func2 must be a CodeFunction instance")

        return self._calculator.calculate(func1, func2)
