"""
AI Assisted Communication for Video Presentations
-------------------------------------------------
Course: Artificial Intelligence 4240-001 — Fall 2025

Description:
    Complete pipeline that:
    1. Extracts and cleans audio using Cleanvoice AI
    2. Processes video for emotion recognition with overlays
    3. Combines cleaned audio with emotion-overlayed video
    4. Generates transcript
"""

# IMPORTS 
import os
import sys
import moviepy.editor as mp
from pathlib import Path
from audio_cleaning import process_audio_with_cleanvoice
from emotion_recognition import process_video_emotions


# LOAD VIDEO
def load_video(video_path):
    """Load and validate video file"""
    try:
        video = mp.VideoFileClip(str(video_path))
        return video
    except Exception as e:
        print(f"Error loading video: {e}")
        sys.exit(1)


# MAIN
def main():
    print("=" * 60)
    print("AI Assisted Communication Project")
    print("=" * 60)

    # ============================================
    # USER INPUT SECTION
    # ============================================
    path_input = input("\nEnter or drag your video file here: ").strip().strip('"')
    video_path = Path(path_input).expanduser().resolve()

    if not video_path.exists():
        print(f"File not found: {video_path}")
        sys.exit(1)

    # Load video for initial info
    video = load_video(video_path)

    # Display info
    print("\n" + "=" * 60)
    print("VIDEO LOADED SUCCESSFULLY")
    print("=" * 60)
    print(f"File: {video_path.name}")
    print(f"Resolution: {video.w} x {video.h}")
    print(f"Duration: {video.duration:.2f} seconds")
    print(f"Frame Rate (FPS): {video.fps}")
    print("=" * 60)

    # ============================================
    # STEP 1: AUDIO CLEANING & EXTRACTION
    # ============================================
    print("\n" + "=" * 60)
    print("STEP 1: AUDIO CLEANING AND EXTRACTION")
    print("=" * 60)

    # Your Cleanvoice API key
    api_key = "cvk_kqE3fsqXlIo.3WtXo1GmnhPkd04m3zZHPel1wBdYBtvAqFTQBcIoiaA"

    try:
        cleaned_audio_file = process_audio_with_cleanvoice(str(video_path), api_key)
        print(f"✓ Cleaned audio saved: {cleaned_audio_file}")
        print(f"✓ Transcript saved: transcript.txt")
    except Exception as e:
        print(f"Error in audio processing: {e}")
        sys.exit(1)
        
    # ============================================
    # STEP 2: FACIAL EXPRESSION ANALYSIS
    # ============================================
    print("\n" + "=" * 60)
    print("STEP 2: EMOTION RECOGNITION")
    print("=" * 60)

    # Create temporary emotion-overlayed video (no audio)
    emotion_video_path = video_path.with_stem(video_path.stem + "_emotion_temp").with_suffix(".mp4")
    
    try:
        process_video_emotions(str(video_path), str(emotion_video_path))
        print(f"✓ Emotion analysis complete: {emotion_video_path}")
    except Exception as e:
        print(f"Error in emotion processing: {e}")
        sys.exit(1)

    # ============================================
    # STEP 3: COMBINE CLEANED AUDIO WITH EMOTION VIDEO
    # ============================================
    print("\n" + "=" * 60)
    print("STEP 3: MERGING CLEANED AUDIO WITH EMOTION VIDEO")
    print("=" * 60)

    try:
        # Load emotion video (no audio) and cleaned audio
        emotion_video_clip = mp.VideoFileClip(str(emotion_video_path))
        cleaned_audio_clip = mp.AudioFileClip(cleaned_audio_file)
        
        # Combine them
        final_video = emotion_video_clip.set_audio(cleaned_audio_clip)
        
        # Create output filename
        output_video_path = video_path.with_stem(video_path.stem + "_final")
        output_video_file = str(output_video_path.with_suffix(".mp4"))
        
        print("Writing final video (this may take a moment)...")
        final_video.write_videofile(
            output_video_file,
            codec="libx264",
            audio_codec="aac",
            verbose=False,
            logger=None
        )
        
        # Cleanup
        emotion_video_clip.close()
        cleaned_audio_clip.close()
        final_video.close()
        
        print(f"✓ Final video created: {output_video_file}")
        
    except Exception as e:
        print(f"Error merging audio and video: {e}")
        sys.exit(1)

    # ============================================
    # CLEANUP TEMPORARY FILES (OPTIONAL)
    # ============================================
    try:
        # Remove temporary emotion video
        if emotion_video_path.exists():
            emotion_video_path.unlink()
            print(f"✓ Cleaned up temporary file: {emotion_video_path.name}")
    except Exception as e:
        print(f"Note: Could not remove temporary file: {e}")

    # ============================================
    # FINAL SUMMARY
    # ============================================
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE!")
    print("=" * 60)
    print("\nOutput Files:")
    print(f"  • Final Video: {output_video_file}")
    print(f"  • Cleaned Audio: {cleaned_audio_file}")
    print(f"  • Transcript: transcript.txt")
    print("\n" + "=" * 60)

    # Close original video
    video.close()


# ENTRY POINT 
if __name__ == "__main__":
    main()