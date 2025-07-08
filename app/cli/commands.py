"""
CLI commands for the photo matching application
"""

import click
import os
from pathlib import Path
from ..core.matcher import PhotoMatcher
from ..core.utils import get_available_folders, save_matching_results
from ..core.verifier import MatchVerifier


@click.group()
def cli():
    """Scene Sync - Photo Matching Application"""
    pass


@cli.command()
@click.option('--film-folder', required=True, help='Path to folder containing film photos')
@click.option('--scene-folder', required=True, help='Path to folder containing scene photos')
@click.option('--output', default='output/results.csv', help='Output CSV file path')
@click.option('--max-features', default=500, help='Maximum number of features to detect')
@click.option('--good-match-percent', default=0.15, help='Good match percentage threshold')
def match(film_folder, scene_folder, output, max_features, good_match_percent):
    """Match photos between film and scene folders"""
    
    # Validate input folders
    if not os.path.exists(film_folder):
        click.echo(f"Error: Film folder does not exist: {film_folder}")
        return
    
    if not os.path.exists(scene_folder):
        click.echo(f"Error: Scene folder does not exist: {scene_folder}")
        return
    
    click.echo(f"Starting photo matching...")
    click.echo(f"Film folder: {film_folder}")
    click.echo(f"Scene folder: {scene_folder}")
    click.echo(f"Output file: {output}")
    click.echo(f"Max features: {max_features}")
    click.echo(f"Good match percent: {good_match_percent}")
    click.echo("-" * 50)
    
    try:
        # Initialize matcher
        matcher = PhotoMatcher(
            max_features=max_features,
            good_match_percent=good_match_percent
        )
        
        # Perform matching
        results = matcher.match_folders(film_folder, scene_folder)
        
        if results:
            # Save results
            save_matching_results(results, output)
            
            click.echo(f"\nMatching completed successfully!")
            click.echo(f"Found {len(results)} matches")
            click.echo(f"Results saved to: {output}")
            
            # Display results summary
            click.echo("\nTop matches:")
            sorted_results = sorted(results, key=lambda x: x['confidence_score'], reverse=True)
            for i, result in enumerate(sorted_results[:5]):
                click.echo(f"{i+1}. {result['film_photo']} -> {result['scene_photo']} (confidence: {result['confidence_score']})")
        else:
            click.echo("No matches found with sufficient confidence.")
    
    except Exception as e:
        click.echo(f"Error during matching: {e}")


@cli.command()
@click.option('--film-base', default='film-photos', help='Base directory for film photos')
@click.option('--scene-base', default='scene-info', help='Base directory for scene photos')
def list_folders(film_base, scene_base):
    """List available folders in film-photos and scene-info directories"""
    
    click.echo("Available folders:")
    click.echo("-" * 50)
    
    # List film folders
    click.echo(f"Film photo folders ({film_base}):")
    film_folders = get_available_folders(film_base)
    if film_folders:
        for folder in film_folders:
            click.echo(f"  - {folder}")
    else:
        click.echo("  No folders found")
    
    click.echo()
    
    # List scene folders
    click.echo(f"Scene photo folders ({scene_base}):")
    scene_folders = get_available_folders(scene_base)
    if scene_folders:
        for folder in scene_folders:
            click.echo(f"  - {folder}")
    else:
        click.echo("  No folders found")


@cli.command()
@click.option('--film-base', default='film-photos', help='Base directory for film photos')
@click.option('--scene-base', default='scene-info', help='Base directory for scene photos')
def setup_directories(film_base, scene_base):
    """Create the required directory structure"""
    
    directories = [
        film_base,
        scene_base,
        'output'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        click.echo(f"Created directory: {directory}")
    
    click.echo("\nDirectory structure created successfully!")
    click.echo("You can now add your photos to the film-photos and scene-info directories.")


@cli.command()
@click.option('--results', required=True, help='Path to the matching results CSV file')
@click.option('--truth', required=True, help='Path to the ground truth CSV file')
def verify(results, truth):
    """Verify matching results against ground truth and compute metrics"""
    
    try:
        verifier = MatchVerifier()
        metrics, detailed_results = verifier.verify_matches(results, truth)
        verifier.print_verification_report(metrics, detailed_results)
        
    except Exception as e:
        click.echo(f"Error during verification: {e}")


@cli.command()
@click.option('--folder', required=True, help='Path to folder to validate')
def validate_folder(folder):
    """Validate a folder and show information about its contents"""
    
    if not os.path.exists(folder):
        click.echo(f"Error: Folder does not exist: {folder}")
        return
    
    from ..core.utils import get_image_files, SUPPORTED_FORMATS
    
    image_files = get_image_files(folder)
    
    click.echo(f"Folder: {folder}")
    click.echo(f"Total image files: {len(image_files)}")
    click.echo(f"Supported formats: {', '.join(SUPPORTED_FORMATS)}")
    
    if image_files:
        click.echo("\nImage files found:")
        for file_path in image_files[:10]:  # Show first 10
            filename = os.path.basename(file_path)
            click.echo(f"  - {filename}")
        
        if len(image_files) > 10:
            click.echo(f"  ... and {len(image_files) - 10} more files")
    else:
        click.echo("\nNo image files found in this folder.")
        click.echo("Make sure the folder contains files with these extensions:")
        for ext in SUPPORTED_FORMATS:
            click.echo(f"  - {ext}") 