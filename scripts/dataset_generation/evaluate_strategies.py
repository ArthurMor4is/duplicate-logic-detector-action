#!/usr/bin/env python3
"""
Similarity Strategy Evaluation Tool

This script evaluates different similarity strategies on a dataset of function pairs
to determine the best approach for duplicate detection based on various metrics.

Based on the experimental analysis from the research notebooks.
"""

import argparse
import json
import math
import os
import re
import sys
from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
    auc,
)


class SimilarityEvaluator:
    """Evaluates different similarity strategies on a dataset."""
    
    def __init__(self, dataset_path: str):
        """
        Initialize the evaluator with a dataset.
        
        Args:
            dataset_path: Path to the JSON dataset file
        """
        self.dataset_path = dataset_path
        self.df = None
        self.results = {}
        self._load_dataset()
        self._prepare_data()
    
    def _load_dataset(self):
        """Load the dataset from JSON file."""
        try:
            with open(self.dataset_path, 'r') as f:
                data = json.load(f)
            
            # Handle both list of records and pandas DataFrame format
            if isinstance(data, list):
                self.df = pd.DataFrame(data)
            else:
                self.df = pd.read_json(self.dataset_path)
            
            print(f"✅ Loaded dataset with {len(self.df)} function pairs")
            
            # Validate required columns
            required_cols = ['func1', 'func2', 'clone']
            missing_cols = [col for col in required_cols if col not in self.df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
                
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            sys.exit(1)
    
    def _prepare_data(self):
        """Prepare the data for evaluation."""
        # Ensure clone column is binary
        self.df["label"] = self.df["clone"].astype(int)
        
        # Normalize code (remove comments, abstract literals, etc.)
        self.df["func1_norm"] = self.df["func1"].apply(self._normalize_code)
        self.df["func2_norm"] = self.df["func2"].apply(self._normalize_code)
        
        print(f"✅ Data prepared. Clone ratio: {self.df['label'].mean():.2%}")
    
    def _normalize_code(self, code: str) -> str:
        """
        Normalize code by removing comments and abstracting identifiers/literals.
        Simplified version of the normalization from experiment_3.ipynb
        """
        # Remove comments (simple approach)
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        
        # Abstract string literals
        code = re.sub(r'"[^"]*"', '"STR"', code)
        code = re.sub(r"'[^']*'", "'STR'", code)
        
        # Abstract numeric literals
        code = re.sub(r'\b\d+\b', '0', code)
        
        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code).strip()
        
        return code
    
    def _simple_tokenize(self, text: str) -> List[str]:
        """Simple tokenization for code."""
        token_pattern = r"[A-Za-z_]\w*|\d+|==|!=|<=|>=|[\(\)\[\]\{\}\.,:;\+\-\*/%<>]"
        return re.findall(token_pattern, text)
    
    def _sequence_matcher_similarity(self, a: str, b: str) -> float:
        """Calculate similarity using difflib.SequenceMatcher."""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, a, b).ratio()
    
    def _levenshtein_similarity(self, a: str, b: str) -> float:
        """Calculate normalized Levenshtein similarity."""
        if a == b:
            return 1.0
        
        len_a, len_b = len(a), len(b)
        if len_a == 0 or len_b == 0:
            return 0.0
        
        # Dynamic programming for Levenshtein distance
        prev = list(range(len_b + 1))
        for i in range(1, len_a + 1):
            curr = [i] + [0] * len_b
            ca = a[i - 1]
            for j in range(1, len_b + 1):
                cb = b[j - 1]
                cost = 0 if ca == cb else 1
                curr[j] = min(
                    prev[j] + 1,       # deletion
                    curr[j - 1] + 1,   # insertion
                    prev[j - 1] + cost # substitution
                )
            prev = curr
        
        distance = prev[len_b]
        max_len = max(len_a, len_b)
        return 1.0 - (distance / max_len)
    
    def _jaccard_tokens_similarity(self, a: str, b: str) -> float:
        """Calculate Jaccard similarity based on tokens."""
        tokens_a = set(self._simple_tokenize(a))
        tokens_b = set(self._simple_tokenize(b))
        
        if not tokens_a and not tokens_b:
            return 1.0
        
        intersection = len(tokens_a & tokens_b)
        union = len(tokens_a | tokens_b)
        
        return intersection / max(1, union)
    
    def _calculate_scores(self, method_name: str, similarity_func) -> None:
        """Calculate similarity scores for a given method."""
        print(f"🔄 Calculating scores for {method_name}...")
        
        scores = []
        for idx, row in self.df.iterrows():
            try:
                score = similarity_func(row['func1_norm'], row['func2_norm'])
                # Ensure score is in [0, 1] range
                score = max(0.0, min(1.0, score))
            except Exception as e:
                print(f"Warning: Error calculating {method_name} for row {idx}: {e}")
                score = np.nan
            scores.append(score)
        
        self.df[method_name] = scores
    
    def _evaluate_method(self, method_name: str) -> Dict[str, Any]:
        """Evaluate a single similarity method."""
        # Get scores and labels, removing NaN values
        df_clean = self.df.dropna(subset=[method_name])
        y_true = df_clean["label"].astype(int).values
        y_score = df_clean[method_name].astype(float).values
        
        if len(y_true) == 0:
            return {"error": "No valid scores"}
        
        # Calculate ROC-AUC
        try:
            roc_auc = roc_auc_score(y_true, y_score)
        except Exception:
            roc_auc = np.nan
        
        # Calculate Precision-Recall curve and AUC
        precision, recall, thresholds = precision_recall_curve(y_true, y_score)
        pr_auc = auc(recall, precision)
        
        # Find best F1 score and corresponding threshold
        with np.errstate(divide='ignore', invalid='ignore'):
            f1_scores = 2 * (precision * recall) / (precision + recall)
            f1_scores[np.isnan(f1_scores)] = 0.0
        
        if len(thresholds) > 0:
            best_idx = np.argmax(f1_scores[1:]) + 1  # Skip first element
            best_threshold = thresholds[best_idx - 1]
        else:
            best_idx = int(np.argmax(f1_scores))
            best_threshold = 0.5
        
        best_f1 = float(f1_scores[best_idx])
        
        # Calculate metrics at best F1 threshold
        y_pred = (y_score >= best_threshold).astype(int)
        accuracy = accuracy_score(y_true, y_pred)
        precision_at_best = precision_score(y_true, y_pred, zero_division=0)
        recall_at_best = recall_score(y_true, y_pred, zero_division=0)
        
        return {
            "method": method_name,
            "roc_auc": float(roc_auc) if not np.isnan(roc_auc) else np.nan,
            "pr_auc": float(pr_auc),
            "best_threshold": float(best_threshold),
            "best_f1": float(best_f1),
            "accuracy_at_best_f1": float(accuracy),
            "precision_at_best_f1": float(precision_at_best),
            "recall_at_best_f1": float(recall_at_best),
            "n_samples": len(y_true),
        }
    
    def evaluate_all_strategies(self) -> pd.DataFrame:
        """Evaluate all similarity strategies."""
        print("\n🚀 Starting similarity strategy evaluation...")
        
        # Define similarity methods
        methods = {
            "jaccard_tokens": self._jaccard_tokens_similarity,
            "sequence_matcher": self._sequence_matcher_similarity,
            "levenshtein_norm": self._levenshtein_similarity,
        }
        
        # Calculate scores for each method
        for method_name, similarity_func in methods.items():
            self._calculate_scores(method_name, similarity_func)
        
        # Evaluate each method
        results = []
        for method_name in methods.keys():
            result = self._evaluate_method(method_name)
            results.append(result)
            self.results[method_name] = result
        
        # Create summary DataFrame
        summary_df = pd.DataFrame(results)
        
        # Sort by F1 score (primary), then PR-AUC, then ROC-AUC
        summary_df = summary_df.sort_values(
            by=["best_f1", "pr_auc", "roc_auc"], 
            ascending=False
        ).reset_index(drop=True)
        
        return summary_df
    
    def print_results(self, summary_df: pd.DataFrame) -> None:
        """Print evaluation results in a clean format."""
        print("\n" + "="*80)
        print("📊 SIMILARITY STRATEGY EVALUATION RESULTS")
        print("="*80)
        
        # Print summary table
        print("\n📈 Performance Summary:")
        print("-" * 80)
        
        # Format the DataFrame for better display
        display_df = summary_df.copy()
        
        # Round numeric columns
        numeric_cols = ['roc_auc', 'pr_auc', 'best_threshold', 'best_f1', 
                       'accuracy_at_best_f1', 'precision_at_best_f1', 'recall_at_best_f1']
        for col in numeric_cols:
            if col in display_df.columns:
                display_df[col] = display_df[col].round(4)
        
        # Rename columns for display
        display_df = display_df.rename(columns={
            'method': 'Method',
            'roc_auc': 'ROC-AUC',
            'pr_auc': 'PR-AUC',
            'best_threshold': 'Best Threshold',
            'best_f1': 'F1 Score',
            'accuracy_at_best_f1': 'Accuracy',
            'precision_at_best_f1': 'Precision',
            'recall_at_best_f1': 'Recall',
            'n_samples': 'Samples'
        })
        
        print(display_df.to_string(index=False))
        
        # Highlight the best method
        best_method = summary_df.iloc[0]
        print("\n" + "="*80)
        print(f"🏆 BEST STRATEGY: {best_method['method'].upper()}")
        print("="*80)
        print(f"📊 F1 Score: {best_method['best_f1']:.4f}")
        print(f"📊 ROC-AUC: {best_method['roc_auc']:.4f}")
        print(f"📊 PR-AUC: {best_method['pr_auc']:.4f}")
        print(f"📊 Best Threshold: {best_method['best_threshold']:.4f}")
        print(f"📊 Accuracy: {best_method['accuracy_at_best_f1']:.4f}")
        print(f"📊 Precision: {best_method['precision_at_best_f1']:.4f}")
        print(f"📊 Recall: {best_method['recall_at_best_f1']:.4f}")
        
        # Provide recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 80)
        if best_method['method'] == 'jaccard_tokens':
            print("• Use Jaccard Tokens for balanced speed and accuracy")
            print("• Good for general-purpose duplicate detection")
        elif best_method['method'] == 'levenshtein_norm':
            print("• Use Levenshtein Distance for highest precision")
            print("• Best for catching subtle duplicates")
        elif best_method['method'] == 'sequence_matcher':
            print("• Use Sequence Matcher for structural similarity")
            print("• Good for detecting similar code patterns")
        
        print(f"• Set similarity threshold to {best_method['best_threshold']:.4f}")
        print(f"• Expected to achieve {best_method['best_f1']:.1%} F1 score on similar data")


