YouTube Automation Engine
1. Project Concept
This software is a fully autonomous "Faceless Channel" generator. It functions as a virtual production studio where different Python modules act as specialized employees (Writer, Editor, Artist, Manager).

The system is designed to generate high-retention content in two distinct formats:

YouTube Shorts: Fast-paced, vertical (9:16), under 60 seconds.

Long Form Documentaries: Cinematic, horizontal (16:9), 10+ minutes long.

Unlike basic automation scripts, this engine features "Smart Logic" to handle aspect ratios, music sentiment, and automated decision-making without user intervention.

2. Technical Architecture & Features
We developed this bot through several distinct phases of logic refinement. Below are the key systems implemented:

A. The AI Writer (Groq & Llama 3)
API: Uses Groq for ultra-fast inference.

Logic: Implements a "Chunking Strategy" for long-form content. Instead of asking for a 1500-word script at once (which AI often fails at), it generates the script in three distinct parts (Intro, Body, Conclusion) and stitches them together to guarantee 10+ minute durations.

Brainstorming: Includes a "Creative Partner" mode that reads your history.txt and suggests 10 fresh, viral topics you haven't covered yet.

B. The Visual Engine (Smart Scale-to-Fill)
Source: Fetches stock footage from Pexels and Pixabay.

Smart Crop: Implements a mathematical "Scale-to-Fill" algorithm. It calculates the exact zoom factor required to cover the target screen (Vertical or Horizontal) and centers the footage. This eliminates black bars and prevents "blank strip" errors.

Strict Filtering: Automatically rejects landscape videos when making Shorts, and portrait videos when making Long Form, ensuring high production value.

C. The Audio Engineer (Smart Tagging & Randomization)
Voice: Uses Edge TTS with a +10% speed increase for better retention.

Music Library: Replaces folder-based sorting with a "Master Library" system. Files are tagged via filenames (e.g., Epic_Action_Sad.mp3). The bot scans keywords to find tracks that match the video's mood, allowing one file to serve multiple genres without duplication.

Transitions: Scans an assets/transitions/ folder and randomly selects different SFX (Swoosh, Pop, Glitch) for every scene change to prevent repetition.

D. The Editor (Turbo Render)
Multi-Threading: The rendering engine utilizes threads=MAX_CORES to unlock multi-core CPU processing.

Optimization: "Ken Burns" (Dynamic Zoom) effects are disabled for Long Form videos to prevent CPU bottlenecks, ensuring 10-minute videos render in ~30 minutes instead of 4+ hours.

Subtitle Logic: Hardcoded positioning ensures subtitles appear in the "Safe Zone" (Bottom 20%) for cinematic videos, preventing them from overlapping with headers or faces.

E. Auto-Pilot (Timeouts)
Hands-Free: The system includes a timer on all user inputs. If no input is detected within 60 seconds, the bot automatically selects default values (Brainstorm Topic -> Upbeat Music -> Upload to YouTube), allowing for fully unattended operation.

3. Installation & Setup
Prerequisites
Python 3.10+

ImageMagick (Required for text rendering)

FFmpeg (Installed via MoviePy)

Dependencies
Install the required libraries:

Bash

pip install moviepy requests edge-tts google-api-python-client google-auth-oauthlib google-auth-httplib2 groq numpy pandas

Folder Structure
Ensure your project directory is set up as follows:

Plaintext

/project_root
 │
 ├── bot.py                 # Main entry point (The Manager)
 ├── config.py              # Settings and API keys
 ├── generators.py          # Script writing and asset gathering
 ├── media_engine.py        # Video editing and rendering
 ├── effects.py             # Visual effects and thumbnails
 ├── studio.py              # YouTube Upload API and Sheets logging
 │
 ├── /assets
 │    ├── transition.mp3    # Fallback sound
 │    ├── subscribe.mp4     # Green screen overlay
 │    ├── outro.mp4         # (Optional) Fixed outro video
 │    └── /transitions      # Add multiple .mp3 files here (pop, swoosh)
 │
 ├── /songs
 │    └── /Master_Library   # Put ALL mp3 files here. Name them with keywords.
 │
 └── /history.txt           # Stores list of created videos
4. Configuration
Open config.py to set your API keys and preferences.

API Keys: Add your Groq, Pexels, and Google API keys.

Channel Name: Update the CHANNEL_NAME variable for watermarks.

Video Settings: You can adjust max_scenes to control video length. (Recommended: 150 scenes for 10-minute videos).

5. How to Use
Manual Mode
Run the bot: python bot.py

Select your mode: 1 for Shorts, 2 for Long Form.

Select a topic: Choose "Brainstorm" to get ideas or type your own.

Select Music: Choose a mood (e.g., Thrilling, Sad).

Review: The bot will pause after rendering. Watch the video file.

Upload: Type y to upload to YouTube automatically.

Auto-Pilot Mode
Run the bot: python bot.py

Do nothing.

After 60 seconds, the bot will automatically:

Select Long Form mode.

Brainstorm a viral topic.

Select "Upbeat" music.

Generate the video.

Wait 10 minutes (for render/review buffer) and then auto-upload to YouTube.

6. Common Issues & Fixes (New Device Setup)
Problem: Rendering takes 3+ hours
Cause: "Ken Burns" (Zoom) effect forces single-core processing on every pixel.

Fix: Ensure you are using the latest media_engine.py which has "Static Mode" enabled. This utilizes multi-threading (threads=8) and drops render time to ~30 minutes.

Problem: "Blank Strip" or Black Bars in Video
Cause: Trying to fit a Landscape video into a Vertical Short (or vice versa).

Fix: The bot now uses a "Scale-to-Fill" mathematical formula. It calculates the exact zoom needed to cover the screen and crops the excess.

Problem: Subtitles are missing or metadata empty
Cause: Special characters in the script (like # or *) confuse the TTS engine.

Fix: The generators.py file now includes a text cleaner regex to strip these characters before generating audio.

Problem: "MoviePy Error: ImageMagick binary not found"
Cause: ImageMagick is not installed or not in the system PATH.

Fix: Install ImageMagick. Open config.py and ensure IMAGEMAGICK_PATH points to the magick.exe file (e.g., C:\Program Files\ImageMagick...\magick.exe).

Problem: "OSError: MoviePy error: the file is not an audio file"
Cause: You likely pasted a Shortcut (.lnk) file into the songs folder instead of the actual .mp3.

Fix: Only put actual .mp3 files in the /songs/Master_Library folder.
License & Usage Rights:

This software is the result of significant personal effort and development time. It is intended for personal use and demonstration purposes only.

Do Not Distribute: You are not permitted to copy, reproduce, distribute, or sell this source code, in whole or in part, without explicit written permission.

No Commercial Derivatives: Creating commercial products or services based on this specific codebase is strictly prohibited.

Thank you for respecting the hard work that went into building this automation engine.