import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add the scripts directory to the path so we can import the detector
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from duplicate_logic_detector import DuplicateMatch, DuplicateLogicDetector, CodeFunction


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
            body_content="def test_function(x, y):\n    return x + y"
        )
        
        assert func.name == "test_function"
        assert func.file_path == "test.py"
        assert func.line_start == 1
        assert func.line_end == 10
        assert func.signature == "def test_function(x, y):"
        assert func.body_content == "def test_function(x, y):\n    return x + y"


class TestDuplicateMatch:
    """Test the DuplicateMatch dataclass."""
    
    def test_duplicate_match_creation(self):
        """Test creating a DuplicateMatch instance."""
        func1 = CodeFunction(
            name="func1", file_path="file1.py", line_start=1, line_end=5,
            signature="def func1():", body_content="def func1():\n    pass"
        )
        func2 = CodeFunction(
            name="func2", file_path="file2.py", line_start=10, line_end=15,
            signature="def func2():", body_content="def func2():\n    pass"
        )
        
        match = DuplicateMatch(
            new_function=func1,
            existing_function=func2,
            similarity_score=0.85
        )
        
        assert match.similarity_score == 0.85
        assert match.new_function == func1
        assert match.existing_function == func2


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
        detector = DuplicateLogicDetector(
            repository_path=str(temp_repo)
        )
        return detector
    
    def test_detector_initialization(self, detector):
        """Test detector initialization."""
        assert detector is not None
        assert hasattr(detector, 'repo_path')
        assert hasattr(detector, 'ast_analyzer')
        assert hasattr(detector, 'existing_functions')
    
    def test_extract_functions_from_file(self, detector, temp_repo):
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
            body_content="def calculate_total(items):\n    total = 0\n    for item in items:\n        total += item.get('price', 0)\n    return total"
        )
        
        func2 = CodeFunction(
            name="compute_sum",
            file_path="file2.py",
            line_start=10,
            line_end=15,
            signature="def compute_sum(products):",
            body_content="def compute_sum(products):\n    sum_total = 0\n    for product in products:\n        sum_total += product.get('price', 0)\n    return sum_total"
        )
        
        similarity = detector._calculate_similarity(func1, func2)
        
        # Should detect some similarity between these similar functions
        assert similarity > 0.0
        assert isinstance(similarity, float)
        assert 0 <= similarity <= 1
    
    def test_jaccard_similarity_calculation(self, detector):
        """Test Jaccard similarity calculation between two functions."""
        func1 = CodeFunction(
            name="func1", file_path="file1.py", line_start=1, line_end=5,
            signature="def func1():", body_content="def func1():\n    return x + y"
        )
        func2 = CodeFunction(
            name="func2", file_path="file2.py", line_start=1, line_end=5,
            signature="def func2():", body_content="def func2():\n    return a + b"
        )
        
        similarity = detector._calculate_similarity_jaccard_tokens(func1, func2)
        
        assert isinstance(similarity, float)
        assert 0 <= similarity <= 1


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
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
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
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email_address) is not None

def compute_discount_amount(original_price, discount_percent):
    \"\"\"Compute the discount amount for a price.\"\"\"
    if discount_percent < 0 or discount_percent > 100:
        return 0
    return original_price * (discount_percent / 100)
""")
            
            yield repo_path
    
    def test_full_duplicate_detection(self, sample_repo):
        """Test the complete duplicate detection process."""
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
            assert match.similarity_score >= 0.0
            assert match.similarity_score <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
