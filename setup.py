#!/usr/bin/env python3
"""
Setup script for Scene Sync
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def create_directories():
    """Create required directories"""
    directories = ['film-photos', 'scene-info', 'output']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")


def install_dependencies():
    """Install Python dependencies"""
    return run_command(
        "pip install -r requirements.txt",
        "Installing Python dependencies"
    )


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("✗ Python 3.7 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True


def main():
    """Main setup function"""
    print("Scene Sync - Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    print("\nCreating directories...")
    create_directories()
    
    # Install dependencies
    print("\nInstalling dependencies...")
    if not install_dependencies():
        print("\nSetup failed. Please check the error messages above.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✓ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Add your film photos to the 'film-photos' directory")
    print("2. Add your scene photos to the 'scene-info' directory")
    print("3. Run the application:")
    print("   - CLI: python main.py match --film-folder film-photos/folder1 --scene-folder scene-info/folder2")
    print("   - Web: python main.py web")
    print("\nFor more information, see README.md")


if __name__ == '__main__':
    main() 