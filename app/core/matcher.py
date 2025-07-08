"""
ORB-based photo matching functionality
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from .utils import (
    get_image_files, 
    load_image_for_matching, 
    get_file_name_from_path,
    calculate_matching_score
)


class PhotoMatcher:
    """
    Handles ORB-based photo matching between film and scene photos
    """
    
    def __init__(self, max_features: int = 500, good_match_percent: float = 0.15, ratio_threshold: float = 0.75):
        """
        Initialize the photo matcher
        
        Args:
            max_features: Maximum number of features to detect
            good_match_percent: Percentage of good matches threshold
            ratio_threshold: Threshold for ratio test (Lowe's ratio test)
        """
        self.max_features = max_features
        self.good_match_percent = good_match_percent
        self.ratio_threshold = ratio_threshold
        
        # Initialize ORB detector
        self.orb = cv2.ORB_create(max_features)
        
        # Initialize feature matcher (use k=2 for ratio test)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    
    def detect_features(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Detect ORB features in an image
        
        Args:
            image: Grayscale image
            
        Returns:
            Tuple of (keypoints, descriptors)
        """
        keypoints, descriptors = self.orb.detectAndCompute(image, None)
        return keypoints, descriptors
    
    def match_features_with_ratio_test(self, desc1: np.ndarray, desc2: np.ndarray) -> List:
        """
        Match features between two images using ratio test
        
        Args:
            desc1: Descriptors from first image
            desc2: Descriptors from second image
            
        Returns:
            List of good matches that pass ratio test
        """
        if desc1 is None or desc2 is None:
            return []
        
        # Use k=2 to get the two best matches for each descriptor
        matches = self.matcher.knnMatch(desc1, desc2, k=2)
        
        good_matches = []
        for match_pair in matches:
            # Apply ratio test (Lowe's ratio test)
            if len(match_pair) == 2:
                best_match, second_best_match = match_pair
                # Check if the best match is significantly better than the second best
                if best_match.distance < self.ratio_threshold * second_best_match.distance:
                    good_matches.append(best_match)
        
        return good_matches
    
    def match_features(self, desc1: np.ndarray, desc2: np.ndarray) -> List:
        """
        Match features between two images (legacy method for backward compatibility)
        
        Args:
            desc1: Descriptors from first image
            desc2: Descriptors from second image
            
        Returns:
            List of matches
        """
        if desc1 is None or desc2 is None:
            return []
        
        matches = self.matcher.match(desc1, desc2)
        matches = sorted(matches, key=lambda x: x.distance)
        
        return matches
    
    def calculate_similarity_with_ratio_test(self, matches: List) -> float:
        """
        Calculate similarity score based on ratio-tested matches
        
        Args:
            matches: List of good matches that passed ratio test
            
        Returns:
            Similarity score between 0 and 1
        """
        if not matches:
            return 0.0
        
        # Calculate score based on number of good matches and their quality
        num_matches = len(matches)
        if num_matches == 0:
            return 0.0
        
        # Calculate average distance of good matches
        avg_distance = sum(m.distance for m in matches) / num_matches
        
        # Normalize distance (lower is better) and factor in number of matches
        distance_score = max(0, 1 - (avg_distance / 100))
        match_count_score = min(1.0, num_matches / 50)  # Normalize by expected number of matches
        
        # Combine both factors
        final_score = (distance_score * 0.7) + (match_count_score * 0.3)
        return min(final_score, 1.0)
    
    def calculate_similarity(self, matches: List) -> float:
        """
        Calculate similarity score based on matches (legacy method)
        
        Args:
            matches: List of feature matches
            
        Returns:
            Similarity score between 0 and 1
        """
        if not matches:
            return 0.0
        
        # Calculate good matches threshold
        good_matches_count = int(len(matches) * self.good_match_percent)
        good_matches = matches[:good_matches_count]
        
        # Calculate score based on average distance of good matches
        if good_matches:
            avg_distance = sum(m.distance for m in good_matches) / len(good_matches)
            # Normalize distance (lower is better)
            score = max(0, 1 - (avg_distance / 100))
            return score
        
        return 0.0
    
    def match_single_photo(self, film_photo_path: str, scene_photos: List[str]) -> Tuple[str, float]:
        """
        Match a single film photo against all scene photos using ratio test
        
        Args:
            film_photo_path: Path to the film photo
            scene_photos: List of scene photo paths
            
        Returns:
            Tuple of (best_match_filename, confidence_score)
        """
        try:
            # Load and process film photo
            film_image = load_image_for_matching(film_photo_path)
            film_kp, film_desc = self.detect_features(film_image)
            
            if film_desc is None:
                return None, 0.0
            
            best_match = None
            best_score = 0.0
            
            # Compare with each scene photo
            for scene_photo_path in scene_photos:
                try:
                    scene_image = load_image_for_matching(scene_photo_path)
                    scene_kp, scene_desc = self.detect_features(scene_image)
                    
                    if scene_desc is None:
                        continue
                    
                    # Match features using ratio test
                    matches = self.match_features_with_ratio_test(film_desc, scene_desc)
                    
                    if matches:
                        # Calculate similarity score using ratio-tested matches
                        similarity = self.calculate_similarity_with_ratio_test(matches)
                        
                        # Update best match if this is better
                        if similarity > best_score:
                            best_score = similarity
                            best_match = get_file_name_from_path(scene_photo_path)
                
                except Exception as e:
                    print(f"Error processing scene photo {scene_photo_path}: {e}")
                    continue
            
            return best_match, best_score
            
        except Exception as e:
            print(f"Error processing film photo {film_photo_path}: {e}")
            return None, 0.0
    
    def match_folders(self, film_folder: str, scene_folder: str) -> List[Dict]:
        """
        Match all photos between two folders
        
        Args:
            film_folder: Path to folder containing film photos
            scene_folder: Path to folder containing scene photos
            
        Returns:
            List of matching results
        """
        # Get image files from both folders
        film_photos = get_image_files(film_folder)
        scene_photos = get_image_files(scene_folder)
        
        if not film_photos:
            raise ValueError(f"No image files found in film folder: {film_folder}")
        
        if not scene_photos:
            raise ValueError(f"No image files found in scene folder: {scene_folder}")
        
        print(f"Found {len(film_photos)} film photos and {len(scene_photos)} scene photos")
        print(f"Using ratio test with threshold: {self.ratio_threshold}")
        
        results = []
        
        # Match each film photo against scene photos
        for film_photo_path in film_photos:
            film_filename = get_file_name_from_path(film_photo_path)
            
            print(f"Processing film photo: {film_filename}")
            
            best_match, confidence = self.match_single_photo(film_photo_path, scene_photos)
            
            if best_match and confidence > 0.1:  # Minimum confidence threshold
                results.append({
                    'film_photo': film_filename,
                    'scene_photo': best_match,
                    'confidence_score': round(confidence, 3)
                })
                print(f"  Matched with {best_match} (confidence: {confidence:.3f})")
            else:
                print(f"  No good match found (best confidence: {confidence:.3f})")
        
        return results 