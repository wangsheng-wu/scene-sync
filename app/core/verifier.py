"""
Verification and metrics computation for photo matching results
"""

import csv
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class VerificationMetrics:
    """Container for verification metrics"""
    total_results: int
    total_truth: int
    correct_matches: int
    incorrect_matches: int
    missed_matches: int
    extra_matches: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float


class MatchVerifier:
    """
    Handles verification of matching results against ground truth
    """
    
    def __init__(self):
        """Initialize the verifier"""
        pass
    
    def load_csv_to_dict(self, csv_path: str) -> Dict[str, str]:
        """
        Load a CSV file into a dictionary mapping film_photo to scene_photo
        
        Args:
            csv_path: Path to the CSV file
            
        Returns:
            Dictionary mapping film_photo to scene_photo
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        mapping = {}
        try:
            with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Check if required columns exist
                if 'film_photo' not in reader.fieldnames or 'scene_photo' not in reader.fieldnames:
                    raise ValueError(f"CSV must contain 'film_photo' and 'scene_photo' columns. Found: {reader.fieldnames}")
                
                for row in reader:
                    film_photo = row['film_photo'].strip()
                    scene_photo = row['scene_photo'].strip()
                    if film_photo and scene_photo:  # Skip empty rows
                        mapping[film_photo] = scene_photo
        
        except Exception as e:
            raise ValueError(f"Error reading CSV file {csv_path}: {e}")
        
        return mapping
    
    def verify_matches(self, results_csv: str, truth_csv: str) -> Tuple[VerificationMetrics, Dict]:
        """
        Verify matching results against ground truth
        
        Args:
            results_csv: Path to results CSV file
            truth_csv: Path to ground truth CSV file
            
        Returns:
            Tuple of (metrics, detailed_results)
        """
        # Load both CSV files
        results_dict = self.load_csv_to_dict(results_csv)
        truth_dict = self.load_csv_to_dict(truth_csv)
        
        # Initialize counters
        correct_matches = 0
        incorrect_matches = 0
        missed_matches = 0
        extra_matches = 0
        
        # Track detailed results for reporting
        detailed_results = {
            'correct': [],
            'incorrect': [],
            'missed': [],
            'extra': []
        }
        
        # Check each film photo in truth
        for film_photo, truth_scene_photo in truth_dict.items():
            if film_photo in results_dict:
                result_scene_photo = results_dict[film_photo]
                if result_scene_photo == truth_scene_photo:
                    correct_matches += 1
                    detailed_results['correct'].append({
                        'film_photo': film_photo,
                        'scene_photo': truth_scene_photo
                    })
                else:
                    incorrect_matches += 1
                    detailed_results['incorrect'].append({
                        'film_photo': film_photo,
                        'truth_scene_photo': truth_scene_photo,
                        'result_scene_photo': result_scene_photo
                    })
            else:
                missed_matches += 1
                detailed_results['missed'].append({
                    'film_photo': film_photo,
                    'scene_photo': truth_scene_photo
                })
        
        # Check for extra matches (in results but not in truth)
        for film_photo in results_dict:
            if film_photo not in truth_dict:
                extra_matches += 1
                detailed_results['extra'].append({
                    'film_photo': film_photo,
                    'scene_photo': results_dict[film_photo]
                })
        
        # Calculate metrics
        total_results = len(results_dict)
        total_truth = len(truth_dict)
        
        # Avoid division by zero
        accuracy = correct_matches / total_truth if total_truth > 0 else 0.0
        precision = correct_matches / total_results if total_results > 0 else 0.0
        recall = correct_matches / total_truth if total_truth > 0 else 0.0
        
        # Calculate F1 score
        if precision + recall > 0:
            f1_score = 2 * (precision * recall) / (precision + recall)
        else:
            f1_score = 0.0
        
        metrics = VerificationMetrics(
            total_results=total_results,
            total_truth=total_truth,
            correct_matches=correct_matches,
            incorrect_matches=incorrect_matches,
            missed_matches=missed_matches,
            extra_matches=extra_matches,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score
        )
        
        return metrics, detailed_results
    
    def print_verification_report(self, metrics: VerificationMetrics, detailed_results: Dict):
        """
        Print a formatted verification report
        
        Args:
            metrics: Verification metrics
            detailed_results: Detailed results for each category
        """
        print("=" * 60)
        print("VERIFICATION REPORT")
        print("=" * 60)
        
        # Summary metrics
        print(f"Total matches in results: {metrics.total_results}")
        print(f"Total matches in truth:   {metrics.total_truth}")
        print()
        
        print("MATCHING ACCURACY:")
        print(f"  Correct matches:    {metrics.correct_matches}")
        print(f"  Incorrect matches:  {metrics.incorrect_matches}")
        print(f"  Missed matches:     {metrics.missed_matches}")
        print(f"  Extra matches:      {metrics.extra_matches}")
        print()
        
        print("METRICS:")
        print(f"  Accuracy:  {metrics.accuracy:.3f} ({metrics.accuracy*100:.1f}%)")
        print(f"  Precision: {metrics.precision:.3f} ({metrics.precision*100:.1f}%)")
        print(f"  Recall:    {metrics.recall:.3f} ({metrics.recall*100:.1f}%)")
        print(f"  F1 Score:  {metrics.f1_score:.3f}")
        print()
        
        # Detailed results
        if detailed_results['incorrect']:
            print("INCORRECT MATCHES:")
            for item in detailed_results['incorrect']:
                print(f"  {item['film_photo']} -> {item['result_scene_photo']} (should be {item['truth_scene_photo']})")
            print()
        
        if detailed_results['missed']:
            print("MISSED MATCHES:")
            for item in detailed_results['missed']:
                print(f"  {item['film_photo']} -> {item['scene_photo']} (not found in results)")
            print()
        
        if detailed_results['extra']:
            print("EXTRA MATCHES:")
            for item in detailed_results['extra']:
                print(f"  {item['film_photo']} -> {item['scene_photo']} (not in truth)")
            print()
        
        print("=" * 60) 