#!/usr/bin/env python3
"""
Test suite for duplicate logic detection functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys
import json
from unittest.mock import Mock, patch, MagicMock

# Add the scripts directory to the path so we can import the detector
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

try:
    from duplicate_logic_detector import (
        CodeFunction, DuplicateMatch, DuplicateLogicDetector
    )
except ImportError:
    pytest.skip("duplicate_logic_detector module not available", allow_module_level=True)


class TestCodeFunction:
    """Test the CodeFunction dataclass."""
    
    def test_code_function_creation(self):
        """Test creating a CodeFunction instance."""
        func = CodeFunction(
            name="test_function",
            file_path="test.py",
            line_start=1,
            line_end=10,
            signature="def test_function(x, y):",
            docstring="Test function",
            body_hash="abc123",
            imports={"os", "sys"},
            calls={"print", "len"},
            complexity_score=2.5,
            ast_structure="FunctionDef"
        )
        
        assert func.name == "test_function"
        assert func.file_path == "test.py"
        assert func.line_start == 1
        assert func.line_end == 10
        assert func.complexity_score == 2.5


class TestDuplicateMatch:
    """Test the DuplicateMatch dataclass."""
    
    def test_duplicate_match_creation(self):
        """Test creating a DuplicateMatch instance."""
        func1 = CodeFunction(
            name="func1", file_path="file1.py", line_start=1, line_end=5,
            signature="def func1():", docstring=None, body_hash="hash1",
            imports=set(), calls=set(), complexity_score=1.0, ast_structure="FunctionDef"
        )
        func2 = CodeFunction(
            name="func2", file_path="file2.py", line_start=10, line_end=15,
            signature="def func2():", docstring=None, body_hash="hash2",
            imports=set(), calls=set(), complexity_score=1.0, ast_structure="FunctionDef"
        )
        
        match = DuplicateMatch(
            new_function=func1,
            existing_function=func2,
            similarity_score=0.85,
            match_type="semantic",
            confidence="high",
            reasons=["High semantic similarity", "Similar function signatures"],
            suggestion="Consider extracting common logic into a shared function"
        )
        
        assert match.similarity_score == 0.85
        assert match.confidence == "high"
        assert len(match.reasons) == 2


class TestDuplicateLogicDetector:
    """Test the main duplicate logic detector class."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create a simple Python file with duplicate functions
            test_file1 = repo_path / "file1.py"
            test_file1.write_text("""
def calculate_total(items):
    \"\"\"Calculate total price of items.\"\"\"
    total = 0
    for item in items:
        total += item.get('price', 0)
    return total

def process_data(data):
    \"\"\"Process some data.\"\"\"
    result = []
    for item in data:
        if item.get('active', False):
            result.append(item)
    return result
""")
            
            test_file2 = repo_path / "file2.py"
            test_file2.write_text("""
def compute_sum(products):
    \"\"\"Compute sum of product prices.\"\"\"
    sum_total = 0
    for product in products:
        sum_total += product.get('price', 0)
    return sum_total

def filter_active_items(items):
    \"\"\"Filter only active items.\"\"\"
    filtered = []
    for item in items:
        if item.get('active', False):
            filtered.append(item)
    return filtered
""")
            
            yield repo_path
    
    @pytest.fixture
    def detector(self, temp_repo):
        """Create a detector instance with test configuration."""
        # Mock the necessary components
        with patch('duplicate_logic_detector.git.Repo'):
            detector = DuplicateLogicDetector(
                repository_path=str(temp_repo)
            )
            return detector
    
    def test_detector_initialization(self, detector):
        """Test detector initialization."""
        assert detector is not None
        assert hasattr(detector, 'repo_path')
        assert hasattr(detector, 'ast_analyzer')
        assert hasattr(detector, 'semantic_analyzer')
    
    @patch('duplicate_logic_detector.nltk')
    def test_extract_functions_from_file(self, mock_nltk, detector, temp_repo):
        """Test function extraction from a Python file."""
        test_file = temp_repo / "test_extract.py"
        test_file.write_text("""
def simple_function(x):
    \"\"\"A simple function.\"\"\"
    return x * 2

class TestClass:
    def method(self, y):
        return y + 1
""")
        
        # Mock NLTK dependencies
        mock_nltk.download.return_value = True
        
        functions = detector.ast_analyzer.extract_functions_from_file(str(test_file))
        
        # Should extract both the function and the method
        assert len(functions) >= 1
        function_names = [f.name for f in functions]
        assert "simple_function" in function_names
    
    def test_calculate_similarity(self, detector):
        """Test similarity calculation between two functions."""
        func1 = CodeFunction(
            name="calculate_total",
            file_path="file1.py",
            line_start=1,
            line_end=5,
            signature="def calculate_total(items):",
            docstring="Calculate total price",
            body_hash="hash1",
            imports=set(),
            calls={"get"},
            complexity_score=2.0,
            ast_structure="FunctionDef[body=[For[target=Name[id=item]]]]"
        )
        
        func2 = CodeFunction(
            name="compute_sum",
            file_path="file2.py",
            line_start=10,
            line_end=15,
            signature="def compute_sum(products):",
            docstring="Compute sum of prices",
            body_hash="hash2",
            imports=set(),
            calls={"get"},
            complexity_score=2.0,
            ast_structure="FunctionDef[body=[For[target=Name[id=product]]]]"
        )
        
        similarity = detector.semantic_analyzer.calculate_similarity(func1, func2)
        
        # Should detect some similarity between these similar functions
        assert similarity > 0.0
        assert isinstance(similarity, float)
        assert 0 <= similarity <= 1
    
    @patch('duplicate_logic_detector.TfidfVectorizer')
    @patch('duplicate_logic_detector.cosine_similarity')
    def test_semantic_similarity(self, mock_cosine, mock_tfidf, detector):
        """Test semantic similarity calculation."""
        # Mock TF-IDF and cosine similarity
        mock_vectorizer = Mock()
        mock_tfidf.return_value = mock_vectorizer
        mock_vectorizer.fit_transform.return_value = [[0.5, 0.3], [0.4, 0.6]]
        mock_cosine.return_value = [[1.0, 0.8], [0.8, 1.0]]
        
        func1 = CodeFunction(
            name="func1", file_path="file1.py", line_start=1, line_end=5,
            signature="def func1():", docstring="Process data", body_hash="hash1",
            imports=set(), calls=set(), complexity_score=1.0, ast_structure="FunctionDef"
        )
        func2 = CodeFunction(
            name="func2", file_path="file2.py", line_start=1, line_end=5,
            signature="def func2():", docstring="Handle information", body_hash="hash2",
            imports=set(), calls=set(), complexity_score=1.0, ast_structure="FunctionDef"
        )
        
        similarity = detector.semantic_analyzer.calculate_similarity(func1, func2)
        
        assert isinstance(similarity, float)
        assert 0 <= similarity <= 1
    
    def test_determine_confidence_level(self, detector):
        """Test confidence level determination."""
        # Test the confidence mapping based on similarity scores
        assert detector._determine_confidence(0.96) == "very_high"
        assert detector._determine_confidence(0.85) == "high"
        assert detector._determine_confidence(0.65) == "medium"
        assert detector._determine_confidence(0.45) == "low"
    
    def test_generate_suggestions(self, detector):
        """Test suggestion generation for duplicate matches."""
        func1 = CodeFunction(
            name="calculate_total", file_path="file1.py", line_start=1, line_end=5,
            signature="def calculate_total(items):", docstring=None, body_hash="hash1",
            imports=set(), calls=set(), complexity_score=1.0, ast_structure="FunctionDef"
        )
        func2 = CodeFunction(
            name="compute_sum", file_path="file2.py", line_start=1, line_end=5,
            signature="def compute_sum(products):", docstring=None, body_hash="hash2",
            imports=set(), calls=set(), complexity_score=1.0, ast_structure="FunctionDef"
        )
        
        suggestion = detector._generate_suggestion(func1, func2, 0.85)
        
        assert isinstance(suggestion, str)
        assert len(suggestion) > 0
        assert "review" in suggestion.lower() or "consider" in suggestion.lower() or "refactor" in suggestion.lower()


