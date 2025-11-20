"""
AI Assisted Communication for Video Presentations
-------------------------------------------------
Course: Artificial Intelligence 4240-001 — Fall 2025
Author: 

Description:
    It allows the user to load a video file, display its basic properties, 
    and includes placeholder sections for future AI modules:
        - Audio cleaning and extraction
        - Facial expression analysis
        - Subtitle generation and synchronization
"""

# IMPORTS 
import os
import sys
import moviepy.editor as mp
from pathlib import Path
from audio_cleaning import process_audio_with_cleanvoice


# LOAD VIDEO
def load_video(video_path):
    try:
        video = mp.VideoFileClip(str(video_path))
        return video
    except Exception as e:
        print(f"Error loading video: {e}")
        sys.exit(1)


# MAIN
def main():
    print("AI Assisted Communication Project")
    print("---------------------------------------------------")

    # USER INPUT SECTION
    path_input = input("Enter or drag your video file here: ").strip().strip('"')
    video_path = Path(path_input).expanduser().resolve()

    if not video_path.exists():
        print(f"File not found: {video_path}")
        sys.exit(1)

    # Load video
    video = load_video(video_path)

    # Display info
    print("\nVideo Loaded Successfully")
    print(f"File: {video_path}")
    print(f"Resolution: {video.w} x {video.h}")
    print(f"Duration: {video.duration:.2f} seconds")
    print(f"Frame Rate (FPS): {video.fps}\n")

    # AUDIO CLEANING
    print("\nAudio Cleaning and Extraction...")

    # Your Cleanvoice API key
    api_key = "YOUR API HERE"

    cleaned_audio_file = process_audio_with_cleanvoice(video_path, api_key)
    print(f"Cleaned audio file: {cleaned_audio_file}\n")

    # MERGE CLEANED AUDIO BACK INTO VIDEO
    print("Merging cleaned audio back into the video...")

    cleaned_audio = mp.AudioFileClip(cleaned_audio_file)
    final_video = video.set_audio(cleaned_audio)

    output_video_path = video_path.with_stem(video_path.stem + "_cleaned")
    output_video_file = str(output_video_path) + ".mp4"

    final_video.write_videofile(
        output_video_file,
        codec="libx264",
        audio_codec="aac",
        verbose=False,
        logger=None
    )


    # FACIAL EXPRESSION ANALYSIS
    # Placeholder for emotion detection and facial expression recognition.


    # SUBTITLE GENERATION & SYNCHRONIZATION
    # Placeholder for generating emotion-aware subtitles.


    # FINAL OUTPUT / SAVE RESULTS
    # Placeholder for rendering or saving results.

    print(f"\nFinal video created: {output_video_file}")
    print("Processing complete.")
    
# ENTRY POINT 
if __name__ == "__main__":
    main()
