#!/usr/bin/env python3
"""
Duplicate Logic Detection Tool

This script analyzes code changes in pull requests to detect if new logic
recreates functionality that already exists in the codebase.

Uses token-based similarity analysis with Jaccard similarity to detect
duplicate code patterns.
"""

import argparse
import ast
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
import subprocess
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn


@dataclass
class CodeFunction:
    """Represents a function extracted from code."""

    name: str
    file_path: str
    line_start: int
    line_end: int
    signature: str
    body_content: str


@dataclass
class DuplicateMatch:
    """Represents a potential duplicate logic match."""

    new_function: CodeFunction
    existing_function: CodeFunction
    similarity_score: float


class ASTAnalyzer:
    """Analyzes Python AST for structural patterns and similarity."""

    def __init__(self):
        self.console = Console()

    def extract_functions_from_file(self, file_path: str) -> List[CodeFunction]:
        """Extract all functions from a Python file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
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
        self,
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
        content: str,
        file_path: str,
    ) -> Optional[CodeFunction]:
        """Extract detailed information about a function."""
        try:
            signature = self._get_function_signature(node)

            lines = content.split("\n")
            line_start = node.lineno
            line_end = node.end_lineno or line_start

            body_lines = lines[line_start:line_end]
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
        """Extract normalized function signature."""
        args = []

        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)

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

        returns = ""
        if node.returns:
            returns = f" -> {ast.unparse(node.returns)}"

        prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
        return f"{prefix}def {node.name}({', '.join(args)}){returns}"

    def _normalize_code(self, code: str) -> str:
        """Normalize code by removing comments, extra whitespace, etc."""
        lines = []
        for line in code.split("\n"):
            line = re.sub(r"#.*$", "", line)
            line = re.sub(r"\s+", " ", line.strip())
            if line:
                lines.append(line)
        return "\n".join(lines)

    def _extract_imports(self, node: ast.AST) -> Set[str]:
        """Extract all imports used within a function."""
        imports = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                imports.add(child.id)
            elif isinstance(child, ast.Attribute):
                attr_str = ast.unparse(child)
                imports.add(attr_str)
        return imports

    def _extract_function_calls(self, node: ast.AST) -> Set[str]:
        """Extract all function calls within a function."""
        calls = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.add(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    func_str = ast.unparse(child.func)
                    calls.add(func_str)
        return calls

    def _calculate_complexity(self, node: ast.AST) -> float:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1

        return float(complexity)

    def _get_ast_structure(self, node: ast.AST) -> str:
        """Get a structural fingerprint of the AST."""
        structure = []
        for child in ast.walk(node):
            structure.append(type(child).__name__)
        return ",".join(sorted(set(structure)))


class DuplicateLogicDetector:
    """Main class for detecting duplicate logic in code changes."""

    def __init__(self, repository_path: str):
        self.repo_path = Path(repository_path)
        self.console = Console()
        self.ast_analyzer = ASTAnalyzer()
        self.existing_functions: List[CodeFunction] = []

    def analyze_pr_changes(
        self, changed_files: List[str], base_sha: str, head_sha: str
    ) -> List[DuplicateMatch]:
        """Analyze changes in a pull request for duplicate logic."""
        matches = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task1 = progress.add_task("Indexing existing codebase...", total=None)
            self._index_existing_functions()
            progress.update(task1, completed=True)

            task2 = progress.add_task(
                "Analyzing changed files...", total=len(changed_files)
            )

            for file_path in changed_files:
                if not file_path.endswith(".py") or not Path(file_path).exists():
                    progress.advance(task2)
                    continue

                new_functions = self._get_changed_functions(
                    file_path, base_sha, head_sha
                )

                for new_func in new_functions:
                    function_matches = self._find_similar_functions(new_func)
                    matches.extend(function_matches)

                progress.advance(task2)

        matches.sort(key=lambda m: m.similarity_score, reverse=True)

        return matches

    def _index_existing_functions(self):
        """Index all functions in the existing codebase."""
        python_files = []
        python_files.extend(self.repo_path.glob("*.py"))

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
    ) -> List[CodeFunction]:
        """Get functions that were added or significantly modified in a file."""
        try:
            current_functions = self.ast_analyzer.extract_functions_from_file(file_path)

            try:
                result = subprocess.run(
                    ["git", "show", f"{base_sha}:{file_path}"],
                    capture_output=True,
                    text=True,
                    cwd=self.repo_path,
                )
                if result.returncode == 0:
                    temp_file = Path(f"/tmp/base_{Path(file_path).name}")
                    temp_file.write_text(result.stdout)
                    temp_file.unlink()

                    changed_functions = current_functions

                    return changed_functions
                else:
                    return current_functions
            except Exception:
                return current_functions

        except Exception as e:
            self.console.print(
                f"[red]Error analyzing changes in {file_path}: {e}[/red]"
            )
            return []

    def _find_similar_functions(self, new_func: CodeFunction) -> List[DuplicateMatch]:
        """Find existing functions similar to the new function."""
        matches = []

        for existing_func in self.existing_functions:
            if (
                existing_func.file_path == new_func.file_path
                and existing_func.name == new_func.name
            ):
                continue

            similarity_score = self._calculate_similarity(new_func, existing_func)
            match = DuplicateMatch(
                new_function=new_func,
                existing_function=existing_func,
                similarity_score=similarity_score,
            )
            matches.append(match)

        return matches

    def _calculate_similarity(self, func1: CodeFunction, func2: CodeFunction) -> float:
        """Calculate similarity between two functions using the configured method."""
        return self._calculate_similarity_jaccard_tokens(func1, func2)

    def _calculate_similarity_jaccard_tokens(
        self, func1: CodeFunction, func2: CodeFunction
    ) -> float:
        """Calculate similarity using jaccard_tokens method (current default)."""
        _TOKEN_RE = re.compile(
            r"[A-Za-z_]\w*|\d+|==|!=|<=|>=|[\(\)\[\]\{\}\.,:;\+\-\*/%<>]"
        )

        A, B = (
            set(_TOKEN_RE.findall(func1.body_content)),
            set(_TOKEN_RE.findall(func2.body_content)),
        )

        if not A and not B:
            return 1.0

        similarity_score = len(A & B) / max(1, len(A | B))

        return similarity_score


class ReportGenerator:
    """Generates reports for duplicate logic analysis."""

    def __init__(self):
        self.console = Console()

    def generate_github_comment(self, matches: List[DuplicateMatch]) -> str:
        """Generate a GitHub PR comment with duplicate logic findings."""
        if not matches:
            return ""

        comment = "## 🔍 Duplicate Logic Detection\n\n"
        comment += "The following functions in your PR may recreate logic that already exists:\n\n"

        for i, match in enumerate(matches[:5], 1):
            comment += f"**New Function:** `{match.new_function.name}` in `{match.new_function.file_path}`\n"
            comment += f"**Similar to:** `{match.existing_function.name}` in `{match.existing_function.file_path}`\n"
            comment += f"**Similarity:** {match.similarity_score:.1%}\n"

        comment += "<details>\n<summary>ℹ️ About this check</summary>\n\n"
        comment += "This automated analysis compares new functions against the existing codebase\n"
        comment += "Please review these matches to avoid code duplication and improve maintainability.\n"
        comment += "</details>"

        return comment

    def generate_json_report(self, matches: List[DuplicateMatch]) -> Dict[str, Any]:
        """Generate a JSON report of all findings."""
        return {
            "summary": {
                "total_matches": len(matches),
            },
            "matches": [asdict(match) for match in matches],
        }

    def print_console_report(self, matches: List[DuplicateMatch]):
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
            table.add_row(
                f"{match.new_function.name}\n{match.new_function.file_path}",
                f"{match.existing_function.name}\n{match.existing_function.file_path}",
                f"{match.similarity_score:.1%}",
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

        detector = DuplicateLogicDetector(args.repository_path)

        matches = detector.analyze_pr_changes(
            changed_files, args.base_sha, args.head_sha
        )

        report_gen = ReportGenerator()

        if args.output_format == "console":
            report_gen.print_console_report(matches)
        elif args.output_format == "github-actions":
            if matches:
                with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                    f.write("duplicates_found=true\n")
                    f.write(f"match_count={len(matches)}\n")

                comment = report_gen.generate_github_comment(matches)
                with open("duplicate-logic-report.md", "w") as f:
                    f.write(comment)

            else:
                with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                    f.write("duplicates_found=false\n")
                    f.write("match_count=0\n")
                console.print("[green]No significant duplicates found[/green]")

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
