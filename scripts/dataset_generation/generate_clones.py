import argparse
import ast
import os
import random
import sys
from typing import List, Optional, Tuple

import openai

OPNEAIAPIKEY = ""


def extract_function_names_from_str(source: str) -> List[str]:
    """
    Extracts a list of top-level function names from a Python source string.
    """
    tree = ast.parse(source)
    return [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]


def extract_function_names(module_path: str) -> List[str]:
    """
    Extracts a list of top-level function names from a Python module file.
    """
    with open(module_path, "r", encoding="utf-8") as f:
        source = f.read()
    return extract_function_names_from_str(source)


def extract_function_source_from_str(source: str, function_name: str) -> Optional[str]:
    """
    Extract the source code for a top-level function with the given name from a source string.
    Returns the function source code as a string, or None if not found.
    """
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            lines = source.splitlines()
            fn_start = node.lineno - 1
            fn_end = fn_start
            for i in range(fn_start + 1, len(lines)):
                if lines[i].lstrip().startswith("def ") or lines[i].lstrip().startswith("class "):
                    break
                fn_end = i
            return "\n".join(lines[fn_start : fn_end + 1])
    return None


def extract_function_source(module_path: str, function_name: str) -> Optional[str]:
    """
    Extract source of a top-level function from a module by its name.
    """
    with open(module_path, "r", encoding="utf-8") as f:
        source = f.read()
    return extract_function_source_from_str(source, function_name)


def select_random_modules_with_functions(
    source_folders: List[str], n_modules: int, seed: Optional[int] = None
) -> List[str]:
    """
    Recursively selects n_modules Python files that contain top-level functions randomly 
    from the given folders (including all subfolders), using the specified seed. 
    Returns a list of module file paths.
    
    Args:
        source_folders: List of folder paths to search for Python files
        n_modules: Maximum number of modules to select
        seed: Random seed for reproducible results
        
    Returns:
        List of selected Python file paths that contain top-level functions
    """
    # First, collect all files that have top-level functions
    files_with_functions: List[str] = []
    for source_folder in source_folders:
        for root, _, files in os.walk(source_folder):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path):
                        # Check if this file has top-level functions
                        function_names = extract_function_names(file_path)
                        if function_names:
                            files_with_functions.append(file_path)
    
    # Then randomly select from those files
    rng = random.Random(seed)
    rng.shuffle(files_with_functions)
    return files_with_functions[:n_modules]


def choose_random_method_from_module(module_path: str, seed: Optional[int] = None) -> Optional[str]:
    """
    Chooses a random top-level function name from a Python module file, using the given seed.
    Returns the function name or None if none found.
    """
    fnames = extract_function_names(module_path)
    if not fnames:
        return None
    rng = random.Random(seed)
    return rng.choice(fnames)


def create_multiple_clones_with_gpt_from_source(
    function_source: str, 
    n_clones: int, 
    openai_api_key: str, 
    gpt_model: str = "gpt-4-turbo"
) -> List[str]:
    """
    Given a string with function code, asks OpenAI GPT to create multiple distinct clones 
    with different implementations in a single API call.
    
    Args:
        function_source: The original function source code
        n_clones: Number of distinct clones to generate
        openai_api_key: OpenAI API key
        gpt_model: GPT model to use
    
    Returns:
        List of clone function source codes (may be fewer than n_clones if parsing fails)
    """
    if not function_source or n_clones <= 0:
        return []

    prompt = (
        f"Given the following Python function:\n\n"
        f"{function_source}\n\n"
        f"Create {n_clones} distinct Python functions that accomplish the same task as the original function. "
        f"Each clone must:\n"
        f"1. Have the same purpose and input/output behavior as the original\n"
        f"2. Use a different implementation approach (different algorithms, logic flow, or data structures)\n"
        f"3. Use different variable names and code structure\n"
        f"4. Be completely distinct from the original function and from each other\n"
        f"5. Have a unique but descriptive function name that reflects the original purpose\n\n"
        f"6. Do not include imports inside the method's body\n\n"
        f"Please output exactly {n_clones} complete function definitions, separated by blank lines. "
        f"Do not include any explanations, comments, or markdown formatting - just the function code."
    )
    
    client = openai.OpenAI(api_key=openai_api_key)
    try:
        response = client.chat.completions.create(
            model=gpt_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert Python programmer specializing in creating functionally equivalent but structurally distinct code implementations.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.8,  # Higher temperature for more diversity
            # max_tokens=2048,  # More tokens to accommodate multiple functions
            n=1,
        )
        
        content = response.choices[0].message.content
        if not content:
            return []
            
        # Clean up markdown if present
        raw_content = content.strip()
        if raw_content.startswith("```"):
            lines = raw_content.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            raw_content = "\n".join(lines).strip()
        
        # Parse the response to extract individual functions
        return parse_multiple_functions_from_response(raw_content)
        
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return []


