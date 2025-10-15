"""
Main duplicate logic detector module.

This module provides the primary DuplicateLogicDetector class that orchestrates
all the other modules to perform duplicate logic detection on code changes.
"""

import subprocess
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .extractor import PythonFunctionExtractor
from .models import CodeFunction, DuplicateMatch
from .similarity import SimilarityAnalyzer
from .thresholds import ThresholdConfig


class DuplicateLogicDetector:
    """
    Main class for detecting duplicate logic in code changes.
    
    This class orchestrates the function extraction, similarity analysis,
    and duplicate detection process for pull request changes.
    """

    def __init__(
        self,
        repository_path: str,
        similarity_method: str = "jaccard_tokens",
        min_function_lines: int = 5,
        threshold_config: Optional[ThresholdConfig] = None,
        console: Optional[Console] = None,
    ):
        """
        Initialize the duplicate logic detector.
        
        Args:
            repository_path: Path to the repository root
            similarity_method: Method to use for similarity calculation
            min_function_lines: Minimum lines for a function to be analyzed
            threshold_config: Configuration for similarity thresholds
            console: Rich console for output
        """
        self.repo_path = Path(repository_path)
        self.console = console or Console()
        self.min_function_lines = min_function_lines
        
        # Initialize the components
        self.extractor = PythonFunctionExtractor(self.console)
        self.similarity_analyzer = SimilarityAnalyzer(similarity_method)
        self.threshold_config = threshold_config or ThresholdConfig(console=self.console)
        self.existing_functions: List[CodeFunction] = []
        
        # Log the configuration
        self.console.print(f"[blue]Initialized detector with {similarity_method} similarity method[/blue]")

    def analyze_pr_changes(
        self,
        changed_files: List[str],
        base_sha: str,
        head_sha: str,
    ) -> List[DuplicateMatch]:
        """
        Analyze changes in a pull request for duplicate logic.
        
        Args:
            changed_files: List of file paths that changed in the PR
            base_sha: Base commit SHA for comparison
            head_sha: Head commit SHA for comparison
            
        Returns:
            List of duplicate matches sorted by similarity score (highest first)
        """
        matches = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            # Step 1: Index existing codebase
            task1 = progress.add_task("Indexing existing codebase...", total=None)
            self._index_existing_functions()
            progress.update(task1, completed=True)

            # Step 2: Analyze changed files
            python_files = [f for f in changed_files if f.endswith(".py")]
            if not python_files:
                self.console.print("[yellow]No Python files to analyze[/yellow]")
                return []

            task2 = progress.add_task(
                "Analyzing changed files...", total=len(python_files)
            )

            for file_path in python_files:
                if not Path(file_path).exists():
                    progress.advance(task2)
                    continue

                # Get functions that were added or modified
                new_functions = self._get_changed_functions(file_path, base_sha, head_sha)

                # Find similar functions for each new function
                for new_func in new_functions:
                    function_matches = self._find_similar_functions(new_func)
                    matches.extend(function_matches)

                progress.advance(task2)

        # Sort by similarity score (highest first)
        matches.sort(key=lambda m: m.similarity_score, reverse=True)

        self.console.print(f"[green]Analysis complete: {len(matches)} potential duplicates found[/green]")
        return matches

    def _index_existing_functions(self) -> None:
        """Index all functions in the existing codebase."""
        self.existing_functions = []
        
        # Find all Python files in the repository
        python_files = list(self.repo_path.glob("**/*.py"))
        
        for file_path in python_files:
            if file_path.is_file():
                functions = self.extractor.extract_from_file(file_path)
                
                # Filter functions based on criteria
                filtered_functions = self.extractor.filter_functions(
                    functions,
                    min_lines=self.min_function_lines,
                    exclude_test_files=True,
                    exclude_private=False,
                )
                
                self.existing_functions.extend(filtered_functions)

        self.console.print(
            f"[green]Indexed {len(self.existing_functions)} functions from codebase[/green]"
        )

    def _get_changed_functions(
        self, file_path: str, base_sha: str, head_sha: str
    ) -> List[CodeFunction]:
        """
        Get functions that were added or significantly modified in a file.
        
        For now, this implementation returns all functions in the current version
        of the file. A more sophisticated implementation could compare with the
        base version to identify only truly new/modified functions.
        
        Args:
            file_path: Path to the file to analyze
            base_sha: Base commit SHA
            head_sha: Head commit SHA
            
        Returns:
            List of functions that appear to be new or modified
        """
        try:
            # Extract functions from the current version
            current_functions = self.extractor.extract_from_file(file_path)
            
            # Filter to get meaningful functions
            filtered_functions = self.extractor.filter_functions(
                current_functions,
                min_lines=self.min_function_lines,
                exclude_test_files=True,
                exclude_private=False,
            )

            # TODO: Implement more sophisticated change detection
            # For now, we analyze all functions in changed files
            # In the future, we could:
            # 1. Compare with base version to find truly new/modified functions
            # 2. Use git diff to identify changed line ranges
            # 3. Only analyze functions that intersect with changed lines

            return filtered_functions

        except Exception as e:
            self.console.print(f"[red]Error analyzing changes in {file_path}: {e}[/red]")
            return []

    def _find_similar_functions(self, new_func: CodeFunction) -> List[DuplicateMatch]:
        """
        Find existing functions similar to the new function.
        
        Args:
            new_func: The new function to compare against existing ones
            
        Returns:
            List of duplicate matches for this function
        """
        matches = []

        for existing_func in self.existing_functions:
            # Skip if it's the same function (same file and name)
            if (
                existing_func.file_path == new_func.file_path
                and existing_func.name == new_func.name
            ):
                continue

            # Calculate similarity
            similarity_score = self.similarity_analyzer.calculate_similarity(
                new_func, existing_func
            )

            # Only include matches above the configured threshold
            # Check both file paths and use the more strict (higher) threshold
            new_threshold = self.threshold_config.get_threshold_for_file(new_func.file_path)
            existing_threshold = self.threshold_config.get_threshold_for_file(existing_func.file_path)
            effective_threshold = max(new_threshold, existing_threshold)
            
            if similarity_score >= effective_threshold:
                match = DuplicateMatch(
                    new_function=new_func,
                    existing_function=existing_func,
                    similarity_score=similarity_score,
                )
                matches.append(match)

        return matches

    def get_configuration_info(self) -> dict:
        """Get information about the current detector configuration."""
        config = {
            "repository_path": str(self.repo_path),
            "similarity_method": self.similarity_analyzer.current_method,
            "similarity_description": self.similarity_analyzer.current_method_description,
            "min_function_lines": self.min_function_lines,
            "indexed_functions": len(self.existing_functions),
            "available_similarity_methods": list(
                self.similarity_analyzer.get_available_methods().keys()
            ),
        }
        
        # Add threshold configuration
        config.update(self.threshold_config.get_configuration_summary())
        
        return config

    def print_configuration(self) -> None:
        """Print the current detector configuration."""
        config = self.get_configuration_info()
        
        self.console.print("[bold blue]Duplicate Logic Detector Configuration[/bold blue]")
        self.console.print(f"Repository: {config['repository_path']}")
        self.console.print(f"Similarity Method: {config['similarity_method']}")
        self.console.print(f"Description: {config['similarity_description']}")
        self.console.print(f"Min Function Lines: {config['min_function_lines']}")
        self.console.print(f"Indexed Functions: {config['indexed_functions']}")
        
        # Print threshold configuration
        self.console.print("")
        self.threshold_config.print_configuration()


