import argparse
import ast
import json
import os
import random
import sys
from itertools import combinations
from typing import Optional

import pandas as pd


def extract_function_name_from_source(function_source: str) -> Optional[str]:
    """
    Extract the function name from function source code.
    
    Args:
        function_source (str): The source code of the function.
        
    Returns:
        Optional[str]: The function name, or None if parsing fails.
    """
    try:
        tree = ast.parse(function_source)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                return node.name
    except Exception:
        pass
    return None


def build_function_clone_dataset(
    folder_path: str, 
    output_path: str, 
    seed: int,
    format: str = "json", 
    clone_ratio: float = 0.5
) -> None:
    """
    Build a dataset of function pairs from Python modules in the given folder.
    Same-module pairs are marked as clones. Cross-module pairs are non-clone.
    The final dataset is balanced according to the specified clone_ratio.

    Args:
        folder_path (str): Path to folder containing Python modules.
        output_path (str): Path to write output file.
        seed (int): Random seed for reproducible sampling.
        format (str): Output format - 'json', 'parquet', or 'csv' (default: 'json').
        clone_ratio (float): Ratio of true clones in the final dataset (default: 0.5).
                           0.5 means 50% true clones, 50% false clones.
    """

    # Step 1: Collect functions from all modules
    module_functions: dict[str, list[str]] = {}
    for fname in os.listdir(folder_path):
        if fname.endswith(".py"):
            fpath = os.path.join(folder_path, fname)
            with open(fpath, "r", encoding="utf-8") as fin:
                try:
                    src = fin.read()
                    tree = ast.parse(src)
                    functions = []
                    for node in tree.body:
                        if isinstance(node, ast.FunctionDef):
                            function_src = ast.get_source_segment(src, node)
                            if function_src is not None:
                                functions.append(function_src)
                    if functions:
                        module_functions[fname] = functions
                except Exception:
                    # Ignore modules that cannot be parsed
                    continue

    # Step 2: Generate all possible pairs and separate them by type
    true_clone_pairs = []
    false_clone_pairs = []
    modules = list(module_functions.keys())

    # Same-module pairs (clones), no reverse duplicates
    for module_name, functions in module_functions.items():
        if len(functions) > 1:
            for func1, func2 in combinations(functions, 2):
                func1_name = extract_function_name_from_source(func1)
                func2_name = extract_function_name_from_source(func2)
                true_clone_pairs.append({
                    "func1": func1,
                    "func2": func2,
                    "func1_name": func1_name,
                    "func2_name": func2_name,
                    "clone": True,
                    "source_module1": module_name,
                    "source_module2": module_name,
                })
                
    # Cross-module pairs (not clones), also only unique pairs
    for i in range(len(modules)):
        funcs_i = module_functions[modules[i]]
        for j in range(i + 1, len(modules)):
            funcs_j = module_functions[modules[j]]
            for func1 in funcs_i:
                for func2 in funcs_j:
                    func1_name = extract_function_name_from_source(func1)
                    func2_name = extract_function_name_from_source(func2)
                    false_clone_pairs.append({
                        "func1": func1,
                        "func2": func2,
                        "func1_name": func1_name,
                        "func2_name": func2_name,
                        "clone": False,
                        "source_module1": modules[i],
                        "source_module2": modules[j],
                    })

    # Step 3: Balance the dataset according to clone_ratio
    total_true_clones = len(true_clone_pairs)
    total_false_clones = len(false_clone_pairs)
    
    if total_true_clones == 0:
        print("Warning: No true clone pairs found. Dataset will contain only false clones.")
        rows = false_clone_pairs
    elif total_false_clones == 0:
        print("Warning: No false clone pairs found. Dataset will contain only true clones.")
        rows = true_clone_pairs
    else:
        # Calculate how many of each type to include
        if clone_ratio >= 1.0:
            # Use all true clones, no false clones
            selected_true_clones = total_true_clones
            selected_false_clones = 0
        elif clone_ratio <= 0.0:
            # Use all false clones, no true clones
            selected_true_clones = 0
            selected_false_clones = total_false_clones
        else:
            # Calculate balanced sampling
            # If we want clone_ratio of true clones, then:
            # selected_true_clones / (selected_true_clones + selected_false_clones) = clone_ratio
            # This gives us: selected_false_clones = selected_true_clones * (1 - clone_ratio) / clone_ratio
            
            # Strategy: Use all available true clones if possible, then calculate false clones needed
            if total_true_clones <= total_false_clones * clone_ratio / (1 - clone_ratio):
                # We have enough false clones to balance with all true clones
                selected_true_clones = total_true_clones
                selected_false_clones = int(total_true_clones * (1 - clone_ratio) / clone_ratio)
            else:
                # We have more true clones than needed, so we need to sample both
                # Use all false clones and calculate true clones needed
                selected_false_clones = total_false_clones
                selected_true_clones = int(total_false_clones * clone_ratio / (1 - clone_ratio))
        
        # Sample the pairs
        rng = random.Random(seed)  # Use provided seed for reproducibility
        
        if selected_true_clones > 0 and selected_true_clones < total_true_clones:
            selected_true_pairs = rng.sample(true_clone_pairs, selected_true_clones)
        else:
            selected_true_pairs = true_clone_pairs[:selected_true_clones]
            
        if selected_false_clones > 0 and selected_false_clones < total_false_clones:
            selected_false_pairs = rng.sample(false_clone_pairs, selected_false_clones)
        else:
            selected_false_pairs = false_clone_pairs[:selected_false_clones]
        
        # Combine and shuffle
        rows = selected_true_pairs + selected_false_pairs
        rng.shuffle(rows)
        
        # Print statistics
        actual_true_count = len(selected_true_pairs)
        actual_false_count = len(selected_false_pairs)
        total_pairs = actual_true_count + actual_false_count
        actual_ratio = actual_true_count / total_pairs if total_pairs > 0 else 0
        
        print(f"Dataset balance:")
        print(f"  Available: {total_true_clones} true clones, {total_false_clones} false clones")
        print(f"  Selected: {actual_true_count} true clones ({actual_ratio:.1%}), {actual_false_count} false clones ({1-actual_ratio:.1%})")
        print(f"  Total pairs: {total_pairs}")

    # Step 4: Save in the specified format
    if format.lower() == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2, ensure_ascii=False)
    elif format.lower() == "parquet":
        try:
            df = pd.DataFrame(rows)
            df.to_parquet(output_path, index=False)
        except ImportError:
            print("Warning: pyarrow not available, falling back to JSON format")
            json_path = output_path.replace(".parquet", ".json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2, ensure_ascii=False)
    else:  # CSV fallback (not recommended for function code)
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)


