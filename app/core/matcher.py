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
    
    def __init__(self, max_features: int = 800, good_match_percent: float = 0.15):
        """
        Initialize the photo matcher
        
        Args:
            max_features: Maximum number of features to detect
            good_match_percent: Percentage of good matches threshold
        """
        self.max_features = max_features
        self.good_match_percent = good_match_percent
        
        # Initialize ORB detector
        self.orb = cv2.ORB_create(max_features)
        
        # Initialize feature matcher
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    
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
    
    def match_features(self, desc1: np.ndarray, desc2: np.ndarray) -> List:
        """
        Match features between two images
        
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
    
    def calculate_similarity(self, matches: List) -> float:
        """
        Calculate similarity score based on matches
        
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
        Match a single film photo against all scene photos
        
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
                    
                    # Match features
                    matches = self.match_features(film_desc, scene_desc)
                    
                    if matches:
                        # Calculate similarity score
                        similarity = self.calculate_similarity(matches)
                        
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
        
        results = []
        
        # Match each film photo against scene photos
        for film_photo_path in film_photos:
            film_filename = get_file_name_from_path(film_photo_path)
            
            print(f"Processing film photo: {film_filename}")
            
            best_match, confidence = self.match_single_photo(film_photo_path, scene_photos)
            confident_match = 1 if confidence >= 0.7 else 0
            
            if best_match and confidence > 0.6:  # Minimum confidence threshold
                results.append({
                    'film_photo': film_filename,
                    'scene_photo': best_match,
                    'confidence_score': round(confidence, 3),
                    'confident_match': confident_match
                })
                print(f"  Matched with {best_match} (confidence: {confidence:.3f})")
            else:
                results.append({
                    'film_photo': film_filename,
                    'scene_photo': None,
                    'confidence_score': 0.0,
                    'confident_match': -1
                })
                print(f"  No good match found (best confidence: {confidence:.3f})")
        
        return results
    
    def inspect_image_pair(self, film_photo_path: str, scene_photo_path: str) -> Dict:
        """
        Inspect a specific pair of images and return detailed matching information
        
        Args:
            film_photo_path: Path to the film photo
            scene_photo_path: Path to the scene photo
            
        Returns:
            Dictionary containing detailed matching information
        """
        try:
            # Load and process both images
            film_image = load_image_for_matching(film_photo_path)
            scene_image = load_image_for_matching(scene_photo_path)
            
            # Detect features in both images
            film_kp, film_desc = self.detect_features(film_image)
            scene_kp, scene_desc = self.detect_features(scene_image)
            
            if film_desc is None or scene_desc is None:
                return {
                    'success': False,
                    'error': 'Could not detect features in one or both images',
                    'film_keypoints': 0,
                    'scene_keypoints': 0,
                    'matches': [],
                    'confidence_score': 0.0
                }
            
            # Match features
            matches = self.match_features(film_desc, scene_desc)
            
            # Calculate similarity score
            similarity = self.calculate_similarity(matches)
            
            # Prepare keypoint data for visualization
            film_keypoints = []
            for kp in film_kp:
                film_keypoints.append({
                    'x': float(kp.pt[0]),
                    'y': float(kp.pt[1]),
                    'size': float(kp.size),
                    'angle': float(kp.angle),
                    'response': float(kp.response)
                })
            
            scene_keypoints = []
            for kp in scene_kp:
                scene_keypoints.append({
                    'x': float(kp.pt[0]),
                    'y': float(kp.pt[1]),
                    'size': float(kp.size),
                    'angle': float(kp.angle),
                    'response': float(kp.response)
                })
            
            # Prepare match data for visualization
            match_data = []
            for match in matches:
                film_idx = match.queryIdx
                scene_idx = match.trainIdx
                
                if film_idx < len(film_kp) and scene_idx < len(scene_kp):
                    film_kp_coord = film_kp[film_idx].pt
                    scene_kp_coord = scene_kp[scene_idx].pt
                    
                    match_data.append({
                        'film_x': float(film_kp_coord[0]),
                        'film_y': float(film_kp_coord[1]),
                        'scene_x': float(scene_kp_coord[0]),
                        'scene_y': float(scene_kp_coord[1]),
                        'distance': float(match.distance)
                    })
            
            return {
                'success': True,
                'film_keypoints': film_keypoints,
                'scene_keypoints': scene_keypoints,
                'matches': match_data,
                'total_matches': len(matches),
                'confidence_score': round(similarity, 3),
                'film_filename': get_file_name_from_path(film_photo_path),
                'scene_filename': get_file_name_from_path(scene_photo_path)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'film_keypoints': [],
                'scene_keypoints': [],
                'matches': [],
                'confidence_score': 0.0
            } 