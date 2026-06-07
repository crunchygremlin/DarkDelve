#!/usr/bin/env python3
"""Build standalone DarkDelve executable"""
import subprocess
import sys
import os
import platform
import urllib.request
import shutil
from pathlib import Path

def download_ollama_binaries():
    """Download Ollama binaries for all platforms"""
    binaries = {
        "linux_x64": "https://github.com/ollama/ollama/releases/latest/download/ollama-linux-amd64",
        "macos_arm64": "https://github.com/ollama/ollama/releases/latest/download/ollama-darwin-arm64",
        "windows_x64": "https://github.com/ollama/ollama/releases/latest/download/ollama-windows-amd64.exe",
    }
    
    vendor_dir = Path("vendor")
    vendor_dir.mkdir(exist_ok=True)
    
    for name, url in binaries.items():
        path = vendor_dir / f"ollama_{name}"
        if not path.exists():
            print(f"Downloading {name}...")
            try:
                urllib.request.urlretrieve(url, path)
                if not name.endswith(".exe"):
                    os.chmod(path, 0o755)
                print(f"  Downloaded to {path}")
            except Exception as e:
                print(f"  Failed to download {name}: {e}")

def build():
    print("Building DarkDelve...")
    
    # Download Ollama binaries
    download_ollama_binaries()
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", "darkdelve",
        "--add-data", "config:config",
        "--add-data", "assets:assets",
        "--add-data", "vendor:vendor",
        "--hidden-import", "tcod",
        "--hidden-import", "numpy",
        "--hidden-import", "yaml",
        "--hidden-import", "sqlite3",
        "--hidden-import", "requests",
        "--clean",
        "darkdelve.py"
    ]
    
    print("Running PyInstaller...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("\nBuild complete!")
        print(f"Executable: dist/darkdelve")
        
        # Copy config and assets to dist for easy distribution
        dist_dir = Path("dist")
        if dist_dir.exists():
            shutil.copytree("config", dist_dir / "config", dirs_exist_ok=True)
            shutil.copytree("assets", dist_dir / "assets", dirs_exist_ok=True)
            shutil.copytree("vendor", dist_dir / "vendor", dirs_exist_ok=True)
            print("Copied config, assets, and vendor to dist/")
    else:
        print("Build failed!")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)

if __name__ == "__main__":
    build()