"""
AUDIO CLEANING & EXTRACTION (Cleanvoice AI)
"""
from cleanvoice import Cleanvoice
from moviepy.editor import VideoFileClip


def extract_audio_from_video(video_path, output_audio_path="extracted_audio.wav"):
    """Extracts the audio track from a video file and saves it as a WAV file."""
    try:
        print("Extracting audio from video...")
        video = VideoFileClip(str(video_path))
        video.audio.write_audiofile(output_audio_path, verbose=False, logger=None)
        video.close()
        print(f"Audio extracted successfully: {output_audio_path}")
        return output_audio_path
    except Exception as e:
        print(f"Error extracting audio: {e}")
        raise


def process_audio_with_cleanvoice(video_path, api_key):
    """
    Extracts audio from a video, processes it using Cleanvoice AI,
    and saves a plain text transcript (no timestamps, no summary).
    
    Returns:
        str: Path to the cleaned audio file
    """

    # Extract audio from video
    audio_path = extract_audio_from_video(video_path, "extracted_audio.wav")
    print(f"Audio extracted: {audio_path}")

    # Initialize Cleanvoice SDK
    print("Initializing Cleanvoice SDK...")
    cv = Cleanvoice({'api_key': api_key})

    # Process audio with AI-powered cleaning
    print("Processing audio with AI-powered cleaning...")
    result, output_path = cv.process_and_download(
        audio_path,
        "cleaned_audio.wav",
        {
            "remove_noise": True,
            "transcription": True
        }
    )

    # Display results
    print("\nAudio processing complete!")
    print(f"Cleaned audio saved as: {output_path}")

    # Extract transcript text
    if result.transcript and result.transcript.text:
        transcript_text = result.transcript.text
    else:
        transcript_text = "No transcript returned."

    # Save transcript to file
    with open("transcript.txt", "w", encoding="utf-8") as f:
        f.write(transcript_text)

    print("Transcript saved to transcript.txt")

    return output_path