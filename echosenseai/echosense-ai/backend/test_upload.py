import requests
import os

# Create dummy audio file
filename = "test_audio.mp3"
with open(filename, "wb") as f:
    f.write(b"dummy audio content" * 100)

url = "http://127.0.0.1:8000/api/upload/audio"
try:
    print(f"Uploading {filename} to {url}...")
    with open(filename, "rb") as f:
        files = {"file": (filename, f, "audio/mpeg")}
        response = requests.post(url, files=files)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
finally:
    if os.path.exists(filename):
        os.remove(filename)
