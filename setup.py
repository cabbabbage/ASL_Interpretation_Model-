import os
import subprocess
import sys

def install_packages():
    """
    Installs the required Python packages using pip.
    """
    packages = [
        'opencv-python',
        'numpy',
        'mediapipe',
        'scikit-learn',
        'scikit-learn-extra',
        'fastdtw',
        'scipy',
        'tensorflow',
        'pandas',  # Required by Kaggle API
        'tk',      # For tkinter (usually comes with Python, but added just in case)
        'kaggle',  # For Kaggle API
    ]
    
    # Install each package
    for package in packages:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def download_kaggle_dataset():
    """
    Downloads the Kaggle dataset 'risangbaskoro/wlasl-processed' to the current working directory.
    """
    # Check if Kaggle API credentials exist
    kaggle_json = os.path.join(os.path.expanduser('~'), '.kaggle', 'kaggle.json')
    if not os.path.isfile(kaggle_json):
        print("Kaggle API credentials not found!")
        print("Please follow the instructions to set up Kaggle API credentials.")
        print("Visit: https://github.com/Kaggle/kaggle-api#api-credentials")
        sys.exit(1)
    
    # Ensure the .kaggle directory has the correct permissions
    os.chmod(kaggle_json, 0o600)
    
    # Download the dataset using Kaggle API
    print("Downloading the Kaggle dataset 'risangbaskoro/wlasl-processed'...")
    try:
        subprocess.check_call(['kaggle', 'datasets', 'download', '-d', 'risangbaskoro/wlasl-processed'])
        print("Dataset downloaded successfully.")
    except subprocess.CalledProcessError as e:
        print("Error downloading the dataset:")
        print(e)
        sys.exit(1)
    
    # Unzip the dataset
    dataset_zip = 'wlasl-processed.zip'
    if os.path.isfile(dataset_zip):
        print("Unzipping the dataset...")
        shutil.unpack_archive(dataset_zip, extract_dir='wlasl-processed')
        print("Dataset unzipped successfully.")
    else:
        print("Dataset zip file not found after download.")
        sys.exit(1)

def run_make_directory():
    """
    Runs the 'make_directory.py' script in the current directory.
    """
    script_name = 'make_directory.py'
    if os.path.isfile(script_name):
        print(f"Running '{script_name}'...")
        try:
            subprocess.check_call([sys.executable, script_name])
            print(f"'{script_name}' executed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error running '{script_name}':")
            print(e)
            sys.exit(1)
    else:
        print(f"'{script_name}' not found in the current directory.")
        sys.exit(1)

def main():
    # Step 1: Install required packages
    print("Installing required Python packages...")
    install_packages()
    print("All packages installed successfully.\n")
    
    # Step 2: Download Kaggle dataset
    #download_kaggle_dataset()
    
    # Step 3: Run make_directory.py
    run_make_directory()

if __name__ == '__main__':
    main()
