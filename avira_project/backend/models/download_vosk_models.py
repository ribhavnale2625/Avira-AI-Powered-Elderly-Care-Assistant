import os
import sys
import zipfile
import urllib.request

def download_progress(block_num, block_size, total_size):
    read_so_far = block_num * block_size
    if total_size > 0:
        percent = read_so_far * 100 / total_size
        sys.stdout.write(f"\rDownloading: {percent:.2f}% ({read_so_far / (1024*1024):.2f}MB / {total_size / (1024*1024):.2f}MB)")
    else:
        sys.stdout.write(f"\rDownloading: {read_so_far / (1024*1024):.2f}MB")
    sys.stdout.flush()

def download_and_extract(url, dest_dir):
    filename = url.split('/')[-1]
    zip_path = os.path.join(dest_dir, filename)
    
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        
    print(f"\nDownloading {url} to {zip_path}...")
    urllib.request.urlretrieve(url, zip_path, download_progress)
    print(f"\nExtracting {zip_path}...")
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(dest_dir)
        
    print(f"Extraction completed. Removing zip file...")
    os.remove(zip_path)
    print("Done!")

if __name__ == "__main__":
    models_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. English Model
    en_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    en_dir = os.path.join(models_dir, "vosk-model-small-en-us-0.15")
    if not os.path.exists(en_dir):
        download_and_extract(en_url, models_dir)
    else:
        print("English model already exists.")
        
    # 2. Hindi Model
    hi_url = "https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip"
    hi_dir = os.path.join(models_dir, "vosk-model-small-hi-0.22")
    if not os.path.exists(hi_dir):
        download_and_extract(hi_url, models_dir)
    else:
        print("Hindi model already exists.")
        
    print("\nAll models downloaded and extracted successfully!")
