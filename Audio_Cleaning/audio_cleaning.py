# AUDIO CLEANING & EXTRACTION (Cleanvoice AI)
from cleanvoice import Cleanvoice
from moviepy.editor import VideoFileClip

# pip install cleanvoice-sdk


def extract_audio_from_video(video_path, output_audio_path="audio.wav"):
    # Extracts the audio track from a video file and saves it as a WAV file.
    try:
        print("Extracting audio from video...")
        video = VideoFileClip(str(video_path))
        video.audio.write_audiofile(output_audio_path, verbose=False, logger=None)
        print(f"Audio extracted successfully: {output_audio_path}")
        return output_audio_path
    except Exception as e:
        print(f"Error extracting audio: {e}")
        raise


def process_audio_with_cleanvoice(video_path, api_key):
    """
    Extracts audio from a video, processes it using Cleanvoice AI (v2),
    and saves a plain text transcript (no timestamps, no summary).
    """

    # --- AUDIO EXTRACT ---
    audio_path = extract_audio_from_video(video_path, "extracted_audio.wav")
    print(f"Audio extracted: {audio_path}")

    # --- CLEANVOICE ---
    print("Initializing Cleanvoice SDK...")
    cv = Cleanvoice({'api_key': api_key})

    print("Processing audio with AI-powered cleaning...")
    result, output_path = cv.process_and_download(
        audio_path,
        "cleaned_audio.wav",
        {
            "remove_noise": True,
            "transcription": True
        }
    )

    # --- CLEANVOICE RETURNED RESULTS ---
    print("\n Audio cleaned successfully!")
    print(f"Cleaned audio saved as: {output_path}")

    # --- Extract simple transcript (no timestamps, no summary) ---
    if result.transcript and result.transcript.text:
        transcript_text = result.transcript.text
    else:
        transcript_text = "No transcript returned."

    # --- SAVE TRANSCRIPT FILE ---
    with open("transcript.txt", "w") as f:
        f.write(transcript_text)

    print("Transcript saved to transcript.txt")

    return output_path