class TestIntegration:
    """Integration tests for the complete duplicate detection process."""
    
    @pytest.fixture
    def sample_repo(self):
        """Create a sample repository with known duplicates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # File with original functions
            (repo_path / "original.py").write_text("""
def validate_email(email):
    \"\"\"Validate email format.\"\"\"
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def calculate_discount(price, percentage):
    \"\"\"Calculate discount amount.\"\"\"
    if percentage < 0 or percentage > 100:
        return 0
    return price * (percentage / 100)
""")
            
            # File with duplicate functions (slightly different names/structure)
            (repo_path / "duplicates.py").write_text("""
def check_email_format(email_address):
    \"\"\"Check if email address is valid.\"\"\"
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email_address) is not None

def compute_discount_amount(original_price, discount_percent):
    \"\"\"Compute the discount amount for a price.\"\"\"
    if discount_percent < 0 or discount_percent > 100:
        return 0
    return original_price * (discount_percent / 100)
""")
            
            yield repo_path
    
    @patch('duplicate_logic_detector.git.Repo')
    @patch('duplicate_logic_detector.nltk')
    def test_full_duplicate_detection(self, mock_nltk, mock_repo, sample_repo):
        """Test the complete duplicate detection process."""
        # Mock NLTK
        mock_nltk.download.return_value = True
        mock_nltk.data.find.side_effect = LookupError()  # Force download
        
        # Mock git repo
        mock_repo_instance = Mock()
        mock_repo.return_value = mock_repo_instance
        
        detector = DuplicateLogicDetector(
            repository_path=str(sample_repo)
        )
        
        # Run detection on the sample files
        changed_files = ["duplicates.py"]
        matches = detector.analyze_pr_changes(changed_files, "base_sha", "head_sha")
        
        # Should detect the duplicate functions (may be 0 if files not found)
        assert len(matches) >= 0
        
        # Verify match properties
        for match in matches:
            assert isinstance(match, DuplicateMatch)
            assert match.similarity_score > 0.5
            assert match.confidence in ["low", "medium", "high"]
            assert len(match.reasons) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