def main():
    """Main function to handle command-line arguments and execute evaluation."""
    parser = argparse.ArgumentParser(
        description="Evaluate similarity strategies for duplicate code detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run evaluate-strategies --dataset dataset.json
  uv run evaluate-strategies --dataset my_clone_pairs.json --output-csv results.csv
  uv run evaluate-strategies --dataset balanced_dataset.json --verbose
        """,
    )

    # Required arguments
    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to JSON dataset file containing function pairs with 'func1', 'func2', and 'clone' columns"
    )
    
    # Optional arguments
    parser.add_argument(
        "--output-csv",
        help="Path to save detailed results as CSV file"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    try:
        # Validate dataset file exists
        if not os.path.exists(args.dataset):
            print(f"❌ Error: Dataset file '{args.dataset}' not found")
            sys.exit(1)

        if args.verbose:
            print(f"📂 Dataset file: {args.dataset}")
            if args.output_csv:
                print(f"📄 Output CSV: {args.output_csv}")

        # Initialize evaluator
        evaluator = SimilarityEvaluator(args.dataset)
        
        # Run evaluation
        summary_df = evaluator.evaluate_all_strategies()
        
        # Print results
        evaluator.print_results(summary_df)
        
        # Save CSV if requested
        if args.output_csv:
            summary_df.to_csv(args.output_csv, index=False)
            print(f"\n💾 Detailed results saved to: {args.output_csv}")
        
        print(f"\n✅ Evaluation completed successfully!")
        
        # Return the best method name for potential scripting use
        best_method = summary_df.iloc[0]['method']
        print(f"\n🎯 Best method for scripting: {best_method}")

    except KeyboardInterrupt:
        print("\n❌ Evaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during evaluation: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
