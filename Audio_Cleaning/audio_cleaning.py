# AUDIO CLEANING & EXTRACTION (Cleanvoice AI)
from cleanvoice import Cleanvoice
import requests
import time
import os
from moviepy.editor import VideoFileClip

# pip install cleanvoice-sdk



def extract_audio_from_video(video_path, output_audio_path="audio.wav"):
 
    # Extracts the audio track from a video file and saves it as a WAV file.
    try:
        print("Extracting audio from video...")
        video = VideoFileClip(str(video_path))
        video.audio.write_audiofile(output_audio_path, verbose=False, logger=None)
        print(f"Audio extracted successfully: {output_audio_path}")
        return output_audio_path   # <-- ADD THIS
    except Exception as e:
        print(f"Error extracting audio: {e}")
        raise

def clean_audio_with_cleanvoice(input_audio_path, output_audio_path, api_key):

    # Sends an audio file to Cleanvoice AI for noise removal and speech enhancement.

    print("Uploading audio to Cleanvoice AI for cleaning...")

    url = "https://api.cleanvoice.ai/v1/process"
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"file": open(input_audio_path, "rb")}

    try:
        response = requests.post(url, headers=headers, files=files)
        response.raise_for_status()
    except Exception as e:
        print(f"Error uploading file to Cleanvoice: {e}")
        return

    job_data = response.json()
    job_id = job_data.get("id")
    if not job_id:
        print("Could not get job ID from Cleanvoice API response.")
        return

    print(f"Job submitted successfully (Job ID: {job_id})")
    print("Waiting for Cleanvoice AI to process the audio...")

    # Poll job status
    status_url = f"https://api.cleanvoice.ai/v1/jobs/{job_id}"
    while True:
        status_response = requests.get(status_url, headers=headers)
        status_data = status_response.json()

        if status_data.get("status") == "completed":
            print("Audio cleaning completed. Downloading file...")
            download_url = status_data.get("output_url")
            break
        elif status_data.get("status") == "failed":
            print("Cleanvoice AI job failed.")
            return
        else:
            time.sleep(5)

    # Download the cleaned file
    cleaned_audio = requests.get(download_url)
    with open(output_audio_path, "wb") as f:
        f.write(cleaned_audio.content)

    print(f"Cleaned audio saved as: {output_audio_path}")



def process_audio_with_cleanvoice(video_path, api_key):

    # Extracts audio from a video, processes it using Cleanvoice AI
    # Downloads the cleaned result locally


    print("Extracting audio from video...")
    audio_path = extract_audio_from_video(video_path, "extracted_audio.wav")
    print(f"Audio extracted: {audio_path}")

    print("Initializing Cleanvoice SDK...")
    cv = Cleanvoice({'api_key': api_key})

    print("Processing audio with AI-powered cleaning...")
    result, output_path = cv.process_and_download(
        audio_path, 
        "cleaned_audio.wav",
        {
            "fillers": True,
            "stutters": True,
            "long_silences": True,
            "mouth_sounds": True,
            "breath": True,
            "remove_noise": True,
            "normalize": True,
            "transcription": True,
            "summarize": True
        }
    )

    print("\n Audio cleaned successfully!")
    print(f"Cleaned audio saved as: {output_path}")
    print(f"Transcription summary: {result.transcript.summary if result.transcript else 'No summary.'}")

    return output_path

