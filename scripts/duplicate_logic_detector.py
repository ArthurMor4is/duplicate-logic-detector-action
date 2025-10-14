#!/usr/bin/env python3
"""
Duplicate Logic Detection Tool

This script analyzes code changes in pull requests to detect if new logic
recreates functionality that already exists in the codebase.

This is the main entry point that uses the modular duplicate_detector package.
"""

import argparse
import os
import sys

from rich.console import Console

from duplicate_detector.detector import DuplicateLogicDetector
from duplicate_detector.reporters import MultiFormatReporter


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
        choices=["console", "github-actions", "json", "markdown"],
        default="console",
        help="Output format",
    )
    parser.add_argument("--repository-path", default=".", help="Path to repository")
    parser.add_argument(
        "--similarity-method",
        choices=["jaccard_tokens", "sequence_matcher", "levenshtein_norm"],
        default=os.getenv("SIMILARITY_METHOD", "jaccard_tokens"),
        help="Similarity method to use for duplicate detection (default: jaccard_tokens)"
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.0,
        help="Minimum similarity score to include in results (0.0-1.0)"
    )

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

        # Initialize detector with the specified similarity method
        detector = DuplicateLogicDetector(
            repository_path=args.repository_path,
            similarity_method=args.similarity_method,
            console=console
        )

        # Show configuration
        if args.output_format == "console":
            detector.print_configuration()

        # Analyze changes
        matches = detector.analyze_pr_changes(
            changed_files, 
            args.base_sha, 
            args.head_sha,
            similarity_threshold=args.similarity_threshold
        )

        # Generate reports
        reporter = MultiFormatReporter(console)

        if args.output_format == "console":
            reporter.generate_report(matches, "console")
            
        elif args.output_format == "github-actions":
            # Write GitHub Actions outputs
            if matches:
                with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                    f.write("duplicates_found=true\n")
                    f.write(f"match_count={len(matches)}\n")

                # Generate GitHub comment
                comment = reporter.generate_report(matches, "github")
                with open("duplicate-logic-report.md", "w") as f:
                    f.write(comment)

            else:
                with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                    f.write("duplicates_found=false\n")
                    f.write("match_count=0\n")
                console.print("[green]No significant duplicates found[/green]")

            # Generate JSON report for artifacts
            json_report = reporter.generate_report(matches, "json")
            with open("duplicate-logic-report.json", "w") as f:
                f.write(json_report)

        elif args.output_format == "json":
            json_report = reporter.generate_report(matches, "json")
            print(json_report)
            
        elif args.output_format == "markdown":
            markdown_report = reporter.generate_report(matches, "markdown")
            print(markdown_report)

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