def parse_multiple_functions_from_response(response_text: str) -> List[str]:
    """
    Parse multiple function definitions from a single LLM response.
    
    Args:
        response_text: Raw text response containing multiple function definitions
        
    Returns:
        List of individual function source codes
    """
    functions = []
    
    try:
        # Try to parse the entire response as Python code
        tree = ast.parse(response_text)
        
        # Extract each function definition
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                # Get the source code for this function
                function_source = ast.get_source_segment(response_text, node)
                if function_source:
                    functions.append(function_source.strip())
                    
    except SyntaxError:
        # If parsing fails, try to split by function definitions manually
        print("Warning: Failed to parse response as valid Python. Attempting manual parsing...")
        functions = parse_functions_manually(response_text)
    
    return functions


def parse_functions_manually(text: str) -> List[str]:
    """
    Manually parse function definitions from text when AST parsing fails.
    
    Args:
        text: Raw text containing function definitions
        
    Returns:
        List of individual function source codes
    """
    functions = []
    lines = text.splitlines()
    current_function = []
    in_function = False
    base_indent = 0
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines when not in a function
        if not stripped and not in_function:
            continue
            
        # Check if this is the start of a function
        if stripped.startswith("def ") and ":" in stripped:
            # If we were already collecting a function, save it
            if current_function:
                functions.append("\n".join(current_function).strip())
            
            # Start collecting new function
            current_function = [line]
            in_function = True
            base_indent = len(line) - len(line.lstrip())
            continue
        
        if in_function:
            # Check if we're still inside the function
            if stripped:  # Non-empty line
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= base_indent and not line.startswith(' ') and not line.startswith('\t'):
                    # We've reached a new top-level statement, end current function
                    if current_function:
                        functions.append("\n".join(current_function).strip())
                    current_function = []
                    in_function = False
                    
                    # Check if this line starts a new function
                    if stripped.startswith("def ") and ":" in stripped:
                        current_function = [line]
                        in_function = True
                        base_indent = len(line) - len(line.lstrip())
                else:
                    # Still inside the function
                    current_function.append(line)
            else:
                # Empty line inside function
                current_function.append(line)
    
    # Don't forget the last function
    if current_function:
        functions.append("\n".join(current_function).strip())
    
    return functions


def create_clones_dataset_for_methods(
    methods: List[Tuple[str, str]],
    n_clones: int,
    output_folder: str,
    openai_api_key: str,
    gpt_model: str = "gpt-4-turbo",
):
    """
    For a given list of (method_source_str, function_name) tuples, creates a module for each
    in output_folder, each containing the original function plus N clones with different implementations.
    Uses batch generation to create all clones in a single API call per function.
    """
    os.makedirs(output_folder, exist_ok=True)
    for i, (function_source, function_name) in enumerate(methods):
        print(f"Generating {n_clones} clones for method '{function_name}' (method {i + 1}/{len(methods)})...")
        
        all_functions = []
        # Add the original
        all_functions.append(function_source)
        
        # Generate all clones in a single API call
        clone_codes = create_multiple_clones_with_gpt_from_source(
            function_source, n_clones, openai_api_key, gpt_model=gpt_model
        )
        
        if not clone_codes:
            print(f"WARNING: Failed to generate any clones for {function_name}")
        elif len(clone_codes) < n_clones:
            print(f"WARNING: Only generated {len(clone_codes)} out of {n_clones} requested clones for {function_name}")
        else:
            print(f"Successfully generated {len(clone_codes)} clones for {function_name}")
        
        # Process each generated clone
        for ci, clone_code in enumerate(clone_codes):
            try:
                # Validate that the clone is valid Python code
                ast.parse(clone_code)
                all_functions.append(clone_code)
                
            except SyntaxError as e:
                print(f"WARNING: Clone {ci + 1} for {function_name} has syntax errors: {e}")
                print(f"Problematic code:\n{clone_code}")
                continue
        
        # Build module source string
        module_code = "\n\n".join(all_functions) + "\n"
        
        # Save to file
        module_fname = f"{function_name}_dataset.py"
        module_fpath = os.path.join(output_folder, module_fname)
        with open(module_fpath, "w", encoding="utf-8") as fout:
            fout.write(module_code)
        
        actual_clones = len(all_functions) - 1  # Subtract 1 for the original function
        print(f"Written dataset module: {module_fpath} (1 original + {actual_clones} clones)")


