"""
Download MSY Data from GitHub Repository
Downloads the real Mai Shan Yun dataset from the challenge repository
"""
import requests
import os
from pathlib import Path
import zipfile
import io

def download_file_from_github(url: str, output_path: Path):
    """Download a file from GitHub raw URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"✓ Downloaded {output_path.name}")
        return True
    except Exception as e:
        print(f"✗ Failed to download {url}: {str(e)}")
        return False

def download_msy_data(data_dir: str = "data"):
    """Download MSY data files from GitHub repository"""
    data_path = Path(data_dir)
    data_path.mkdir(exist_ok=True)
    
    # GitHub repository base URL (raw content)
    base_url = "https://raw.githubusercontent.com/tamu-datathon-org/mai-shen-yun/main"
    
    print("Downloading MSY data from GitHub repository...")
    print("=" * 60)
    
    # Files to download
    files_to_download = [
        "MSY Data - Ingredient.csv",
        "MSY Data - Shipment.csv",
        "May_Data_Matrix (1).xlsx",
        "June_Data_Matrix.xlsx",
        "July_Data_Matrix (1).xlsx",
        "August_Data_Matrix (1).xlsx",
        "September_Data_Matrix.xlsx",
        "October_Data_Matrix_20251103_214000.xlsx"
    ]
    
    downloaded = 0
    for filename in files_to_download:
        # URL encode the filename
        url_encoded_name = filename.replace(" ", "%20").replace("(", "%28").replace(")", "%29")
        url = f"{base_url}/{url_encoded_name}"
        output_path = data_path / filename
        
        if download_file_from_github(url, output_path):
            downloaded += 1
    
    print("=" * 60)
    print(f"Downloaded {downloaded}/{len(files_to_download)} files")
    
    if downloaded > 0:
        print("\n✅ MSY data download complete!")
        print(f"Data files are in: {data_path.absolute()}")
    else:
        print("\n⚠️ No files were downloaded. Please check your internet connection.")
        print("You can manually download files from:")
        print("https://github.com/tamu-datathon-org/mai-shen-yun/tree/main")

if __name__ == "__main__":
    download_msy_data()


