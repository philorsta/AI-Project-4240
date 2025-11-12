# AUDIO CLEANING & EXTRACTION (Cleanvoice AI)

import requests
import time
import os
from moviepy.editor import VideoFileClip


def extract_audio_from_video(video_path, output_audio_path="audio.wav"):
 
    # Extracts the audio track from a video file and saves it as a WAV file.
 
    try:
        print("Extracting audio from video...")
        video = VideoFileClip(str(video_path))
        video.audio.write_audiofile(output_audio_path, verbose=False, logger=None)
        print(f"Audio extracted successfully: {output_audio_path}")
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

    raw_audio = "audio.wav"
    cleaned_audio = "cleaned_audio.wav"

    # Extract
    extract_audio_from_video(video_path, raw_audio)

    # Clean using Cleanvoice
    clean_audio_with_cleanvoice(raw_audio, cleaned_audio, api_key)

    return cleaned_audio
