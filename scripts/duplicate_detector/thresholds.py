"""
Threshold configuration module for the duplicate logic detector.

This module handles the parsing and validation of similarity thresholds,
supporting both global thresholds and per-folder thresholds.
"""

import json
from typing import Dict, Optional, Any
from rich.console import Console


class ThresholdConfig:
    """
    Configuration class for similarity thresholds.
    
    Supports both global thresholds and folder-specific thresholds.
    Folder-specific thresholds override the global threshold for functions
    located in specific directories.
    """
    
    def __init__(
        self,
        global_threshold: float = 0.7,
        folder_thresholds: Optional[Dict[str, float]] = None,
        console: Optional[Console] = None,
    ):
        """
        Initialize threshold configuration.
        
        Args:
            global_threshold: Global similarity threshold (0.0-1.0)
            folder_thresholds: Per-folder thresholds as dict (folder_path -> threshold)
            console: Rich console for output
        """
        self.global_threshold = global_threshold
        self.folder_thresholds = folder_thresholds or {}
        self.console = console or Console()
        
        # Validate thresholds
        self._validate_thresholds()
    
    def _validate_thresholds(self) -> None:
        """Validate threshold values."""
        if not 0.0 <= self.global_threshold <= 1.0:
            raise ValueError(f"Global threshold must be between 0.0 and 1.0, got {self.global_threshold}")
        
        for folder, threshold in self.folder_thresholds.items():
            if not 0.0 <= threshold <= 1.0:
                raise ValueError(f"Threshold for folder '{folder}' must be between 0.0 and 1.0, got {threshold}")
    
    def should_report_match(self, similarity_score: float, file_path: str) -> bool:
        """
        Determine if a match should be reported based on thresholds.
        
        Args:
            similarity_score: Calculated similarity score
            file_path: Path to the file containing the function
            
        Returns:
            True if match should be reported, False otherwise
        """
        # Find the most specific folder threshold that matches the file path
        threshold = self.global_threshold
        longest_match = ""
        
        for folder_path, folder_threshold in self.folder_thresholds.items():
            # Normalize paths for comparison
            normalized_folder = folder_path.strip("/")
            normalized_file = file_path.strip("/")
            
            # Check if the file is in this folder or its subdirectories
            if normalized_file.startswith(normalized_folder + "/") or normalized_file.startswith(normalized_folder):
                # Use the most specific (longest) matching folder path
                if len(normalized_folder) > len(longest_match):
                    threshold = folder_threshold
                    longest_match = normalized_folder
        
        return similarity_score >= threshold
    
    def get_threshold_for_file(self, file_path: str) -> float:
        """
        Get the effective threshold for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Effective threshold for the file
        """
        threshold = self.global_threshold
        longest_match = ""
        
        for folder_path, folder_threshold in self.folder_thresholds.items():
            # Normalize paths for comparison
            normalized_folder = folder_path.strip("/")
            normalized_file = file_path.strip("/")
            
            # Check if the file is in this folder or its subdirectories
            if normalized_file.startswith(normalized_folder + "/") or normalized_file.startswith(normalized_folder):
                # Use the most specific (longest) matching folder path
                if len(normalized_folder) > len(longest_match):
                    threshold = folder_threshold
                    longest_match = normalized_folder
        
        return threshold
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get configuration summary for reporting."""
        return {
            "global_threshold": self.global_threshold,
            "folder_thresholds": self.folder_thresholds,
        }
    
    def print_configuration(self) -> None:
        """Print threshold configuration to console."""
        self.console.print("\n[bold blue]📊 Threshold Configuration[/bold blue]")
        self.console.print(f"  Global Threshold: [green]{self.global_threshold}[/green]")
        
        if self.folder_thresholds:
            self.console.print("  Folder-Specific Thresholds:")
            for folder, threshold in self.folder_thresholds.items():
                self.console.print(f"    {folder}: [green]{threshold}[/green]")
        else:
            self.console.print("  No folder-specific thresholds configured")
    
    @classmethod
    def from_strings(
        cls,
        global_threshold_str: Optional[str] = None,
        folder_thresholds_json: Optional[str] = None,
        console: Optional[Console] = None,
    ) -> "ThresholdConfig":
        """
        Create ThresholdConfig from string inputs (useful for CLI/environment variables).
        
        Args:
            global_threshold_str: Global threshold as string
            folder_thresholds_json: Folder thresholds as JSON string
            console: Rich console for output
            
        Returns:
            ThresholdConfig instance
            
        Raises:
            ValueError: If inputs are invalid
        """
        console = console or Console()
        
        # Parse global threshold
        global_threshold = None
        if global_threshold_str:
            try:
                global_threshold = float(global_threshold_str)
            except ValueError:
                raise ValueError(f"Invalid global threshold: '{global_threshold_str}'. Must be a number.")
        
        # Parse folder thresholds
        folder_thresholds = {}
        if folder_thresholds_json and folder_thresholds_json.strip() != "{}":
            try:
                folder_thresholds = json.loads(folder_thresholds_json)
                if not isinstance(folder_thresholds, dict):
                    raise ValueError("Folder thresholds must be a JSON object")
                
                # Validate that all values are numbers
                for folder, threshold in folder_thresholds.items():
                    if not isinstance(threshold, (int, float)):
                        raise ValueError(f"Threshold for folder '{folder}' must be a number, got {type(threshold).__name__}")
                    
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid folder thresholds JSON: {e}")
        
        # Create config with defaults
        return cls(
            global_threshold=global_threshold if global_threshold is not None else 0.7,
            folder_thresholds=folder_thresholds,
            console=console,
        )


def create_threshold_config_from_env(console: Optional[Console] = None) -> ThresholdConfig:
    """
    Create ThresholdConfig from environment variables.
    
    Reads from:
    - GLOBAL_THRESHOLD: Global threshold value
    - FOLDER_THRESHOLDS: JSON string of folder-specific thresholds
    
    Args:
        console: Rich console for output
        
    Returns:
        ThresholdConfig instance
    """
    import os
    
    global_threshold_str = os.getenv("GLOBAL_THRESHOLD")
    folder_thresholds_json = os.getenv("FOLDER_THRESHOLDS", "{}")
    
    return ThresholdConfig.from_strings(
        global_threshold_str, folder_thresholds_json, console
    )