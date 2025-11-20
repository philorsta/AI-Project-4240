# AI Assisted Communication for Video Presentations

## OVERVIEW
___
Effective communication is often challenging.
In the last half-decade, video-over-IP has become much more important than it
had been. The pandemic of the early 2020s forced people into quarantine, and
effectively, social isolation. It became apparent that phone calls were not
enough to replace face-to-face meetings. Apps like Zoom, Skype, and Facetime
were suddenly at the forefront of the world’s attention and many found that
these tools offered relief from the loneliness of isolation. These apps became
such a part of the public consciousness that even as public spaces began to
populate again, these technologies stuck around. They are still being used
daily and are now a fundamental part of business and education.

Though these apps gave an answer to one of the biggest questions of this
decade, they came with some inadequacies. The subtle-but-many problems
permeating telecommunications: poor connections, dropped packets, noises that
are amplified by integrated microphones, the loss of information inherent in
compression algorithms necessary to transfer enormous video files across the
internet, all frustrate communication. This project offers a solution in three
parts.

Before audio gets distorted by compression, an AI powered tool will isolate the
speaker’s voice, attenuate competing frequencies, and accentuate the
frequencies that best carry speech information. Packet loss can turn the
speaker’s face into a pixelated mask. An AI tool will map the speaker’s face,
generate a simplified representation, and overlay the result unobtrusively
alongside the speaker. As a final measure to facilitate the best communication
achievable, an AI tool will generate subtitles; a reliable method for syntax,
but hardly a replacement for speech or somatic expression alone.
___
## GOALS

Create an application that utilizes AI tools to:
Clean audio for voice clarity
Read facial expressions and generate simplified depictions
Generate subtitles
Aid those with sight impairments, autism, and bad internet connections.
___
## TOOLS

- Krisp - audio cleaning and voice isolation
- Facial recognition software - TBD - determine facial expressions
- Subtitling software - TBD - generate subtitles

We will likely discover tools are a better fit for this project as we research
this topic further.
___
## Open Allocation Contribution Method

- Choose a task from the Trello board, or create tasks using the Trello board
- Create a branch with title of the Trello card you are working on. When you
  are finished, submit a pull request with a description of the feature
- Add a link or tag to the related Trello card
___
## Development Setup

Docker instructions here
___
## Design Overview

Link to high-level flowchart or design here

---

# Audio Cleaning & Transcription (Implementation Details)

This project processes video files by automatically:

1. **Extracting the audio track**
2. **Cleaning the audio using Cleanvoice’s AI engine**
3. **Saving a cleaned audio file**
4. **Generating a full transcription**
5. **Saving the transcription as a `.txt` file**
6. **Replacing the original video’s audio with the cleaned version**

All audio logic is implemented inside `audio_cleaning.py`.

---

## Required Installations

Before running the project locally, install:

```bash
pip install moviepy
pip install cleanvoice-sdk
pip install requests

## Cleanvoice API Key Setup

To use Cleanvoice for audio cleaning and transcription, you **must supply your API key**.

How to get a Cleanvoice API Key :

1. Go to: https://cleanvoice.ai/api
2. Create an account (free trial usually available)
3. Navigate to Dashboard → API Keys
4. Click Create API Key
5. Copy the generated key

### **Where to put the API key**
Inside `project.py`, the key is defined here:

```python
api_key = "YOUR_API_KEY_HERE"

