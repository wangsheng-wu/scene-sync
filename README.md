# Scene Sync - Photo Matching App

A Python application that matches film photos with scene photos using ORB (Oriented FAST and Rotated BRIEF) feature detection and matching.

## Features

- **Command Line Interface**: Process photos directly from the terminal
- **Web Interface**: User-friendly browser-based interface
- **ORB Feature Detection**: Advanced image matching using OpenCV
- **Flexible Input**: Support for various image formats

## Project Structure

```
scene-sync/
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── matcher.py          # ORB matching logic
│   │   └── utils.py            # Utility functions
│   ├── cli/
│   │   ├── __init__.py
│   │   └── commands.py         # CLI commands
│   └── web/
│       ├── __init__.py
│       ├── routes.py           # Flask routes
│       ├── templates/          # HTML templates
│       └── static/             # CSS, JS, images
├── film-photos/                # Input folder for film photos
├── scene-info/                 # Input folder for scene photos
├── output/                     # Output folder for results
├── requirements.txt
├── main.py                     # Main application entry point
└── README.md
```

## Setup

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create Required Directories**:
   ```bash
   mkdir -p film-photos scene-info output
   ```

3. **Add Your Photos**:
   - Place film photos in `film-photos/` (organized in subfolders)
   - Place scene photos in `scene-info/` (organized in subfolders)

## Usage

### Command Line Interface

```bash
# Match photos from specific folders
python main.py match --film-folder film-photos/folder1 --scene-folder scene-info/folder2

# List available folders
python main.py list-folders

# Run with custom output directory
python main.py match --film-folder film-photos/folder1 --scene-folder scene-info/folder2 --output output/results.csv
```

### Web Interface

```bash
# Start the web server
python main.py web

# Then open http://localhost:5001 in your browser
```

## Input Requirements

- **Image Formats**: JPEG, PNG, BMP, TIFF
- **Folder Structure**: Each folder should contain only image files
- **File Names**: Must be unique within each folder
- **Image Quality**: Higher resolution images work better for matching

## Output

The app generates a CSV file with columns:
- `film_photo`: Name of the film photo file
- `scene_photo`: Name of the matched scene photo file
- `confidence_score`: Matching confidence (0-1)

## Configuration

You can adjust matching parameters in `app/core/matcher.py`:
- `MAX_FEATURES`: Maximum number of features to detect
- `GOOD_MATCH_PERCENT`: Threshold for good matches
- `MIN_MATCHES`: Minimum matches required for a valid match 