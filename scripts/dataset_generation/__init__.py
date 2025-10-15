"""
Dataset Generation Module for Duplicate Logic Detector

This module provides tools for generating datasets of function clones
to help users test and choose strategies for duplicate detection.

The dataset generation process consists of two main steps:
1. Clone Generation: Create function clones using LLM (generate_clones.py)
2. Dataset Building: Build balanced datasets from generated clones (build_dataset.py)
"""

from .generate_clones import (
    create_clones_dataset_for_methods,
    create_multiple_clones_with_gpt_from_source,
    extract_function_names,
    extract_function_source,
    select_random_modules_with_functions,
    choose_random_method_from_module,
)

from .build_dataset import (
    build_function_clone_dataset,
    extract_function_name_from_source,
)

__version__ = "1.0.0"
__all__ = [
    "create_clones_dataset_for_methods",
    "create_multiple_clones_with_gpt_from_source",
    "extract_function_names",
    "extract_function_source", 
    "select_random_modules_with_functions",
    "choose_random_method_from_module",
    "build_function_clone_dataset",
    "extract_function_name_from_source",
]
