#!/usr/bin/env python3
"""
Rail-Drishti Setup Script

This script automates the setup process for the Rail-Drishti Streamlit application.
It prepares the dataset and verifies the configuration.

Usage:
    python setup.py
"""

import os
import sys
import shutil
from pathlib import Path

print("┌" + "─" * 60 + "┐")
print("│" + " " * 17 + "🚂 Rail-Drishti Setup" + " " * 17 + "│")
print("└" + "─" * 60 + "┘")
print()

def check_file_exists(path, description):
    """Check if a file exists and print status."""
    if os.path.exists(path):
        print(f"✅ {description}: Found")
        return True
    else:
        print(f"❌ {description}: Not found")
        return False

def create_directory(path, description):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)
    if os.path.exists(path):
        print(f"✅ {description}: Created/Verified")
        return True
    else:
        print(f"❌ {description}: Failed to create")
        return False

def main():
    print("🔍 Step 1: Checking environment...\n")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 8:
        print(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"❌ Python version: {python_version.major}.{python_version.minor}.{python_version.micro} (3.8+ required)")
        return False
    
    print()
    print("📁 Step 2: Setting up directories...\n")
    
    # Create data directory
    data_dir = "data"
    create_directory(data_dir, "Data directory")
    
    print()
    print("📊 Step 3: Checking dataset...\n")
    
    # Check if CSV exists in data folder
    csv_path = "data/indian_railway_data.csv"
    csv_exists = check_file_exists(csv_path, "Dataset (data/indian_railway_data.csv)")
    
    if not csv_exists:
        print()
        print("🚨 Dataset not found!")
        print()
        print("Please ensure you have 'indian_railway_data.csv' in the data directory.")
        print()
    
    print()
    print("🔑 Step 4: Checking configuration...\n")
    
    # Check if api_client.py exists
    api_client_exists = check_file_exists("frontend/api_client.py", "API Client (frontend/api_client.py)")
    
    if api_client_exists:
        # Check for API key
        with open("frontend/api_client.py", "r") as f:
            content = f.read()
            if 'GEMINI_API_KEY = "AIzaSy' in content:
                # Check if it's the default key
                if 'AIzaSyDvLDAirzQi_sE9pMQDk3u8ev5IyiIZoVE' in content:
                    print("⚠️ Gemini API Key: Using default (consider changing)")
                else:
                    print("✅ Gemini API Key: Configured")
            else:
                print("❌ Gemini API Key: Not configured")
                print("   Update line 13 in frontend/api_client.py with your Gemini API key")
                print("   Get your key from: https://makersuite.google.com/app/apikey")
    
    print()
    print("📦 Step 5: Checking dependencies...\n")
    
    # Check if requirements.txt exists
    requirements_exists = check_file_exists("requirements.txt", "Requirements file")
    
    if requirements_exists:
        print()
        print("📄 To install dependencies, run:")
        print("   pip install -r requirements.txt")
    
    print()
    print("🎯 Step 6: Checking core files...\n")
    
    app_exists = check_file_exists("frontend/app.py", "Main application (frontend/app.py)")
    readme_exists = check_file_exists("README.md", "Documentation (README.md)")
    
    print()
    print("─" * 62)
    print()
    
    # Summary
    all_ready = csv_exists and api_client_exists and app_exists
    
    if all_ready:
        print("✅ Setup complete! You're ready to run the application.")
        print()
        print("🚀 To start the application, run:")
        print("   streamlit run frontend/app.py")
        print()
        print("👉 The app will open at: http://localhost:8501")
    else:
        print("⚠️ Setup incomplete. Please complete the steps above.")
        print()
        print("📚 For detailed instructions, see README.md")
    
    print()
    print("─" * 62)
    
    return all_ready

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print()
        print(f"❌ Error during setup: {str(e)}")
        sys.exit(1)
