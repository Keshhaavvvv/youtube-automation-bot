AI Dual-Channel Automation Engine
1. Project Concept
This software is a high-frequency autonomous video production engine designed to operate a "Faceless Channel" ecosystem. Unlike standard automation tools that target a single demographic, this system implements a Dual-Channel Architecture. It generates viral short-form and long-form content in English and simultaneously adapts, translates, and renders a localized version for the Hindi (Indian) market.

The engine functions as a virtual production studio, orchestrating distinct modules for scripting, asset retrieval, translation, audio synchronization, and video rendering. It is engineered for high retention, utilizing psychometric hooks and algorithmic pacing to maximize viewer engagement on platforms like YouTube Shorts.

2. Technical Architecture & Features
The system operates on a modular architecture, allowing for independent upgrades to specific components. Below are the core subsystems:

A. The Retention-Focused Writer (Groq & Llama 3)
Negative Hook Strategy: The AI is prompted to generate scripts that utilize "Negative Pattern Interrupts" (e.g., "Stop doing this," "You are being lied to") to prevent scroll-past behavior.

Loop Logic: Scripts are engineered with circular narratives where the ending sentence grammatically flows back into the opening hook, encouraging repeated viewing sessions.

Topic Exclusion: A persistent history log ensures the AI never generates duplicate content, forcing it to brainstorm novel topics based on real-time trends or deep psychological analysis.

B. The Dual-Channel Translation Engine
Contextual Hinglish: The system does not use literal translation. It employs a dedicated AI agent to rewrite English scripts into "Viral Urban Hinglish"—a natural blend of Hindi and English widely consumed in India.

Tone Preservation: The translator is instructed to maintain the specific emotional tone (Dark, Upbeat, Mystery) of the original script, replacing idioms rather than translating them word-for-word.

Asset Reuse: To maximize efficiency, the system generates visual assets (stock footage, AI images, background music) once for the English video and reuses them for the Hindi render, significantly reducing API usage and render times.

C. Visual Engine & Smart Rendering
Direct FFmpeg Compositing: The engine bypasses standard editing overhead by calculating exact pixel coordinates for cropping and resizing. This eliminates "odd-pixel" crashes (e.g., 1079px vs 1080px) and ensures strictly compliant 9:16 or 16:9 output.

Hybrid Sourcing: The system dynamically selects between Pexels/Pixabay stock footage for realistic scenes and Pollinations AI image generation for abstract or impossible concepts (e.g., "Cyberpunk Ancient Rome").

Smart Fill: A mathematical "Scale-to-Fill" algorithm calculates the precise zoom factor required to fit horizontal footage into vertical screens without black bars or blank strips.

D. Audio Engineering (Elastic Sync)
Elastic Synchronization: Hindi audio is often 20-30% longer than English. The system measures the duration of the generated Hindi audio and mathematically stretches or compresses the subtitle timestamps to ensure perfect synchronization without drifting.

Smart Volume Logic: Sound effects are dynamically leveled based on type. "Impact" sounds are boosted (1.2x), while repetitive sounds like "Dings" are attenuated (0.6x) to prevent listener fatigue.

Speed Control: Voiceovers are generated at +15% speed to match the fast-paced nature of modern short-form content.

3. Installation & Setup
Prerequisites
Python 3.10+

ImageMagick (Required for dynamic text rendering)

FFmpeg (Essential for video encoding)

Dependencies
Install the required Python libraries:
pip install moviepy requests edge-tts google-api-python-client google-auth-oauthlib google-auth-httplib2 groq numpy pandas imageio-ffmpeg

Folder Structure
Ensure your project directory is organized as follows:
/project_root
 │
 ├── bot.py                 # Main Orchestrator (The Manager)
 ├── config.py              # Configuration and API Keys
 ├── generators.py          # Scripting, Translation, and Asset Gathering
 ├── media_engine.py        # Video Editing, Compositing, and FFmpeg logic
 ├── studio.py              # YouTube API Authentication and Uploads
 ├── translator.py          # Dedicated Hindi/Hinglish Logic
 │
 ├── /assets
 │    ├── /sfx              # Sound effects (pop.mp3, whoosh.mp3)
 │    └── /transitions      # Visual/Audio transition assets
 │
 ├── /temp                  # Temporary storage for current session assets
 └── history.txt            # Database of previously generated topics

 4. Configuration
Open config.py to configure your environment:

API Keys: Input valid keys for Groq (AI), Pexels (Stock), and Google (YouTube Data API).

Channel Profiles: Configure client_secrets_english.json and client_secrets_hindi.json for dual-channel authentication.

Render Settings: Adjust VIDEO_MODE defaults (Shorts/Long) and thread counts based on your CPU capabilities.

5. How to Use
Operation Modes
Run the system via the command line: python bot.py

Video Format Selection: Choose between Shorts (Vertical) or Long Form (Horizontal).

Target Audience:

English Only: Generates and uploads to the US channel.

Hindi Only: Generates the English master (skipped render) and produces the Hindi version.

Both: Full Dual-Channel automation.

Topic Selection: Choose from Real-Time Trends (News/Finance), AI Brainstorming, or Manual Input.

Auto-Pilot
If no input is provided within 60 seconds, the system defaults to "Auto-Pilot Mode." It will automatically select "Both Channels," generate a viral topic, produce the content, and upload to the respective YouTube channels without human intervention.

6. Dual-Channel Workflow
The system follows a strict linear pipeline to ensure consistency across languages:

Script Generation: The AI writes a high-retention English script.

Asset Acquisition: Stock footage and AI art are gathered based on English keywords.

English Production: Audio is generated, and the English video is rendered (or skipped if "Hindi Only" is selected).

Translation: The script is passed to the Translation Engine for Hinglish adaptation.

Audio Replacement: Hindi voiceovers are generated using neural voices (Swara/Madhur).

Re-Compositing: The original visual timeline is preserved, but audio tracks and subtitles are swapped for the Hindi counterparts.

Deployment: Metadata (Titles/Tags) is translated and optimized for high-CTR keywords before uploading to the respective channels.

7. License & Usage Rights
This software is the result of proprietary development and is intended for personal use and demonstration purposes only.

Do Not Distribute: You are not permitted to copy, reproduce, distribute, or sell this source code, in whole or in part, without explicit written permission.

No Commercial Derivatives: Creating commercial products or "Software as a Service" (SaaS) platforms based on this specific codebase is strictly prohibited.