def main():
    """Main function to handle command-line arguments and execute dataset building."""
    parser = argparse.ArgumentParser(
        description="Build function clone pairs dataset from generated clone files (Step 2 of 2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run build-dataset --clones-folder="clones_output" --dataset-name="functions_clone_pairs.json"
  uv run build-dataset --clones-folder="generated_clones" --dataset-name="balanced_dataset.json" --clone-ratio=0.3 --format=json
  uv run build-dataset --clones-folder="reviewed_clones" --dataset-name="final_dataset.parquet" --clone-ratio=0.5 --format=parquet --verbose
        """,
    )

    # Required arguments
    parser.add_argument(
        "--clones-folder", 
        required=True, 
        help="Path to folder containing generated clone files (from generate_clones.py)"
    )
    parser.add_argument(
        "--dataset-name",
        required=True,
        help="Name of the output dataset file (e.g., 'functions_clone_pairs.json')",
    )

    # Optional arguments
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducible results (default: 42)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "parquet", "csv"],
        default="json",
        help="Output format for the dataset (default: json). JSON is recommended for function code.",
    )
    parser.add_argument(
        "--clone-ratio",
        type=float,
        default=0.5,
        help="Ratio of true clones in the final dataset (default: 0.5). "
             "0.5 means 50%% true clones and 50%% false clones. "
             "1.0 means only true clones, 0.0 means only false clones.",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Validate arguments
    if not os.path.exists(args.clones_folder):
        print(f"Error: Clones folder '{args.clones_folder}' does not exist")
        sys.exit(1)
    
    if not os.path.isdir(args.clones_folder):
        print(f"Error: '{args.clones_folder}' is not a directory")
        sys.exit(1)

    if args.clone_ratio < 0.0 or args.clone_ratio > 1.0:
        print("Error: --clone-ratio must be between 0.0 and 1.0")
        sys.exit(1)

    # Check if there are any Python files in the clones folder
    py_files = [f for f in os.listdir(args.clones_folder) if f.endswith('.py')]
    if not py_files:
        print(f"Error: No Python files found in clones folder '{args.clones_folder}'")
        sys.exit(1)

    if args.verbose:
        print(f"Clones folder: {args.clones_folder}")
        print(f"Dataset name: {args.dataset_name}")
        print(f"Seed: {args.seed}")
        print(f"Output format: {args.format}")
        print(f"Clone ratio: {args.clone_ratio} ({args.clone_ratio*100:.1f}% true clones)")
        print(f"Found {len(py_files)} Python files to process")

    try:
        # Build function clone pairs dataset
        build_function_clone_dataset(
            args.clones_folder, 
            args.dataset_name, 
            seed=args.seed,
            format=args.format, 
            clone_ratio=args.clone_ratio
        )

        print("Dataset created successfully!")
        print(f"Dataset file: {args.dataset_name}")
        print(f"Format: {args.format}")

    except Exception as e:
        print(f"Error creating dataset: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()