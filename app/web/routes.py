"""
Flask routes for the web interface
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import tempfile
from pathlib import Path
from ..core.matcher import PhotoMatcher
from ..core.utils import get_available_folders, save_matching_results


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
    
    @app.route('/api/match', methods=['POST'])
    def match_photos():
        """Match photos between selected folders"""
        try:
            data = request.get_json()
            film_folder = data.get('film_folder')
            scene_folder = data.get('scene_folder')
            max_features = data.get('max_features', 500)
            good_match_percent = data.get('good_match_percent', 0.15)
            
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
            
            # Initialize matcher
            matcher = PhotoMatcher(
                max_features=max_features,
                good_match_percent=good_match_percent
            )
            
            # Perform matching
            results = matcher.match_folders(film_path, scene_path)
            
            # Save results to temporary file
            output_file = os.path.join('output', f'match_results_{film_folder}_{scene_folder}.csv')
            save_matching_results(results, output_file)
            
            return jsonify({
                'success': True,
                'results': results,
                'total_matches': len(results),
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