"""
Function extraction module for Python code analysis.

This module handles parsing Python files and extracting function definitions
along with their metadata.
"""

import ast
import re
from pathlib import Path
from typing import List, Optional, Union

from rich.console import Console

from .models import CodeFunction


class PythonFunctionExtractor:
    """
    Extracts function definitions from Python source code.
    
    This class uses Python's AST (Abstract Syntax Tree) module to parse
    Python files and extract function information including signatures,
    line numbers, and body content.
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the function extractor.
        
        Args:
            console: Optional Rich console for output. If None, creates a new one.
        """
        self.console = console or Console()

    def extract_from_file(self, file_path: Union[str, Path]) -> List[CodeFunction]:
        """
        Extract all functions from a Python file.
        
        Args:
            file_path: Path to the Python file to analyze
            
        Returns:
            List of CodeFunction objects found in the file
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.console.print(f"[red]File not found: {file_path}[/red]")
            return []

        if not file_path.suffix == '.py':
            self.console.print(f"[yellow]Skipping non-Python file: {file_path}[/yellow]")
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return self.extract_from_content(content, str(file_path))

        except UnicodeDecodeError:
            self.console.print(f"[red]Unable to decode file: {file_path}[/red]")
            return []
        except Exception as e:
            self.console.print(f"[red]Error reading {file_path}: {e}[/red]")
            return []

    def extract_from_content(self, content: str, file_path: str) -> List[CodeFunction]:
        """
        Extract functions from Python source code content.
        
        Args:
            content: Python source code as a string
            file_path: Path to the file (for metadata)
            
        Returns:
            List of CodeFunction objects found in the content
        """
        try:
            tree = ast.parse(content, filename=file_path)
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func = self._extract_function_info(node, content, file_path)
                    if func:
                        functions.append(func)

            return functions

        except SyntaxError as e:
            self.console.print(f"[red]Syntax error in {file_path}:{e.lineno}: {e.msg}[/red]")
            return []
        except Exception as e:
            self.console.print(f"[red]Error parsing {file_path}: {e}[/red]")
            return []

    def _extract_function_info(
        self,
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
        content: str,
        file_path: str,
    ) -> Optional[CodeFunction]:
        """
        Extract detailed information about a function from its AST node.
        
        Args:
            node: AST node representing the function
            content: Full source code content
            file_path: Path to the file
            
        Returns:
            CodeFunction object or None if extraction fails
        """
        try:
            signature = self._get_function_signature(node)
            lines = content.split("\n")
            
            line_start = node.lineno
            line_end = node.end_lineno or line_start
            
            # Extract the actual function body content
            body_lines = lines[line_start - 1:line_end]  # AST uses 1-based line numbers
            body_content = "\n".join(body_lines)

            return CodeFunction(
                name=node.name,
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
                signature=signature,
                body_content=body_content,
            )

        except Exception as e:
            self.console.print(f"[red]Error extracting function {node.name}: {e}[/red]")
            return None

    def _get_function_signature(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> str:
        """
        Extract a normalized function signature from the AST node.
        
        Args:
            node: AST node representing the function
            
        Returns:
            String representation of the function signature
        """
        args = []

        # Regular arguments
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                try:
                    arg_str += f": {ast.unparse(arg.annotation)}"
                except Exception:
                    # Fallback if unparse fails
                    arg_str += ": <annotation>"
            args.append(arg_str)

        # *args parameter
        if node.args.vararg:
            vararg = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation:
                try:
                    vararg += f": {ast.unparse(node.args.vararg.annotation)}"
                except Exception:
                    vararg += ": <annotation>"
            args.append(vararg)

        # **kwargs parameter
        if node.args.kwarg:
            kwarg = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation:
                try:
                    kwarg += f": {ast.unparse(node.args.kwarg.annotation)}"
                except Exception:
                    kwarg += ": <annotation>"
            args.append(kwarg)

        # Return annotation
        returns = ""
        if node.returns:
            try:
                returns = f" -> {ast.unparse(node.returns)}"
            except Exception:
                returns = " -> <return_annotation>"

        # Build the full signature
        prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
        return f"{prefix}def {node.name}({', '.join(args)}){returns}"

    def normalize_code(self, code: str) -> str:
        """
        Normalize code by removing comments and extra whitespace.
        
        This can be useful for more consistent similarity analysis.
        
        Args:
            code: Raw Python code
            
        Returns:
            Normalized code string
        """
        lines = []
        for line in code.split("\n"):
            # Remove comments
            line = re.sub(r"#.*$", "", line)
            # Normalize whitespace
            line = re.sub(r"\s+", " ", line.strip())
            if line:  # Skip empty lines
                lines.append(line)
        return "\n".join(lines)

    def filter_functions(
        self,
        functions: List[CodeFunction],
        min_lines: int = 5,
        exclude_test_files: bool = True,
        exclude_private: bool = False,
    ) -> List[CodeFunction]:
        """
        Filter functions based on various criteria.
        
        Args:
            functions: List of functions to filter
            min_lines: Minimum number of lines for a function to be included
            exclude_test_files: Whether to exclude functions from test files
            exclude_private: Whether to exclude private functions (starting with _)
            
        Returns:
            Filtered list of functions
        """
        filtered = []

        for func in functions:
            # Skip small functions
            if func.line_count < min_lines:
                continue

            # Skip test files if requested
            if exclude_test_files and self._is_test_file(func.file_path):
                continue

            # Skip private functions if requested
            if exclude_private and func.name.startswith('_'):
                continue

            filtered.append(func)

        return filtered

    def _is_test_file(self, file_path: str) -> bool:
        """
        Check if a file path appears to be a test file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if the file appears to be a test file
        """
        path = Path(file_path)
        name = path.name.lower()
        parent_names = [p.name.lower() for p in path.parents]

        # Common test file patterns
        test_patterns = [
            name.startswith('test_'),
            name.endswith('_test.py'),
            'test' in parent_names,
            'tests' in parent_names,
        ]

        return any(test_patterns)
