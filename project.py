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


# LOAD VIDEO
def load_video(video_path):
    """
    Loads a video file using MoviePy.

    Args:
        video_path (Path): The path to the video file selected by the user.

    Returns:
        moviepy.video.io.VideoFileClip.VideoFileClip: The loaded video object.
    """
    try:
        video = mp.VideoFileClip(str(video_path))
        return video
    except Exception as e:
        print(f"Error loading video: {e}")
        sys.exit(1)


# MAIN
def main():
    """
    Main entry point for the AI Assisted Communication project.

    Step 1: Load a user-specified video file.
    Step 2: Display video metadata (duration, FPS, resolution).
    Step 3: Provide placeholder sections for AI processing tasks.
    """
    print("AI Assisted Communication Project")
    print("---------------------------------------------------")

    # USER INPUT SECTION 
    # Ask user to type or drag their video file path into the terminal.
    path_input = input("Enter or drag your video file here: ").strip().strip('"')

    # Convert input to an absolute path (cross-platform compatible)
    video_path = Path(path_input).expanduser().resolve()

    # Check that the file actually exists before continuing
    if not video_path.exists():
        print(f"File not found: {video_path}")
        sys.exit(1)

    # LOAD VIDEO 
    video = load_video(video_path)

    # DISPLAY BASIC INFORMATION 
    print("\nVideo Loaded Successfully")
    print(f"File: {video_path}")
    print(f"Resolution: {video.w} x {video.h}")
    print(f"Duration: {video.duration:.2f} seconds")
    print(f"Frame Rate (FPS): {video.fps}\n")


    # AUDIO CLEANING & EXTRACTION
    # Placeholder for integrating audio noise reduction and voice isolation.


    # FACIAL EXPRESSION ANALYSIS
    # Placeholder for emotion detection and facial expression recognition.


    # SUBTITLE GENERATION & SYNCHRONIZATION
    # Placeholder for generating emotion-aware subtitles.


    # FINAL OUTPUT / SAVE RESULTS
    # Placeholder for rendering or saving results.


# ENTRY POINT 
if __name__ == "__main__":
    main()
