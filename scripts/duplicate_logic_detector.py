#!/usr/bin/env python3
"""
Duplicate Logic Detection Tool

This script analyzes code changes in pull requests to detect if new logic
recreates functionality that already exists in the codebase.

Uses multiple detection strategies:
1. AST-based structural similarity
2. Semantic similarity analysis
3. Function signature matching
4. Code pattern recognition
5. Import and dependency analysis
"""

from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError as e:
    print(f"Error importing required dependencies: {e}")
    print("Please install required packages:")
    print("pip install scikit-learn rich")
    sys.exit(1)


@dataclass
class CodeFunction:
    """Represents a function extracted from code."""

    name: str
    file_path: str
    line_start: int
    line_end: int
    signature: str
    docstring: str | None
    body_hash: str
    imports: list[str]  # Changed from Set to List for JSON serialization
    calls: list[str]  # Changed from Set to List for JSON serialization
    complexity_score: float
    ast_structure: str


@dataclass
class DuplicateMatch:
    """Represents a potential duplicate logic match."""

    new_function: CodeFunction
    existing_function: CodeFunction
    similarity_score: float
    match_type: str
    confidence: str
    reasons: list[str]
    suggestion: str


class ASTAnalyzer:
    """Analyzes Python AST for structural patterns and similarity."""

    def __init__(self):
        self.console = Console()

    def extract_functions_from_file(self, file_path: str) -> list[CodeFunction]:
        """Extract all functions from a Python file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=file_path)
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func = self._extract_function_info(node, content, file_path)
                    if func:
                        functions.append(func)

            return functions
        except Exception as e:
            self.console.print(f"[red]Error parsing {file_path}: {e}[/red]")
            return []

    def _extract_function_info(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, content: str, file_path: str
    ) -> CodeFunction | None:
        """Extract detailed information about a function."""
        try:
            # Get function signature
            signature = self._get_function_signature(node)

            # Get docstring
            docstring = ast.get_docstring(node)

            # Get function body
            lines = content.split("\n")
            line_start = node.lineno
            line_end = node.end_lineno or line_start

            # Calculate body hash (excluding comments and docstrings)
            body_lines = lines[line_start - 1 : line_end]
            normalized_body = self._normalize_code("\n".join(body_lines))
            body_hash = hashlib.md5(normalized_body.encode()).hexdigest()

            # Extract imports and function calls
            imports = self._extract_imports(node)
            calls = self._extract_function_calls(node)

            # Calculate complexity score
            complexity = self._calculate_complexity(node)

            # Get AST structure fingerprint
            ast_structure = self._get_ast_structure(node)

            return CodeFunction(
                name=node.name,
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
                signature=signature,
                docstring=docstring,
                body_hash=body_hash,
                imports=imports,
                calls=calls,
                complexity_score=complexity,
                ast_structure=ast_structure,
            )
        except Exception as e:
            self.console.print(f"[red]Error extracting function {node.name}: {e}[/red]")
            return None

    def _get_function_signature(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> str:
        """Extract normalized function signature."""
        args = []

        # Regular arguments
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)

        # Handle *args and **kwargs
        if node.args.vararg:
            vararg = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation:
                vararg += f": {ast.unparse(node.args.vararg.annotation)}"
            args.append(vararg)

        if node.args.kwarg:
            kwarg = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation:
                kwarg += f": {ast.unparse(node.args.kwarg.annotation)}"
            args.append(kwarg)

        # Return type
        returns = ""
        if node.returns:
            returns = f" -> {ast.unparse(node.returns)}"

        prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
        return f"{prefix}def {node.name}({', '.join(args)}){returns}"

    def _normalize_code(self, code: str) -> str:
        """Normalize code by removing comments, extra whitespace, etc."""
        lines = []
        for line in code.split("\n"):
            # Remove comments
            line = re.sub(r"#.*$", "", line)
            # Normalize whitespace
            line = re.sub(r"\s+", " ", line.strip())
            if line:
                lines.append(line)
        return "\n".join(lines)

    def _extract_imports(self, node: ast.AST) -> set[str]:
        """Extract all imports used within a function."""
        imports = []
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                if child.id not in imports:
                    imports.append(child.id)
            elif isinstance(child, ast.Attribute):
                attr_str = ast.unparse(child)
                if attr_str not in imports:
                    imports.append(attr_str)
        return imports

    def _extract_function_calls(self, node: ast.AST) -> set[str]:
        """Extract all function calls within a function."""
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    if child.func.id not in calls:
                        calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    func_str = ast.unparse(child.func)
                    if func_str not in calls:
                        calls.append(func_str)
        return calls

    def _calculate_complexity(self, node: ast.AST) -> float:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(
                child,
                (
                    ast.If,
                    ast.While,
                    ast.For,
                    ast.AsyncFor,
                    ast.ExceptHandler,
                    ast.And,
                    ast.Or,
                ),
            ):
                complexity += 1

        return float(complexity)

    def _get_ast_structure(self, node: ast.AST) -> str:
        """Get a structural fingerprint of the AST."""
        structure = []
        for child in ast.walk(node):
            structure.append(type(child).__name__)
        return ",".join(sorted(set(structure)))


class SemanticAnalyzer:
    """Analyzes semantic similarity between code functions."""

    def __init__(self):
        self.console = Console()
        self.vectorizer = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 3), max_features=1000
        )

    def calculate_similarity(self, func1: CodeFunction, func2: CodeFunction) -> float:
        """Calculate semantic similarity between two functions."""
        # Combine various text features
        text1 = self._extract_text_features(func1)
        text2 = self._extract_text_features(func2)

        if not text1 or not text2:
            return 0.0

        try:
            # Use TF-IDF vectorization
            vectors = self.vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return float(similarity)
        except Exception:
            return 0.0

    def _extract_text_features(self, func: CodeFunction) -> str:
        """Extract textual features from a function for similarity analysis."""
        features = []

        # Function name (split camelCase/snake_case and extract keywords)
        name_tokens = re.sub(r"([a-z])([A-Z])", r"\1 \2", func.name).lower()
        name_tokens = re.sub(r"[_-]", " ", name_tokens)
        features.append(name_tokens)

        # Extract semantic keywords from function name
        semantic_keywords = []
        name_lower = func.name.lower()
        if "validate" in name_lower or "check" in name_lower or "verify" in name_lower:
            semantic_keywords.append("validation")
        if "email" in name_lower or "mail" in name_lower:
            semantic_keywords.append("email")
        if "user" in name_lower or "customer" in name_lower:
            semantic_keywords.append("user")
        if "data" in name_lower or "info" in name_lower:
            semantic_keywords.append("data")
        if (
            "process" in name_lower
            or "transform" in name_lower
            or "convert" in name_lower
        ):
            semantic_keywords.append("processing")
        if (
            "calculate" in name_lower
            or "compute" in name_lower
            or "score" in name_lower
        ):
            semantic_keywords.append("calculation")

        features.extend(semantic_keywords)

        # Docstring (extract key terms)
        if func.docstring:
            doc_lower = func.docstring.lower()
            features.append(doc_lower)
            # Extract key terms from docstring
            if "email" in doc_lower:
                features.append("email")
            if "validate" in doc_lower or "check" in doc_lower:
                features.append("validation")
            if "user" in doc_lower:
                features.append("user")
            if "data" in doc_lower:
                features.append("data")

        # Function calls (meaningful names only)
        meaningful_calls = {
            call for call in func.calls if len(call) > 2 and not call.startswith("_")
        }
        features.extend(meaningful_calls)

        # Add regex pattern detection for common patterns
        if "re.match" in func.calls or "match" in func.calls:
            features.append("regex pattern matching")
        if "get" in " ".join(func.calls):
            features.append("data access")

        # Imports (domain-specific terms)
        domain_imports = {
            imp
            for imp in func.imports
            if any(
                keyword in imp.lower()
                for keyword in [
                    "user",
                    "auth",
                    "data",
                    "api",
                    "db",
                    "service",
                    "util",
                    "email",
                    "mail",
                ]
            )
        }
        features.extend(domain_imports)

        return " ".join(features)


class DuplicateLogicDetector:
    """Main class for detecting duplicate logic in code changes."""

    def __init__(self, repository_path: str):
        self.repo_path = Path(repository_path)
        self.console = Console()
        self.ast_analyzer = ASTAnalyzer()
        self.semantic_analyzer = SemanticAnalyzer()
        self.existing_functions: list[CodeFunction] = []

        # Thresholds for different types of matches
        self.EXACT_MATCH_THRESHOLD = 0.90
        self.HIGH_SIMILARITY_THRESHOLD = 0.70
        self.MODERATE_SIMILARITY_THRESHOLD = 0.50

    def analyze_pr_changes(
        self, changed_files: list[str], base_sha: str, head_sha: str
    ) -> list[DuplicateMatch]:
        """Analyze changes in a pull request for duplicate logic."""
        matches = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            # Load existing codebase functions
            task1 = progress.add_task("Indexing existing codebase...", total=None)
            self._index_existing_functions()
            progress.update(task1, completed=True)

            # Analyze changed files
            task2 = progress.add_task(
                "Analyzing changed files...", total=len(changed_files)
            )

            for file_path in changed_files:
                if not file_path.endswith(".py") or not Path(file_path).exists():
                    progress.advance(task2)
                    continue

                # Get new/modified functions in this file
                new_functions = self._get_changed_functions(
                    file_path, base_sha, head_sha
                )

                # Check each new function against existing ones
                for new_func in new_functions:
                    function_matches = self._find_similar_functions(new_func)
                    matches.extend(function_matches)

                progress.advance(task2)

        # Sort matches by similarity score (highest first)
        matches.sort(key=lambda m: m.similarity_score, reverse=True)

        return matches

    def _index_existing_functions(self):
        """Index all functions in the existing codebase."""
        self.existing_functions = []

        # Find all Python files in src/ and tests/
        python_files = []
        for pattern in ["src/**/*.py", "tests/**/*.py"]:
            python_files.extend(self.repo_path.glob(pattern))

        for file_path in python_files:
            if file_path.is_file():
                functions = self.ast_analyzer.extract_functions_from_file(
                    str(file_path)
                )
                self.existing_functions.extend(functions)

        self.console.print(
            f"[green]Indexed {len(self.existing_functions)} functions from codebase[/green]"
        )

    def _get_changed_functions(
        self, file_path: str, base_sha: str, head_sha: str
    ) -> list[CodeFunction]:
        """Get functions that were added or significantly modified in a file."""
        try:
            # Get current functions
            current_functions = self.ast_analyzer.extract_functions_from_file(file_path)

            # Try to get the base version of the file
            try:
                result = subprocess.run(
                    ["git", "show", f"{base_sha}:{file_path}"],
                    capture_output=True,
                    text=True,
                    cwd=self.repo_path,
                )
                if result.returncode == 0:
                    # Write base version to temp file and analyze
                    temp_file = Path(f"/tmp/base_{Path(file_path).name}")
                    temp_file.write_text(result.stdout)
                    base_functions = self.ast_analyzer.extract_functions_from_file(
                        str(temp_file)
                    )
                    temp_file.unlink()

                    # Find new or significantly changed functions
                    base_func_hashes = {f.name: f.body_hash for f in base_functions}
                    changed_functions = []

                    for func in current_functions:
                        if (
                            func.name not in base_func_hashes
                            or base_func_hashes[func.name] != func.body_hash
                        ):
                            changed_functions.append(func)

                    return changed_functions
                else:
                    # File is new, all functions are new
                    return current_functions
            except Exception:
                # If we can't get base version, treat all functions as new
                return current_functions

        except Exception as e:
            self.console.print(
                f"[red]Error analyzing changes in {file_path}: {e}[/red]"
            )
            return []

    def _find_similar_functions(self, new_func: CodeFunction) -> list[DuplicateMatch]:
        """Find existing functions similar to the new function."""
        matches = []

        for existing_func in self.existing_functions:
            # Skip if it's the same function (same file and name)
            if (
                existing_func.file_path == new_func.file_path
                and existing_func.name == new_func.name
            ):
                continue

            # Calculate various similarity metrics
            similarity_score, match_type, reasons = self._calculate_similarity(
                new_func, existing_func
            )

            if similarity_score >= self.MODERATE_SIMILARITY_THRESHOLD:
                confidence = self._determine_confidence(similarity_score)
                suggestion = self._generate_suggestion(
                    new_func, existing_func, similarity_score
                )

                match = DuplicateMatch(
                    new_function=new_func,
                    existing_function=existing_func,
                    similarity_score=similarity_score,
                    match_type=match_type,
                    confidence=confidence,
                    reasons=reasons,
                    suggestion=suggestion,
                )
                matches.append(match)

        return matches

    def _calculate_similarity(
        self, func1: CodeFunction, func2: CodeFunction
    ) -> tuple[float, str, list[str]]:
        """Calculate comprehensive similarity between two functions."""
        scores = []
        reasons = []

        # 1. Exact body hash match
        if func1.body_hash == func2.body_hash:
            return 1.0, "exact_duplicate", ["Identical function body"]

        # 2. Function signature similarity
        sig_similarity = difflib.SequenceMatcher(
            None, func1.signature, func2.signature
        ).ratio()
        scores.append(sig_similarity * 0.25)
        if sig_similarity > 0.6:
            reasons.append(f"Similar function signature ({sig_similarity:.2f})")

        # 3. Semantic similarity (enhanced)
        semantic_similarity = self.semantic_analyzer.calculate_similarity(func1, func2)
        scores.append(semantic_similarity * 0.35)
        if semantic_similarity > 0.3:
            reasons.append(f"Similar semantic content ({semantic_similarity:.2f})")

        # 4. AST structure similarity
        ast_similarity = self._compare_ast_structures(
            func1.ast_structure, func2.ast_structure
        )
        scores.append(ast_similarity * 0.25)
        if ast_similarity > 0.5:
            reasons.append(f"Similar code structure ({ast_similarity:.2f})")

        # 5. Function calls overlap
        if func1.calls and func2.calls:
            calls_set1 = set(func1.calls)
            calls_set2 = set(func2.calls)
            calls_overlap = len(calls_set1 & calls_set2) / len(calls_set1 | calls_set2)
            scores.append(calls_overlap * 0.15)
            if calls_overlap > 0.3:
                reasons.append(f"Similar function calls ({calls_overlap:.2f})")

        # 6. Function name similarity (new)
        name_similarity = difflib.SequenceMatcher(
            None, func1.name.lower(), func2.name.lower()
        ).ratio()
        if name_similarity > 0.4:
            scores.append(name_similarity * 0.1)
            reasons.append(f"Similar function names ({name_similarity:.2f})")

        # 7. Complexity similarity bonus
        if func1.complexity_score > 1 and func2.complexity_score > 1:
            complexity_ratio = min(
                func1.complexity_score, func2.complexity_score
            ) / max(func1.complexity_score, func2.complexity_score)
            if complexity_ratio > 0.8:
                scores.append(0.05)  # Small bonus for similar complexity
                reasons.append(
                    f"Similar complexity ({func1.complexity_score} vs {func2.complexity_score})"
                )

        overall_similarity = sum(scores)

        # Determine match type
        if overall_similarity >= self.EXACT_MATCH_THRESHOLD:
            match_type = "near_duplicate"
        elif overall_similarity >= self.HIGH_SIMILARITY_THRESHOLD:
            match_type = "high_similarity"
        else:
            match_type = "moderate_similarity"

        return overall_similarity, match_type, reasons

    def _compare_ast_structures(self, struct1: str, struct2: str) -> float:
        """Compare AST structure fingerprints."""
        if not struct1 or not struct2:
            return 0.0

        set1 = set(struct1.split(","))
        set2 = set(struct2.split(","))

        if not set1 or not set2:
            return 0.0

        return len(set1 & set2) / len(set1 | set2)

    def _determine_confidence(self, similarity_score: float) -> str:
        """Determine confidence level based on similarity score."""
        if similarity_score >= self.EXACT_MATCH_THRESHOLD:
            return "very_high"
        elif similarity_score >= self.HIGH_SIMILARITY_THRESHOLD:
            return "high"
        elif similarity_score >= self.MODERATE_SIMILARITY_THRESHOLD:
            return "medium"
        else:
            return "low"

    def _generate_suggestion(
        self,
        new_func: CodeFunction,
        existing_func: CodeFunction,
        similarity_score: float,
    ) -> str:
        """Generate a suggestion for handling the duplicate logic."""
        if similarity_score >= self.EXACT_MATCH_THRESHOLD:
            return (
                f"Consider reusing the existing function `{existing_func.name}` "
                f"from `{existing_func.file_path}` instead of implementing similar logic."
            )
        elif similarity_score >= self.HIGH_SIMILARITY_THRESHOLD:
            return (
                f"Review the existing function `{existing_func.name}` in "
                f"`{existing_func.file_path}` - it may provide similar functionality "
                f"that could be extended or refactored for reuse."
            )
        else:
            return (
                f"Consider reviewing `{existing_func.name}` in "
                f"`{existing_func.file_path}` for potential code reuse opportunities."
            )


class ReportGenerator:
    """Generates reports for duplicate logic analysis."""

    def __init__(self):
        self.console = Console()

    def generate_github_comment(self, matches: list[DuplicateMatch]) -> str:
        """Generate a GitHub PR comment with duplicate logic findings."""
        if not matches:
            return ""

        # Filter to only high-confidence matches for PR comments
        significant_matches = [
            m for m in matches if m.confidence in ["high", "very_high"]
        ]

        if not significant_matches:
            return ""

        comment = "## 🔍 Duplicate Logic Detection\n\n"
        comment += "The following functions in your PR may recreate logic that already exists:\n\n"

        for i, match in enumerate(significant_matches[:5], 1):  # Limit to top 5
            confidence_emoji = "🚨" if match.confidence == "very_high" else "⚠️"

            comment += f"### {confidence_emoji} Match #{i}\n"
            comment += f"**New Function:** `{match.new_function.name}` in `{match.new_function.file_path}`\n"
            comment += f"**Similar to:** `{match.existing_function.name}` in `{match.existing_function.file_path}`\n"
            comment += f"**Similarity:** {match.similarity_score:.1%} ({match.confidence} confidence)\n"
            comment += f"**Type:** {match.match_type.replace('_', ' ').title()}\n\n"

            comment += "**Reasons:**\n"
            for reason in match.reasons:
                comment += f"- {reason}\n"

            comment += f"\n**Suggestion:** {match.suggestion}\n\n"
            comment += "---\n\n"

        comment += "<details>\n<summary>ℹ️ About this check</summary>\n\n"
        comment += "This automated analysis compares new functions against the existing codebase using:\n"
        comment += "- Abstract Syntax Tree (AST) structure analysis\n"
        comment += "- Semantic similarity of function names, docstrings, and calls\n"
        comment += "- Function signature comparison\n"
        comment += "- Code pattern recognition\n\n"
        comment += "Please review these matches to avoid code duplication and improve maintainability.\n"
        comment += "</details>"

        return comment

    def generate_json_report(self, matches: list[DuplicateMatch]) -> dict[str, Any]:
        """Generate a JSON report of all findings."""
        return {
            "summary": {
                "total_matches": len(matches),
                "high_confidence": len(
                    [m for m in matches if m.confidence == "very_high"]
                ),
                "medium_confidence": len(
                    [m for m in matches if m.confidence == "high"]
                ),
                "low_confidence": len([m for m in matches if m.confidence == "medium"]),
            },
            "matches": [asdict(match) for match in matches],
        }

    def print_console_report(self, matches: list[DuplicateMatch]):
        """Print a formatted console report."""
        if not matches:
            self.console.print("[green]✅ No duplicate logic detected![/green]")
            return

        table = Table(title="Duplicate Logic Detection Results")
        table.add_column("New Function", style="cyan")
        table.add_column("Existing Function", style="magenta")
        table.add_column("Similarity", style="yellow")
        table.add_column("Confidence", style="green")

        for match in matches[:10]:  # Show top 10
            confidence_color = {
                "very_high": "red",
                "high": "yellow",
                "medium": "blue",
                "low": "dim",
            }.get(match.confidence, "white")

            table.add_row(
                f"{match.new_function.name}\n{match.new_function.file_path}",
                f"{match.existing_function.name}\n{match.existing_function.file_path}",
                f"{match.similarity_score:.1%}",
                f"[{confidence_color}]{match.confidence}[/{confidence_color}]",
            )

        self.console.print(table)


def main():
    """Main entry point for the duplicate logic detector."""
    parser = argparse.ArgumentParser(
        description="Detect duplicate logic in pull requests"
    )
    parser.add_argument("--pr-number", type=int, help="Pull request number")
    parser.add_argument("--repository", help="Repository name (owner/repo)")
    parser.add_argument("--base-sha", help="Base commit SHA")
    parser.add_argument("--head-sha", help="Head commit SHA")
    parser.add_argument("--changed-files", help="JSON list of changed files")
    parser.add_argument(
        "--output-format",
        choices=["console", "github-actions", "json"],
        default="console",
        help="Output format",
    )
    parser.add_argument("--repository-path", default=".", help="Path to repository")

    args = parser.parse_args()

    console = Console()

    try:
        # Parse changed files
        if args.changed_files:
            changed_files = [
                f.strip() for f in args.changed_files.strip().split("\n") if f.strip()
            ]
        else:
            console.print("[red]No changed files provided[/red]")
            return 1

        if not changed_files:
            console.print("[green]No Python files changed[/green]")
            return 0

        # Initialize detector
        detector = DuplicateLogicDetector(args.repository_path)

        # Analyze changes
        matches = detector.analyze_pr_changes(
            changed_files, args.base_sha, args.head_sha
        )

        # Generate reports
        report_gen = ReportGenerator()

        if args.output_format == "console":
            report_gen.print_console_report(matches)
        elif args.output_format == "github-actions":
            # Generate GitHub Actions outputs
            significant_matches = [
                m for m in matches if m.confidence in ["high", "very_high"]
            ]

            if significant_matches:
                # Use environment files instead of deprecated set-output
                with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                    f.write("duplicates_found=true\n")
                    f.write(f"match_count={len(significant_matches)}\n")

                # Generate markdown report
                comment = report_gen.generate_github_comment(matches)
                with open("duplicate-logic-report.md", "w") as f:
                    f.write(comment)

                console.print(
                    f"[yellow]Found {len(significant_matches)} potential duplicates[/yellow]"
                )
            else:
                # Use environment files instead of deprecated set-output
                with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                    f.write("duplicates_found=false\n")
                    f.write("match_count=0\n")
                console.print("[green]No significant duplicates found[/green]")

            # Always generate JSON report
            json_report = report_gen.generate_json_report(matches)
            with open("duplicate-logic-report.json", "w") as f:
                json.dump(json_report, f, indent=2)

        elif args.output_format == "json":
            json_report = report_gen.generate_json_report(matches)
            print(json.dumps(json_report, indent=2))

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
