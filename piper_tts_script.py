import os
import sys
import tarfile
import urllib.request
import shutil
import glob
import subprocess

PIPER_BINARY_PATH = "piper/piper"
PIPER_TAR_URL = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_aarch64.tar.gz"
PIPER_TAR_NAME = "piper_linux_aarch64.tar.gz"

# Step 1: Download and extract Piper if not present
def download_and_extract_piper():
    if os.path.exists(PIPER_BINARY_PATH) and os.access(PIPER_BINARY_PATH, os.X_OK):
        print(f"Piper binary '{PIPER_BINARY_PATH}' already exists and is executable.")
        return True
    
    print("Piper binary not found or not executable. Downloading...")
    try:
        # Remove existing piper directory if it exists but is incomplete
        if os.path.exists("piper"):
            shutil.rmtree("piper")
        
        urllib.request.urlretrieve(PIPER_TAR_URL, PIPER_TAR_NAME)
        print("Download complete. Extracting...")
        
        with tarfile.open(PIPER_TAR_NAME, "r:gz") as tar:
            tar.extractall()
        
        # Make the binary executable
        if os.path.exists(PIPER_BINARY_PATH):
            os.chmod(PIPER_BINARY_PATH, 0o755)
            print("Piper binary is ready.")
        else:
            print("Error: Piper binary not found after extraction.")
            return False
        
        # Clean up the downloaded archive
        os.remove(PIPER_TAR_NAME)
        return True
        
    except Exception as e:
        print(f"Failed to download or extract Piper: {e}")
        return False

def select_text_file():
    txt_files = glob.glob("*.txt")
    if not txt_files:
        print("No .txt files found. Please add a text file to the folder.")
        sys.exit(1)
    if len(txt_files) == 1:
        print(f"Found text file: {txt_files[0]}")
        return txt_files[0]
    print("Multiple .txt files found:")
    for idx, fname in enumerate(txt_files):
        print(f"  [{idx+1}] {fname}")
    while True:
        choice = input(f"Select a file [1-{len(txt_files)}]: ")
        if choice.isdigit() and 1 <= int(choice) <= len(txt_files):
            return txt_files[int(choice)-1]
        print("Invalid selection. Try again.")

def detect_onnx_and_json():
    onnx_files = glob.glob("*.onnx")
    json_files = glob.glob("*.json")
    if not onnx_files:
        print("No .onnx model file found in the folder.")
        sys.exit(1)
    if not json_files:
        print("No .json config file found in the folder.")
        sys.exit(1)
    
    # Try to match .onnx and .json by base name
    for onnx in onnx_files:
        base = os.path.splitext(onnx)[0]
        for js in json_files:
            if os.path.splitext(js)[0] == base:
                print(f"Using model: {onnx}")
                print(f"Using config: {js}")
                return onnx, js
    
    # Fallback: just use the first of each
    print(f"Warning: No matching .onnx/.json pair found. Using {onnx_files[0]} and {json_files[0]}")
    return onnx_files[0], json_files[0]

def run_piper_tts(text_file, onnx_file, json_file):
    base_name = os.path.splitext(os.path.basename(text_file))[0]
    output_wav = f"{base_name}.wav"
    
    with open(text_file, "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        print(f"Text file '{text_file}' is empty.")
        sys.exit(1)
    
    cmd = [
        f"./{PIPER_BINARY_PATH}",
        "--model", onnx_file,
        "--config", json_file,
        "--output_file", output_wav
    ]
    
    print(f"Running Piper: {' '.join(cmd)}")
    try:
        proc = subprocess.run(cmd, input=text.encode("utf-8"), capture_output=True)
        if proc.returncode != 0:
            print(f"Piper failed with error (stderr):\n{proc.stderr.decode('utf-8')}")
            print(f"Piper output (stdout):\n{proc.stdout.decode('utf-8')}")
            sys.exit(1)
        print(f"Success! Output written to {output_wav}")
    except Exception as e:
        print(f"Failed to run Piper: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if not download_and_extract_piper():
        print("Error: Could not set up Piper binary. Please check your internet connection or permissions.")
        sys.exit(1)
    
    text_file = select_text_file()
    onnx_file, json_file = detect_onnx_and_json()
    run_piper_tts(text_file, onnx_file, json_file) 