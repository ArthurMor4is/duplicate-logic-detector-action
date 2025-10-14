"""
Report generation module for duplicate logic detection results.

This module provides different output formats for duplicate logic detection results,
including console output, GitHub PR comments, and JSON reports.
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from rich.console import Console
from rich.table import Table

from .models import DuplicateMatch


class ReportGenerator(ABC):
    """Abstract base class for report generators."""

    @abstractmethod
    def generate(self, matches: List[DuplicateMatch]) -> str:
        """Generate a report from duplicate matches."""
        pass


class ConsoleReportGenerator(ReportGenerator):
    """Generates formatted console reports using Rich."""

    def __init__(self, console: Console = None):
        """
        Initialize the console report generator.
        
        Args:
            console: Rich console instance. If None, creates a new one.
        """
        self.console = console or Console()

    def generate(self, matches: List[DuplicateMatch]) -> str:
        """Generate and print a console report."""
        if not matches:
            self.console.print("[green]✅ No duplicate logic detected![/green]")
            return "No duplicates found"

        table = Table(title="Duplicate Logic Detection Results")
        table.add_column("New Function", style="cyan", no_wrap=False)
        table.add_column("Existing Function", style="magenta", no_wrap=False)
        table.add_column("Similarity", style="yellow", justify="center")
        table.add_column("Confidence", style="green", justify="center")

        # Show top 10 matches
        for match in matches[:10]:
            table.add_row(
                f"{match.new_function.name}\n{match.new_function.file_path}",
                f"{match.existing_function.name}\n{match.existing_function.file_path}",
                f"{match.similarity_score:.1%}",
                match.confidence_level,
            )

        self.console.print(table)

        # Summary
        total_matches = len(matches)
        high_confidence = len([m for m in matches if m.is_high_confidence])
        
        self.console.print(f"\n[bold]Summary:[/bold]")
        self.console.print(f"  Total matches: {total_matches}")
        self.console.print(f"  High confidence: {high_confidence}")
        
        return f"Found {total_matches} matches ({high_confidence} high confidence)"

    def print_detailed_match(self, match: DuplicateMatch) -> None:
        """Print detailed information about a specific match."""
        self.console.print(f"\n[bold cyan]Match Details[/bold cyan]")
        self.console.print(f"Similarity Score: {match.similarity_score:.1%}")
        self.console.print(f"Confidence: {match.confidence_level}")
        
        self.console.print(f"\n[bold]New Function:[/bold]")
        self.console.print(f"  Name: {match.new_function.name}")
        self.console.print(f"  File: {match.new_function.file_path}")
        self.console.print(f"  Lines: {match.new_function.line_start}-{match.new_function.line_end}")
        
        self.console.print(f"\n[bold]Existing Function:[/bold]")
        self.console.print(f"  Name: {match.existing_function.name}")
        self.console.print(f"  File: {match.existing_function.file_path}")
        self.console.print(f"  Lines: {match.existing_function.line_start}-{match.existing_function.line_end}")


class GitHubCommentGenerator(ReportGenerator):
    """Generates GitHub PR comment reports."""

    def generate(self, matches: List[DuplicateMatch]) -> str:
        """Generate a GitHub PR comment with duplicate logic findings."""
        if not matches:
            return ""

        comment = "## 🔍 Duplicate Logic Detection\n\n"
        comment += "The following functions in your PR may recreate logic that already exists:\n\n"

        # Show top 5 matches in the comment to keep it concise
        for i, match in enumerate(matches[:5], 1):
            comment += f"### Match {i}: {match.confidence_level} Confidence\n"
            comment += f"**New Function:** `{match.new_function.name}` in `{match.new_function.file_path}`\n"
            comment += f"**Similar to:** `{match.existing_function.name}` in `{match.existing_function.file_path}`\n"
            comment += f"**Similarity:** {match.similarity_score:.1%}\n\n"

        # Add summary if there are more matches
        total_matches = len(matches)
        if total_matches > 5:
            comment += f"*... and {total_matches - 5} more matches. Check the full report for details.*\n\n"

        # Add information section
        comment += "<details>\n<summary>ℹ️ About this check</summary>\n\n"
        comment += "This automated analysis compares new functions against the existing codebase "
        comment += "to identify potential code duplication.\n\n"
        comment += "**Confidence Levels:**\n"
        comment += "- **High** (≥80%): Very likely duplicate, consider refactoring\n"
        comment += "- **Medium** (60-79%): Potential duplicate, review recommended\n"
        comment += "- **Low** (40-59%): Some similarity detected, may be coincidental\n\n"
        comment += "Please review these matches to avoid code duplication and improve maintainability.\n"
        comment += "</details>"

        return comment


class JSONReportGenerator(ReportGenerator):
    """Generates JSON reports for programmatic consumption."""

    def generate(self, matches: List[DuplicateMatch]) -> str:
        """Generate a JSON report of all findings."""
        report_data = self._create_report_dict(matches)
        return json.dumps(report_data, indent=2)

    def _create_report_dict(self, matches: List[DuplicateMatch]) -> Dict[str, Any]:
        """Create a dictionary representation of the report."""
        high_confidence = [m for m in matches if m.is_high_confidence]
        
        return {
            "summary": {
                "total_matches": len(matches),
                "high_confidence_matches": len(high_confidence),
                "analysis_complete": True,
            },
            "matches": [match.to_dict() for match in matches],
            "statistics": {
                "confidence_distribution": self._get_confidence_distribution(matches),
                "avg_similarity_score": self._get_average_similarity(matches),
            }
        }

    def _get_confidence_distribution(self, matches: List[DuplicateMatch]) -> Dict[str, int]:
        """Get distribution of confidence levels."""
        distribution = {"High": 0, "Medium": 0, "Low": 0, "Very Low": 0}
        for match in matches:
            distribution[match.confidence_level] += 1
        return distribution

    def _get_average_similarity(self, matches: List[DuplicateMatch]) -> float:
        """Calculate average similarity score."""
        if not matches:
            return 0.0
        return sum(match.similarity_score for match in matches) / len(matches)


class MarkdownReportGenerator(ReportGenerator):
    """Generates detailed Markdown reports."""

    def generate(self, matches: List[DuplicateMatch]) -> str:
        """Generate a detailed Markdown report."""
        if not matches:
            return "# Duplicate Logic Detection Report\n\n✅ No duplicate logic detected!"

        report = "# Duplicate Logic Detection Report\n\n"
        
        # Summary section
        total_matches = len(matches)
        high_confidence = len([m for m in matches if m.is_high_confidence])
        
        report += f"## Summary\n\n"
        report += f"- **Total matches found:** {total_matches}\n"
        report += f"- **High confidence matches:** {high_confidence}\n"
        report += f"- **Analysis date:** {self._get_current_date()}\n\n"

        # High confidence matches first
        if high_confidence > 0:
            report += "## High Confidence Matches\n\n"
            for i, match in enumerate([m for m in matches if m.is_high_confidence], 1):
                report += self._format_match_markdown(match, i)

        # Other matches
        other_matches = [m for m in matches if not m.is_high_confidence]
        if other_matches:
            report += "## Other Potential Matches\n\n"
            for i, match in enumerate(other_matches, high_confidence + 1):
                report += self._format_match_markdown(match, i)

        return report

    def _format_match_markdown(self, match: DuplicateMatch, index: int) -> str:
        """Format a single match as Markdown."""
        md = f"### Match {index}: {match.confidence_level} Confidence\n\n"
        md += f"**Similarity Score:** {match.similarity_score:.1%}\n\n"
        
        md += f"**New Function:**\n"
        md += f"- Name: `{match.new_function.name}`\n"
        md += f"- File: `{match.new_function.file_path}`\n"
        md += f"- Lines: {match.new_function.line_start}-{match.new_function.line_end}\n\n"
        
        md += f"**Existing Function:**\n"
        md += f"- Name: `{match.existing_function.name}`\n"
        md += f"- File: `{match.existing_function.file_path}`\n"
        md += f"- Lines: {match.existing_function.line_start}-{match.existing_function.line_end}\n\n"
        
        md += "---\n\n"
        return md

    def _get_current_date(self) -> str:
        """Get current date as string."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class MultiFormatReporter:
    """
    A unified reporter that can generate multiple output formats.
    
    This class provides a convenient interface for generating reports
    in different formats from the same duplicate detection results.
    """

    def __init__(self, console: Console = None):
        """
        Initialize the multi-format reporter.
        
        Args:
            console: Rich console instance for console output
        """
        self.console = console or Console()
        self._generators = {
            "console": ConsoleReportGenerator(self.console),
            "github": GitHubCommentGenerator(),
            "json": JSONReportGenerator(),
            "markdown": MarkdownReportGenerator(),
        }

    def generate_report(self, matches: List[DuplicateMatch], format_type: str) -> str:
        """
        Generate a report in the specified format.
        
        Args:
            matches: List of duplicate matches to report
            format_type: Type of report to generate ("console", "github", "json", "markdown")
            
        Returns:
            Generated report as a string
            
        Raises:
            ValueError: If format_type is not supported
        """
        if format_type not in self._generators:
            available = ", ".join(self._generators.keys())
            raise ValueError(f"Unsupported format '{format_type}'. Available: {available}")

        generator = self._generators[format_type]
        return generator.generate(matches)

    def get_available_formats(self) -> List[str]:
        """Get list of available report formats."""
        return list(self._generators.keys())

    def print_summary(self, matches: List[DuplicateMatch]) -> None:
        """Print a quick summary to console."""
        if not matches:
            self.console.print("[green]✅ No duplicate logic detected![/green]")
            return

        total = len(matches)
        high_conf = len([m for m in matches if m.is_high_confidence])
        
        self.console.print(f"[yellow]Found {total} potential duplicates ({high_conf} high confidence)[/yellow]")
