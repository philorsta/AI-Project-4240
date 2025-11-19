Environment setup and run instructions

1) Open PowerShell and change to the project directory:

   cd "C:\Users\logan\OneDrive\Documents\SeniorFall\A. I\final project\AI-Project-4240\emotion_recognition"

2) Run the setup script to create a virtual environment and install dependencies:

   .\setup_env.ps1

   - This creates a `.venv` folder and installs packages listed in `requirements.txt`.
   - If you already have a venv you can skip creation; pass -NoInstall to skip package installation.

3) Activate the venv in your interactive shell:

   .\.venv\Scripts\Activate.ps1

4) Run the script (example):

   # GUI mode (press 'q' in the window to quit)
   python .\script.py videos\your_video.mp4

   # Headless mode (no video window)
   python .\script.py videos\your_video.mp4 --no-display

Notes:
- The `requirements.txt` includes: deepface, opencv-python, tensorflow-cpu, keras.
- If your teammate has a GPU and prefers GPU TensorFlow, they can install `tensorflow` inside the venv instead of `tensorflow-cpu`.
- If Python is not found when running the setup script, install Python 3.8+ and ensure the `python` command is available on PATH.