class GitChangeAnalyzer:
    """
    Helper class for analyzing Git changes.
    
    This class provides utilities for working with Git to understand
    what changed in a pull request.
    """

    def __init__(self, repo_path: Path, console: Optional[Console] = None):
        """
        Initialize the Git change analyzer.
        
        Args:
            repo_path: Path to the Git repository
            console: Rich console for output
        """
        self.repo_path = repo_path
        self.console = console or Console()

    def get_file_content_at_commit(self, file_path: str, commit_sha: str) -> str:
        """
        Get the content of a file at a specific commit.
        
        Args:
            file_path: Path to the file relative to repo root
            commit_sha: Git commit SHA
            
        Returns:
            File content as string, or empty string if not found
        """
        try:
            result = subprocess.run(
                ["git", "show", f"{commit_sha}:{file_path}"],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return ""
                
        except Exception as e:
            self.console.print(f"[red]Error getting file content: {e}[/red]")
            return ""

    def get_changed_lines(self, file_path: str, base_sha: str, head_sha: str) -> List[int]:
        """
        Get the line numbers that changed in a file between two commits.
        
        Args:
            file_path: Path to the file
            base_sha: Base commit SHA
            head_sha: Head commit SHA
            
        Returns:
            List of line numbers that were modified
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--unified=0", f"{base_sha}..{head_sha}", "--", file_path],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
            )
            
            if result.returncode != 0:
                return []

            changed_lines = []
            for line in result.stdout.split('\n'):
                if line.startswith('@@'):
                    # Parse the @@ -old_start,old_count +new_start,new_count @@ format
                    parts = line.split()
                    if len(parts) >= 3:
                        new_range = parts[2][1:]  # Remove the '+' prefix
                        if ',' in new_range:
                            start, count = new_range.split(',')
                            start, count = int(start), int(count)
                            changed_lines.extend(range(start, start + count))
                        else:
                            changed_lines.append(int(new_range))
            
            return sorted(set(changed_lines))
            
        except Exception as e:
            self.console.print(f"[red]Error analyzing changed lines: {e}[/red]")
            return []
