"""
Flask routes for the web interface
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import tempfile
import csv
from pathlib import Path
from ..core.matcher import PhotoMatcher
from ..core.utils import get_available_folders, save_matching_results
from ..core.verifier import MatchVerifier


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    
    @app.route('/')
    def index():
        """Main page"""
        return render_template('index.html')
    
    @app.route('/api/folders')
    def get_folders():
        """Get available folders from film-photos and scene-info"""
        try:
            film_folders = get_available_folders('film-photos')
            scene_folders = get_available_folders('scene-info')
            
            return jsonify({
                'success': True,
                'film_folders': film_folders,
                'scene_folders': scene_folders
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/reference-tables')
    def get_reference_tables():
        """Get available reference tables from output folder"""
        try:
            output_dir = 'output'
            if not os.path.exists(output_dir):
                return jsonify({
                    'success': True,
                    'reference_tables': []
                })
            
            reference_tables = []
            for file in os.listdir(output_dir):
                if file.endswith('.csv') and file.startswith('match_results_'):
                    reference_tables.append(file)
            
            return jsonify({
                'success': True,
                'reference_tables': sorted(reference_tables)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    def load_reference_table(reference_file: str):
        """Load reference table and return existing matches and used scene photos"""
        reference_path = os.path.join('output', reference_file)
        
        if not os.path.exists(reference_path):
            raise FileNotFoundError(f"Reference file not found: {reference_path}")
        
        existing_matches = []
        used_scene_photos = set()
        
        try:
            with open(reference_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Check if required columns exist
                required_columns = ['film_photo', 'scene_photo', 'confidence_score', 'confident_match']
                if not all(col in reader.fieldnames for col in required_columns):
                    raise ValueError(f"Reference CSV must contain columns: {required_columns}")
                
                for row in reader:
                    film_photo = row['film_photo'].strip()
                    scene_photo = row['scene_photo'].strip()
                    confident_match = int(row['confident_match'])
                    
                    # Keep confident matches (confident_match = 1)
                    if confident_match == 1 and scene_photo:
                        existing_matches.append({
                            'film_photo': film_photo,
                            'scene_photo': scene_photo,
                            'confidence_score': float(row['confidence_score']),
                            'confident_match': confident_match
                        })
                        used_scene_photos.add(scene_photo)
        
        except Exception as e:
            raise ValueError(f"Error reading reference file {reference_path}: {e}")
        
        return existing_matches, used_scene_photos
    
    @app.route('/api/match', methods=['POST'])
    def match_photos():
        """Match photos between selected folders"""
        try:
            data = request.get_json()
            film_folder = data.get('film_folder')
            scene_folder = data.get('scene_folder')
            max_features = data.get('max_features', 800)
            good_match_percent = data.get('good_match_percent', 0.15)
            reference_table = data.get('reference_table', '')
            
            if not film_folder or not scene_folder:
                return jsonify({
                    'success': False,
                    'error': 'Both film_folder and scene_folder are required'
                }), 400
            
            # Construct full paths
            film_path = os.path.join('film-photos', film_folder)
            scene_path = os.path.join('scene-info', scene_folder)
            
            if not os.path.exists(film_path):
                return jsonify({
                    'success': False,
                    'error': f'Film folder does not exist: {film_path}'
                }), 400
            
            if not os.path.exists(scene_path):
                return jsonify({
                    'success': False,
                    'error': f'Scene folder does not exist: {scene_path}'
                }), 400
            
            # Load reference table if specified
            excluded_film_photos = set()
            used_scene_photos = set()
            existing_confident_matches = []
            
            if reference_table:
                try:
                    existing_matches, used_scene_photos = load_reference_table(reference_table)
                    excluded_film_photos = {match['film_photo'] for match in existing_matches}
                    existing_confident_matches = existing_matches  # Keep all confident matches
                    print(f"Excluding {len(excluded_film_photos)} film photos with confident matches")
                    print(f"Excluding {len(used_scene_photos)} used scene photos")
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': f'Error loading reference table: {str(e)}'
                    }), 400
            
            # Initialize matcher
            matcher = PhotoMatcher(
                max_features=max_features,
                good_match_percent=good_match_percent
            )
            
            # Get all film photos and filter out those with confident matches
            from ..core.utils import get_image_files
            all_film_photos = get_image_files(film_path)
            available_film_photos = [
                photo for photo in all_film_photos 
                if os.path.basename(photo) not in excluded_film_photos
            ]
            
            # Get all scene photos and filter out used ones
            all_scene_photos = get_image_files(scene_path)
            available_scene_photos = [
                photo for photo in all_scene_photos
                if os.path.basename(photo) not in used_scene_photos
            ]
            
            print(f"Processing {len(available_film_photos)} available film photos")
            print(f"Available {len(available_scene_photos)} unused scene photos")
            
            # Perform matching on available photos
            results = []
            if available_film_photos and available_scene_photos:
                for film_photo_path in available_film_photos:
                    film_filename = os.path.basename(film_photo_path)
                    
                    print(f"Processing film photo: {film_filename}")
                    
                    best_match, confidence = matcher.match_single_photo(film_photo_path, available_scene_photos)
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
            
            # Combine existing confident matches with new results
            final_results = existing_confident_matches + results
            
            # Save results to temporary file
            output_file = os.path.join('output', f'match_results_{film_folder}_{scene_folder}.csv')
            save_matching_results(final_results, output_file)
            
            return jsonify({
                'success': True,
                'results': final_results,
                'total_matches': len(final_results),
                'existing_matches': len(existing_confident_matches),
                'new_matches': len(results),
                'excluded_film_photos': len(excluded_film_photos),
                'excluded_scene_photos': len(used_scene_photos),
                'output_file': output_file
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/download/<filename>')
    def download_results(filename):
        """Download results CSV file"""
        try:
            file_path = os.path.join('output', filename)
            if os.path.exists(file_path):
                # Use absolute path and specify mimetype
                abs_path = os.path.abspath(file_path)
                return send_file(
                    abs_path, 
                    as_attachment=True,
                    download_name=filename,
                    mimetype='text/csv'
                )
            else:
                return jsonify({
                    'success': False,
                    'error': f'File not found: {file_path}'
                }), 404
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Download failed: {str(e)}'
            }), 500
    
    @app.route('/api/verify', methods=['POST'])
    def verify_results():
        """Verify matching results against ground truth"""
        try:
            data = request.get_json()
            results_file = data.get('results_file')
            truth_file = data.get('truth_file')
            
            if not results_file or not truth_file:
                return jsonify({
                    'success': False,
                    'error': 'Both results_file and truth_file are required'
                }), 400
            
            # Construct full paths
            results_path = os.path.join('output', results_file)
            truth_path = os.path.join('truth', truth_file)
            
            if not os.path.exists(results_path):
                return jsonify({
                    'success': False,
                    'error': f'Results file does not exist: {results_path}'
                }), 400
            
            if not os.path.exists(truth_path):
                return jsonify({
                    'success': False,
                    'error': f'Truth file does not exist: {truth_path}'
                }), 400
            
            # Perform verification
            verifier = MatchVerifier()
            metrics, detailed_results = verifier.verify_matches(results_path, truth_path)
            
            return jsonify({
                'success': True,
                'metrics': {
                    'total_results': metrics.total_results,
                    'total_truth': metrics.total_truth,
                    'correct_matches': metrics.correct_matches,
                    'incorrect_matches': metrics.incorrect_matches,
                    'missed_matches': metrics.missed_matches,
                    'extra_matches': metrics.extra_matches,
                    'accuracy': round(metrics.accuracy, 3),
                    'precision': round(metrics.precision, 3),
                    'recall': round(metrics.recall, 3),
                    'f1_score': round(metrics.f1_score, 3)
                },
                'detailed_results': detailed_results
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/truth-files')
    def get_truth_files():
        """Get available truth files"""
        try:
            truth_dir = 'truth'
            if not os.path.exists(truth_dir):
                return jsonify({
                    'success': True,
                    'truth_files': []
                })
            
            truth_files = []
            for file in os.listdir(truth_dir):
                if file.endswith('.csv'):
                    truth_files.append(file)
            
            return jsonify({
                'success': True,
                'truth_files': sorted(truth_files)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/validate-folder', methods=['POST'])
    def validate_folder():
        """Validate a folder and return information about its contents"""
        try:
            data = request.get_json()
            folder_path = data.get('folder_path')
            
            if not folder_path:
                return jsonify({
                    'success': False,
                    'error': 'folder_path is required'
                }), 400
            
            if not os.path.exists(folder_path):
                return jsonify({
                    'success': False,
                    'error': f'Folder does not exist: {folder_path}'
                }), 400
            
            from ..core.utils import get_image_files, SUPPORTED_FORMATS
            
            image_files = get_image_files(folder_path)
            
            return jsonify({
                'success': True,
                'folder_path': folder_path,
                'total_images': len(image_files),
                'supported_formats': list(SUPPORTED_FORMATS),
                'image_files': [os.path.basename(f) for f in image_files[:20]]  # First 20 files
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return app 