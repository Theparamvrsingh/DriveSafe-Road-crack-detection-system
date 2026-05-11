"""
Weight Downloader — Downloads model weights from GitHub Releases if not present locally.
Used during deployment on Hugging Face Spaces / Docker environments.
"""

import os
import urllib.request
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
WEIGHTS_DIR = os.path.join(BASE_DIR, "weights")

# GitHub Release download URLs (override with env; upload weights to your repo Releases)
GITHUB_REPO = os.getenv("GITHUB_WEIGHTS_REPO", "theparamvrsingh/DriveSafe-Road-crack-detection-system")
RELEASE_TAG = os.getenv("GITHUB_WEIGHTS_RELEASE_TAG", "v1.0.0")

WEIGHT_FILES = {
    "best_segmentation.pt": f"https://github.com/{GITHUB_REPO}/releases/download/{RELEASE_TAG}/best_segmentation.pt",
    "best_detection.pt": f"https://github.com/{GITHUB_REPO}/releases/download/{RELEASE_TAG}/best_detection.pt",
}


def download_weights():
    """Download model weights from GitHub Releases if they don't exist locally."""
    os.makedirs(WEIGHTS_DIR, exist_ok=True)

    for filename, url in WEIGHT_FILES.items():
        filepath = os.path.join(WEIGHTS_DIR, filename)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 10_000:
            print(f"✅ Weight file already exists: {filename} ({os.path.getsize(filepath)/1e6:.1f} MB)")
            continue

        print(f"⬇️  Downloading {filename} from GitHub Releases...")
        try:
            urllib.request.urlretrieve(url, filepath)
            size_mb = os.path.getsize(filepath) / 1e6

            # Validate — GitHub returns a small HTML page if the file doesn't exist
            if os.path.getsize(filepath) < 10_000:
                os.remove(filepath)
                print(f"⚠️  Downloaded file too small — likely not a valid weight file. Removed {filename}")
            else:
                print(f"✅ Downloaded {filename} ({size_mb:.1f} MB)")
        except Exception as e:
            print(f"⚠️  Could not download {filename}: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)


if __name__ == "__main__":
    download_weights()