def main():
    """Main function to handle command-line arguments and execute clone generation."""
    parser = argparse.ArgumentParser(
        description="Generate function clones from Python source code (Step 1 of 2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run generate-clones --source-code "./src/shared/validators" --dest-folder="clones_output" --n-clones=3 --n-modules=10
  uv run generate-clones --source-code "./src" "./lib" --dest-folder="generated_clones" --n-clones=2 --seed=42 --verbose
  
After generating clones, manually review the generated files in the output folder, then use:
  uv run build-dataset --clones-folder="clones_output" --dataset-name="functions_clone_pairs.json" --clone-ratio=0.5
        """,
    )

    # Required arguments
    parser.add_argument(
        "--source-code", 
        required=True, 
        nargs='+',
        help="Path(s) to folder(s) containing Python source code files. Multiple folders can be specified."
    )
    parser.add_argument(
        "--dest-folder", required=True, help="Destination folder for generated clone files"
    )

    # Optional arguments
    parser.add_argument(
        "--n-clones",
        type=int,
        default=2,
        help="Number of clones to generate per function (default: 2)",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducible results (default: 42)"
    )
    parser.add_argument(
        "--model",
        default="gpt-4-turbo",
        help="OpenAI model to use for generating clones (default: gpt-4-turbo)",
    )
    parser.add_argument(
        "--api-key", default=OPNEAIAPIKEY, help="OpenAI API key (default: uses hardcoded key)"
    )
    parser.add_argument(
        "--n-modules",
        type=int,
        default=None,
        help="Number of random modules to select (default: use all modules)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually creating files",
    )

    args = parser.parse_args()

    # Validate arguments
    for folder in args.source_code:
        if not os.path.exists(folder):
            print(f"Error: Source code folder '{folder}' does not exist")
            sys.exit(1)
        if not os.path.isdir(folder):
            print(f"Error: '{folder}' is not a directory")
            sys.exit(1)

    if args.n_clones < 1:
        print("Error: --n-clones must be at least 1")
        sys.exit(1)

    if args.verbose:
        print(f"Source code folders: {', '.join(args.source_code)}")
        print(f"Destination folder: {args.dest_folder}")
        print(f"Number of clones: {args.n_clones}")
        print(f"Seed: {args.seed}")
        print(f"Model: {args.model}")
        print(f"Number of modules: {args.n_modules if args.n_modules else 'all'}")

    if args.dry_run:
        print("DRY RUN: Would generate clones with the above parameters")
        return

    try:
        # Create destination folder
        os.makedirs(args.dest_folder, exist_ok=True)

        # Select modules
        if args.n_modules:
            selected_modules = select_random_modules_with_functions(args.source_code, args.n_modules, args.seed)
        else:
            # Use all Python files from all source folders
            selected_modules = []
            for source_folder in args.source_code:
                for root, _, files in os.walk(source_folder):
                    for file in files:
                        if file.endswith(".py"):
                            file_path = os.path.join(root, file)
                            if os.path.isfile(file_path):
                                # Check if this file has top-level functions
                                function_names = extract_function_names(file_path)
                                if function_names:
                                    selected_modules.append(file_path)

        if not selected_modules:
            print("Error: No Python files found in source code folders")
            sys.exit(1)

        if args.verbose:
            print(f"Selected {len(selected_modules)} modules")

        # Extract methods to clone
        methods_to_clone = []
        for mod in selected_modules:
            func_name = choose_random_method_from_module(mod, args.seed)
            if func_name:
                method_source = extract_function_source(mod, func_name)
                if method_source:
                    methods_to_clone.append((method_source, func_name))
                    if args.verbose:
                        print(f"Selected function '{func_name}' from {os.path.basename(mod)}")

        if not methods_to_clone:
            print("Error: No functions found to clone")
            sys.exit(1)

        if args.verbose:
            print(f"Found {len(methods_to_clone)} functions to clone")

        # Create clones dataset
        create_clones_dataset_for_methods(
            methods_to_clone, args.n_clones, args.dest_folder, args.api_key, gpt_model=args.model
        )

        print("Clone generation completed successfully!")
        print(f"Generated files in: {args.dest_folder}")
        print(f"Generated {len(methods_to_clone)} modules with clones")
        print("\nNext steps:")
        print(f"1. Review the generated clone files in '{args.dest_folder}'")
        print("2. Remove or fix any problematic clones manually")
        print("3. Run: uv run build-dataset --clones-folder=\"{args.dest_folder}\" --dataset-name=\"your_dataset.json\"")

    except Exception as e:
        print(f"Error generating clones: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()