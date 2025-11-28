# Environment Setup and Run Instructions

## Prerequisites

- **Python 3.8 or higher** installed on your system
- **PowerShell** (comes with Windows)
- **Internet connection** for downloading packages (~2GB total)

---

## Quick Setup (3 Steps)

### 1. Open PowerShell and Navigate to Project Directory

```powershell
cd "C:\path\to\AI-Project-4240\deliverable_directory"
```

Replace the path with your actual project location.

### 2. Run the Setup Script

```powershell
.\setup_env.ps1
```

This will:
- Create a `.venv` folder (virtual environment)
- Install all required packages from `requirements.txt`
- Takes 5-10 minutes depending on your internet speed

**Optional flags:**
```powershell
.\setup_env.ps1 -VenvPath "custom_venv"  # Use custom venv folder name
.\setup_env.ps1 -NoInstall               # Skip package installation
```

### 3. Activate the Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

You should see `(.venv)` appear before your command prompt.

---

## Running the Project

Once your virtual environment is activated:

```powershell
python project.py
```

The program will prompt you to:
1. Enter or drag your video file
2. Wait while it processes (audio cleaning + emotion recognition)
3. Find your output files in the same directory

### Output Files
- `{filename}_final.mp4` - Final video with cleaned audio and emotion overlays
- `cleaned_audio.wav` - Cleaned audio file
- `transcript.txt` - Transcript from Cleanvoice AI

---

## Package Details

The `requirements.txt` includes:

| Package | Version | Purpose |
|---------|---------|---------|
| moviepy | 1.0.3 | Video processing and editing |
| opencv-python | 4.8.1.78 | Computer vision and frame processing |
| deepface | 0.0.79 | Facial emotion recognition |
| tensorflow | 2.15.0 | Deep learning backend |
| tf-keras | 2.15.0 | Keras API for TensorFlow |
| cleanvoice-sdk | 0.1.0 | Audio cleaning and transcription |

---

## Troubleshooting

### Python Not Found
- Install Python from [python.org](https://www.python.org/downloads/)
- Make sure to check "Add Python to PATH" during installation
- Restart PowerShell after installation

### HTTP 401 Error
- Missing api key. Make an account on cleanvoice and grab an api key
- Populate api key in project.py line 71

### Execution Policy Error
If you get "cannot be loaded because running scripts is disabled":
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Package Installation Fails
- Make sure you have a stable internet connection
- Try running with administrator privileges
- Update pip: `python -m pip install --upgrade pip`

### GPU Support
- The default installation uses CPU-only TensorFlow
- For GPU acceleration (if you have an NVIDIA GPU):
  ```powershell
  pip uninstall tensorflow
  pip install tensorflow-gpu==2.15.0
  ```

### Cleanvoice API Issues
- If you get HTTP 502 errors, the Cleanvoice server may be temporarily down
- The pipeline will continue using the original audio
- Wait a few minutes and try again if you need the cleaning feature

### Cleanvoice API Key

- **Important:** Populate the Cleanvoice API key in `project.py` on line 71 before running the script. Replace the placeholder string with your Cleanvoice account API key, or set the `CLEANVOICE_API_KEY` environment variable if the code reads from it. The audio cleaning/transcription step will not work without a valid API key.

---

## Deactivating the Virtual Environment

When you're done:
```powershell
deactivate
```

---

## Team Member Setup

Share these files with your team:
- `setup_env.ps1`
- `requirements.txt`
- `README_ENV.md`
- All `.py` files
- `emoji/` folder

They just need to:
1. Clone/copy the project folder
2. Run `.\setup_env.ps1`
3. Activate venv `.\.venv\Scripts\Activate.ps1run`
4. Run `python project.py`

---

## Notes

- The virtual environment folder (`.venv`) is ~2GB after installation
- First run may take longer as DeepFace downloads pre-trained models
- Video processing time depends on video length and resolution
- For best results, use videos with clear facial expressions