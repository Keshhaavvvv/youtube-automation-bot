# media_engine.py
import os
from moviepy.config import change_settings
# --- CRITICAL CONFIGURATION ---
# Point to your exact ImageMagick installation
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})
import random
import warnings
import math
import json
import glob
import gc 
import subprocess 
import imageio_ffmpeg 
import numpy as np  # <--- CRITICAL: Needed for audio arrays
from moviepy.config import get_setting 
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips, TextClip, CompositeVideoClip, ImageClip, concatenate_audioclips, ColorClip
from moviepy.audio.fx.all import audio_loop, volumex, audio_fadeout, audio_fadein
from moviepy.video.fx.all import fadein, fadeout
from moviepy.audio.AudioClip import AudioArrayClip # <--- CRITICAL: Needed for safe audio loading
import effects 
import config 
import generators
import textwrap

# Suppress Warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- CONFIG: SMART SFX LIBRARY ---
SMART_SFX_MAP = {
    "money": "cash.mp3", "rich": "cash.mp3", "profit": "cash.mp3",
    "scary": "horror_hit.mp3", "dark": "horror_hit.mp3", "mystery": "mystery_swoosh.mp3",
    "idea": "ding.mp3", "solution": "ding.mp3",
    "fast": "whoosh_fast.mp3", "speed": "whoosh_fast.mp3",
    "computer": "type.mp3", "hack": "glitch.mp3", "error": "glitch.mp3",
    "clock": "clock.mp3", "crowd": "crowd.mp3",
    "galaxy": "galaxy.mp3", "space": "galaxy.mp3", "outerspace": "outer_space.mp3",
    "network": "network.mp3",
    "warning": "warning.mp3", "alert": "warning.mp3", "alarm": "alarm.mp3",
    "rain": "rain.mp3", "thunder": "thunder.mp3",
    "explosion": "explosion.mp3", "fire": "fire.mp3",
    "beach": "sea.mp3", "ocean": "ocean.mp3",
    "success": "success.mp3", "win": "success.mp3",
    "failure": "failure.mp3", "lose": "failure.mp3",
    "storm": "storm.mp3", "wind": "wind.mp3", "zombie": "zombie.mp3", "woodpecker": "woodpecker.mp3", "door": "door.mp3", "shatter": "shatter.mp3"
}

# --- CONFIG: VISUAL OVERLAY MAP (Emoji/PNG) ---
# Add this under SMART_SFX_MAP
EMOJI_MAP = {
    "money": "money.png", "cash": "money.png", "rich": "money.png", "profit": "money.png",
    "secret": "shh.png", "quiet": "shh.png", "hidden": "shh.png", "mystery": "shh.png",
    "love": "heart.png", "heart": "heart.png",
    "scary": "skull.png", "death": "skull.png", "dead": "skull.png", "kill": "skull.png", "danger": "skull.png",
    "laugh": "joy.png", "funny": "joy.png", "lol": "joy.png",
    "shock": "scream.png", "omg": "scream.png", "wow": "scream.png", "crazy": "scream.png",
    "fire": "fire.png", "hot": "fire.png", "burn": "fire.png",
    "brain": "brain.png", "smart": "brain.png", "idea": "bulb.png", "think": "brain.png",
    "alien": "alien.png", "ufo": "alien.png",
    "robot": "robot.png", "ai": "robot.png", "bot": "robot.png",
    "stop": "stop.png", "warning": "stop.png", "alert": "stop.png",
    "cool": "sunglasses.png", "boss": "sunglasses.png","angry": "angry.png", "mad": "angry.png","rage": "angry.png",
    "wow": "wow.png", "surprised": "wow.png","shock": "wow.png","fish": "shark.png","ocean": "whale.png","sea": "whale.png",
}

# --- CONFIG: KEYWORD COLORS (Subtitle Animation) ---
KEYWORD_COLORS = {
    # --- EXISTING COLORS ---
    "red": [
        "stop", "danger", "warning", "wrong", "fail", "bad", "alert", "error", 
        "hot", "fight", "war", "attack", "crisis", "hate", "angry", "rage",
        "khatra", "gussa", "barbaad", "darr", "aag", "galti", "jhoot", "dhokha"
    ],
    
    "green": [
        "money", "rich", "cash", "profit", "success", "win", "growth", "dollar", 
        "million", "billion", "wealth", "invest", "lucky", "life", "nature", 
        "paisa", "kamai", "jeet", "munafa", "safalta", "ameer", "crorepati", "zindagi"
    ],
    
    "cyan": [
        "ai", "robot", "future", "tech", "digital", "data", "code", "cyber", 
        "internet", "screen", "system", "online", "network", "electric", "laser",
        "bhavishya", "bijli", "yantra", "dimag", "machine", "computer"
    ],
    
    "purple": [
        "secret", "hidden", "weird", "strange", "soul", "mind", "dream", "mystery", 
        "magic", "spell", "witch", "galaxy", "space", "universe", "void", "royal",
        "raaz", "jaadu", "sapna", "chudail", "aatma", "rahasya", "anjaan", "ajeeb"
    ],
    
    "deepskyblue": [
        "sad", "cry", "tears", "lonely", "alone", "ocean", "sea", "water", "rain", 
        "sky", "calm", "peace", "cold", "truth", "real", "police", "law", "blue",
        "rona", "aansu", "dukhi", "akela", "pani", "samundar", "sach", "neela", "shant"
    ],
    
    "orange": [
        "fast", "speed", "run", "quick", "now", "boom", "blast", "loud", "shout", 
        "scream", "crazy", "insane", "wild", "beast", "monster", "tiger", "lion",
        "bhaago", "jaldi", "tez", "dhamaka", "shor", "khatarnak", "josh", "janwar"
    ],
    
    "hotpink": [
        "love", "heart", "kiss", "sweet", "cute", "baby", "girl", "beauty", 
        "beautiful", "nice", "kind", "happy", "joy", "smile", "laugh", "fun",
        "pyaar", "mohabbat", "dil", "sundar", "khushi", "maza", "hansi", "pyara"
    ],

    "black": [
        "death", "dead", "die", "void", "abyss", "nothing", "empty", "end", 
        "finish", "gone", "lost", "corpse", "grave", "buried", "darkness", "shadow",
        "maut", "khatam", "sunsaan", "andhera", "kaala", "raakh", "murda", "kabar"
    ],

    "white": [
        "god", "angel", "heaven", "pure", "holy", "light", "bright", "shine", 
        "clean", "fresh", "spirit", "cloud", "snow", "white", "peace",
        "bhagwan", "khuda", "allah", "rooh", "safed", "pavitra", "swarg", "ujeala"
    ],

    # --- NEW COLORS ADDED ---

    # TOXIC / ALIEN / VIRUS (Lime Green)
    "lime": [
        # English
        "toxic", "poison", "acid", "virus", "alien", "ufo", "zombie", "infection", 
        "glitch", "hack", "bug", "radioactive", "slime", "snake", "venom", "envy",
        
        # Hinglish
        "zeher", "keeda", "bimari", "virus", "naag", "saamp", "jalan", "hari",
        "khatta", "kadwa", "dushman"
    ],

    # METAL / WEAPON / MACHINE (Silver)
    "silver": [
        # English
        "metal", "iron", "steel", "silver", "grey", "gun", "bullet", "sword", 
        "knife", "blade", "weapon", "armor", "robot", "machine", "engine", "car",
        
        # Hinglish
        "loha", "chandi", "hathyar", "bandook", "goli", "talwar", "chaaku", 
        "gaadi", "motor", "machine"
    ],

    # ANCIENT / EARTH / HISTORY (Saddle Brown)
    "saddlebrown": [
        # English
        "history", "ancient", "old", "past", "time", "clock", "earth", "mud", 
        "dirt", "ground", "floor", "wood", "tree", "root", "dirty", "dust",
        
        # Hinglish
        "itihas", "purana", "waqt", "samay", "mitti", "zameen", "dhool", 
        "ganda", "ped", "jungle", "khet"
    ],

    # HORROR / GORE / MURDER (Crimson - Darker Red)
    "crimson": [
        # English
        "blood", "bleed", "murder", "killer", "gore", "flesh", "bone", "skull", 
        "skeleton", "vampire", "demon", "satan", "cruel", "violent", "horror",
        
        # Hinglish
        "khoon", "katl", "hatya", "shaitan", "hadaddi", "kankal", "bhayankar", 
        "daravna", "rakshas", "paapi"
    ]
}

# --- SHARED HELPER: TEXT STYLE ---
def get_text_style(text):
    """Determines color, stroke, and scale based on keywords."""
    lower_text = text.lower()
    
    # Default Style (Yellow/Gold for standard emphasis)
    color = '#FFD700' 
    stroke = 'black'
    scale = 1.0
    
    # Check for keyword matches
    for color_name, keywords in KEYWORD_COLORS.items():
        # Check using Regex boundary or length > 4 logic to avoid partial matches
        if any(f" {k} " in f" {lower_text} " for k in keywords) or any(k in lower_text for k in keywords if len(k) > 4):
            
            # --- COLOR MAPPING ---
            if color_name == "red": color = '#FF0000'
            elif color_name == "green": color = '#00FF00'
            elif color_name == "cyan": color = '#00FFFF'
            elif color_name == "purple": color = '#DA70D6'
            elif color_name == "deepskyblue": color = '#00BFFF'
            elif color_name == "orange": color = '#FFA500'
            elif color_name == "hotpink": color = '#FF69B4'
            
            # --- NEW MAPPINGS ---
            elif color_name == "lime": color = '#32CD32'      # Toxic Green
            elif color_name == "silver": color = '#C0C0C0'    # Metal Grey
            elif color_name == "saddlebrown": color = '#8B4513' # Earthy Brown
            elif color_name == "crimson": color = '#DC143C'   # Blood Red
            
            # --- SPECIAL MODES (Black/White) ---
            elif color_name == "black": 
                color = '#000000'
                stroke = 'white'   # White Stroke for visibility
                scale = 1.3
                print(f"   [Subtitle] Highlighting '{text}' -> BLACK (Void Mode)")
                return color, stroke, scale
                
            elif color_name == "white":
                color = '#FFFFFF'
                stroke = 'black'   # Black Stroke for visibility
                scale = 1.2
                print(f"   [Subtitle] Highlighting '{text}' -> WHITE (Holy Mode)")
                return color, stroke, scale

            # Standard Pop Effect for colored words
            scale = 1.2
            stroke = 'white' 
            
            print(f"   [Subtitle] Highlighting '{text}' -> {color_name.upper()}")
            return color, stroke, scale
            
    return color, stroke, scale

# --- MUSIC SELECTOR (SMART TAGGING) ---
def get_music_mood():
    base_folder = "songs"
    master_library = os.path.join(base_folder, "Master_Library")
    
    moods = {
        "Thrilling": ["thrill", "action", "fast", "dark"],
        "Peaceful": ["peace", "calm", "ambient", "soft"],
        "Informative": ["info", "news", "beat", "tech"],
        "Upbeat": ["upbeat", "happy", "fun", "pop"],
        "Sad": ["sad", "emotional", "slow", "piano"]
    }
    
    if not os.path.exists(base_folder): os.makedirs(base_folder)
    if not os.path.exists(master_library): os.makedirs(master_library)
    for m in moods.keys():
        p = os.path.join(base_folder, m)
        if not os.path.exists(p): os.makedirs(p)

    print("\n   ---------------------------------------------------")
    print("   🎵 SELECT BACKGROUND MUSIC MOOD (Auto: Upbeat in 60s)")
    
    mood_list = list(moods.keys())
    
    for i, mood in enumerate(mood_list):
        folder_path = os.path.join(base_folder, mood)
        specific_count = len([f for f in os.listdir(folder_path) if f.endswith('.mp3')])
        
        master_matches = 0
        keywords = moods[mood]
        for f in os.listdir(master_library):
            if f.endswith(".mp3") and any(k in f.lower() for k in keywords):
                master_matches += 1
                
        total_count = specific_count + master_matches
        print(f"   {i+1}. {mood} ({total_count} songs)")
        
    print("   ---------------------------------------------------")
    
    choice_input = generators.smart_input("   > Enter number (1-5): ", timeout=60, default_value="4").strip()
    
    selected_mood = "Upbeat" # Default
    try:
        choice = int(choice_input)
        if 1 <= choice <= 5: 
            selected_mood = mood_list[choice-1]
    except: pass
    
    return selected_mood, moods[selected_mood]

# --- 1. PERFECT ENGINE (Metadata Based + ANIMATION + LOGGING) ---
def create_perfect_captions(timing_file_path):
    mode = config.VIDEO_MODE if hasattr(config, 'VIDEO_MODE') else "Shorts"
    font_size = config.VIDEO_SETTINGS[mode]["font_size"]

    if mode == "Shorts":
        text_pos = 'center'
    else:
        text_pos = ('center', 0.8)

    if not os.path.exists(timing_file_path): return []
    try:
        with open(timing_file_path, 'r', encoding='utf-8') as f:
            words = json.load(f)
        if not words: return [] 
    except: return []

    clips = []
    chunk_text = []
    chunk_start = None
    
    for i, w in enumerate(words):
        if chunk_start is None: chunk_start = w['start']
        chunk_text.append(w['word'])
        chunk_end = w['end']
        current_duration = chunk_end - chunk_start
        
        # Determine chunk size (Shorts needs faster pacing)
        chunk_limit = 2 if mode == "Shorts" else 3
        
        if (current_duration > 0.3 and len(chunk_text) >= 1) or len(chunk_text) >= chunk_limit or i == len(words)-1:
            full_text = " ".join(chunk_text).upper().strip()
            
            # --- USE SHARED COLOR LOGIC ---
            text_color, stroke_color, scale_factor = get_text_style(full_text)
            
            try:
                txt = TextClip(
                    full_text, 
                    fontsize=font_size, 
                    color=text_color, 
                    font='Arial-Bold', # Bold for impact
                    stroke_color=stroke_color, 
                    stroke_width=4, # Thicker stroke
                    method='label'
                )
                
                # Apply Pop Effect (Resize)
                if scale_factor > 1.0:
                    txt = txt.resize(scale_factor)
                
                if mode == "Shorts":
                    txt = txt.set_pos('center')
                else:
                    txt = txt.margin(bottom=50, opacity=0).set_pos(('center', 'bottom'))

                txt = txt.set_start(chunk_start).set_duration(current_duration)
                clips.append(txt)
            except Exception as e:
                print(f"   [Text Error] Perfect Engine failed: {e}")
            chunk_text = []
            chunk_start = None
    return clips
# --- HELPER: CREATE EMOJI OVERLAY (ABSOLUTE POSITIONING FIX) ---
def create_emoji_overlay(script_text, video_duration, target_size):
    """Checks script for keywords and returns a popping ImageClip."""
    text_lower = script_text.lower()
    assets_dir = "assets/emojis"
    
    # 1. Find Keyword
    found_file = None
    for keyword, filename in EMOJI_MAP.items():
        if f" {keyword} " in f" {text_lower} " or (keyword in text_lower and len(keyword) > 4):
            path = os.path.join(assets_dir, filename)
            if os.path.exists(path):
                found_file = path
                break
    
    if not found_file: return None

    # 2. Create Clip
    try:
        img = ImageClip(found_file)
        target_w, target_h = target_size
        is_shorts = target_w < target_h 
        
        # --- POSITIONING & SIZE LOGIC ---
        if is_shorts:
            # SHORTS: Center Horizontal, Just above Center Vertical
            # Size: 18% of screen width
            new_w = target_w * 0.18
            img = img.resize(width=new_w) # Resize first to get correct height
            
            # MATH:
            # Center of screen = target_h / 2
            # Move up by emoji height = - img.h
            # Move up by padding (50px) = - 50
            final_y = (target_h / 2) - img.h - 50 
            
            pos = ('center', int(final_y))
            
        else:
            # LONG FORM: Right-Center
            # Size: 12% of screen width
            new_w = target_w * 0.12
            img = img.resize(width=new_w)
            
            # Right side (75% across)
            final_x = target_w * 0.75
            
            pos = (int(final_x), 'center')

        # Duration & Animation
        pop_duration = min(1.0, video_duration)
        img = img.set_pos(pos).set_duration(pop_duration).set_start(0)
        img = img.crossfadein(0.05) 
        
        return img
    except Exception as e:
        print(f"   [Overlay Error] Could not load emoji: {e}")
        return None

# --- 2. BACKUP ENGINE (Calculation Based) ---
def create_estimated_captions(script_text, total_duration):
    mode = config.VIDEO_MODE if hasattr(config, 'VIDEO_MODE') else "Shorts"
    font_size = config.VIDEO_SETTINGS[mode]["font_size"]
    
    if mode == "Shorts":
        text_pos = 'center'
    else:
        text_pos = ('center', 0.8)

    words = script_text.split()
    chunks = []
    current_chunk = []
    
    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= 2 or len(word) > 7:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
    if current_chunk: chunks.append(" ".join(current_chunk))
        
    clips = []
    current_time = 0
    total_chars = len(script_text)
    
    for chunk in chunks:
        chunk_weight = len(chunk) / total_chars if total_chars > 0 else 0
        chunk_duration = total_duration * chunk_weight
        if chunk_duration < 0.3: chunk_duration = 0.3
        
        full_text = chunk.upper()
        
        # --- FIXED: NOW USES COLOR LOGIC ---
        text_color, stroke_color, scale_factor = get_text_style(full_text)
        
        try:
            txt = TextClip(
                full_text, 
                fontsize=font_size, 
                color=text_color, # NO LONGER HARDCODED YELLOW
                font='Arial', 
                stroke_color=stroke_color, 
                stroke_width=3, 
                method='label'
            )
            
            # Apply Pop Effect (Resize)
            if scale_factor > 1.0:
                txt = txt.resize(scale_factor)
            
            if mode == "Shorts":
                txt = txt.set_pos('center')
            else:
                txt = txt.margin(bottom=50, opacity=0).set_pos(('center', 'bottom'))

            txt = txt.set_start(current_time).set_duration(chunk_duration)
            clips.append(txt)
        except Exception as e:
            print(f"   [Text Error] Backup Engine failed: {e}")
            
        current_time += chunk_duration
    return clips

# --- HELPER: GET SMART SFX (FIXED: CHECKS BOTH FOLDERS) ---
def get_smart_sfx_path(script_text):
    """Scans script for keywords and returns a specific SFX path if found."""
    text_lower = script_text.lower()
    
    # Define possible locations
    possible_folders = ["assets/sfx", "assets"]
    
    # Check for keywords
    for keyword, filename in SMART_SFX_MAP.items():
        if keyword in text_lower:
            # Check both folders for the file
            for folder in possible_folders:
                specific_path = os.path.join(folder, filename)
                if os.path.exists(specific_path):
                    print(f"   [SFX] Found sound effect: {filename} for '{keyword}'")
                    return specific_path
    
    # Fallback 1: Randomized Transitions
    transition_folder = "assets/transitions"
    if os.path.exists(transition_folder):
        options = [os.path.join(transition_folder, f) for f in os.listdir(transition_folder) if f.endswith(".mp3")]
        if options: return random.choice(options)
        
    # Fallback 2: Default Transition
    for folder in possible_folders:
        default_path = os.path.join(folder, "transition.mp3")
        if os.path.exists(default_path): return default_path
    
    return None

def safe_load_audio(path, volume=1.0):
    """
    Super-Safe Mode: Converts to WAV and streams from disk.
    Bypasses NumPy entirely to avoid 'stack' errors.
    """
    if not os.path.exists(path): return None
    
    # 1. Create a temp file name
    # We use a unique ID so files don't clash
    temp_wav = path.replace(".mp3", "") + f"_{random.randint(1000, 9999)}_fixed.wav"
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    try:
        # 2. FFmpeg Conversion (Force Stereo, 44.1kHz)
        # This fixes the "buffer crash" and "mono" issues at the source
        cmd = [ffmpeg_exe, "-y", "-i", path, "-vn", "-acodec", "pcm_s16le", "-ac", "2", "-ar", "44100", temp_wav]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 3. Load the WAV directly
        if os.path.exists(temp_wav):
            # We return a direct file clip. 
            # Note: We rely on studio.py to clean up these .wav files later.
            return AudioFileClip(temp_wav).fx(volumex, volume)
            
    except Exception as e:
        print(f"   [Audio Error] Could not load {os.path.basename(path)}: {e}")
        return None
    
    return None

# --- 2. PROCESS SCENE (The Final Correct Version) ---
def process_single_scene(video_path, audio_path, script_text, is_first_scene=False, timing_path=None):
    """
    Combines Video + Audio + Subtitles + Emojis + Transitions.
    FIXED: 
    1. TRUE CROP MATH: Removes x_center rounding bug (Fixes 1079x1920 crash).
    2. SMART VOLUMES: Ding is softer (0.6), Horror is loud (1.2).
    3. RAM AUDIO: Loads SFX into memory to prevent crashes.
    """
    try:
        # --- HELPER: SAFE RAM LOADER ---
        def load_sfx_safe(filename, start_t, max_t, volume_level=1.0):
            if not os.path.exists(filename): return None
            if start_t >= max_t: return None
            try:
                src = AudioFileClip(filename)
                dur = src.duration
                if (start_t + dur) > max_t: dur = max_t - start_t
                if dur < 0.05: 
                    src.close()
                    return None
                audio_data = src.subclip(0, dur).to_soundarray(fps=44100)
                src.close()
                from moviepy.audio.AudioClip import AudioArrayClip
                return AudioArrayClip(audio_data, fps=44100).set_start(start_t).fx(volumex, volume_level)
            except: return None

        # 1. SETUP TARGET RESOLUTION
        try:
            import config
            mode = getattr(config, 'VIDEO_MODE', 'Shorts')
        except: mode = 'Shorts'

        if mode == "Shorts":
            target_w, target_h = 1080, 1920
        else:
            target_w, target_h = 1920, 1080

        # 2. LOAD VIDEO & RESIZE (THE TRUE FIX)
        video = VideoFileClip(video_path)
        
        ratio_clip = video.w / video.h
        ratio_target = target_w / target_h
        
        if ratio_clip > ratio_target:
            # Video is wider -> Match height
            new_h = target_h
            new_w = int(new_h * ratio_clip)
        else:
            # Video is taller -> Match width
            new_w = target_w
            new_h = int(new_w / ratio_clip)
            
        # Safety clamp
        new_w = max(new_w, target_w)
        new_h = max(new_h, target_h)
            
        video = video.resize(width=new_w, height=new_h)
        
        # --- INTEGER CROP LOGIC (Fixes 1079 Bug) ---
        # We calculate exact pixels instead of letting MoviePy round decimals
        x1 = int((video.w - target_w) / 2)
        y1 = int((video.h - target_h) / 2)
        x2 = x1 + target_w
        y2 = y1 + target_h
        
        video = video.crop(x1=x1, y1=y1, x2=x2, y2=y2)

        # 3. MASTER AUDIO SYNC
        audio = AudioFileClip(audio_path)
        master_duration = audio.duration
        
        if master_duration > video.duration:
            import moviepy.video.fx.all as vfx
            video = vfx.loop(video, duration=master_duration)
        else:
            if abs(video.duration - master_duration) > 0.1:
                video = video.subclip(0, master_duration)
        
        video = video.set_duration(master_duration)
        video = video.set_audio(audio)
        
        # 4. PREPARE LAYERS
        sfx_audio_layers = [audio]   
        extra_layers = [] 
        
        # Transition Logic
        if not is_first_scene:
            trans_path = "assets/whoosh_fast.mp3"
            if not os.path.exists(trans_path): trans_path = "assets/transition.mp3"
            
            # Transition Volume: 0.3
            t_clip = load_sfx_safe(trans_path, 0, master_duration, volume_level=0.3)
            if t_clip: sfx_audio_layers.append(t_clip)

        # 5. SFX MAPPING
        SMART_SFX_MAP = {
            "money": "cash.mp3", "rich": "cash.mp3", "profit": "cash.mp3",
            "scary": "horror_hit.mp3", "dark": "horror_hit.mp3", "mystery": "mystery_swoosh.mp3",
            "idea": "ding.mp3", "solution": "ding.mp3",
            "fast": "whoosh_fast.mp3", "speed": "whoosh_fast.mp3",
            "computer": "type.mp3", "hack": "glitch.mp3", "error": "glitch.mp3",
            "clock": "clock.mp3", "crowd": "crowd.mp3",
            "galaxy": "galaxy.mp3", "space": "galaxy.mp3", "outerspace": "outer_space.mp3",
            "network": "network.mp3", "warning": "warning.mp3", "alert": "warning.mp3",
            "rain": "rain.mp3", "thunder": "thunder.mp3", "fire": "fire.mp3",
            "success": "success.mp3", "failure": "failure.mp3", "door": "door.mp3"
        }

        if 'EMOJI_MAP' not in globals():
             EMOJI_MAP = { "money": "money.png", "fire": "fire.png" } 
        else:
             EMOJI_MAP = globals()['EMOJI_MAP']

        # 6. SCAN SCRIPT
        import re
        clean_text = re.sub(r'[^\w\s]', '', script_text).lower()
        words = clean_text.split()
        
        if len(words) > 0: step_time = master_duration / len(words)
        else: step_time = 0.5
        current_time = 0
        last_sfx_time = -5 

        for word in words:
            # A. KEYWORD SFX (Smart Volumes)
            if word in SMART_SFX_MAP:
                if (current_time - last_sfx_time) > 2.0:
                    sound_filename = SMART_SFX_MAP[word]
                    sfx_path = f"assets/{sound_filename}"
                    
                    # --- SMART VOLUME LOGIC ---
                    vol = 1.0 
                    if "ding.mp3" in sound_filename: vol = 0.6    # Softer Ding
                    elif "horror_hit.mp3" in sound_filename: vol = 1.2 # Strong Horror
                    elif "cash.mp3" in sound_filename: vol = 0.8  # Balanced Cash
                    
                    s_clip = load_sfx_safe(sfx_path, current_time, master_duration, volume_level=vol)
                    if s_clip:
                        sfx_audio_layers.append(s_clip)
                        last_sfx_time = current_time
            
            # B. EMOJIS + POP
            if word in EMOJI_MAP:
                 emoji_clip = create_emoji_overlay(word, master_duration, (target_w, target_h))
                 if emoji_clip:
                     extra_layers.append(emoji_clip.set_start(current_time))
                     
                     pop_paths = ["assets/pop.mp3", "assets/Pop.mp3", "assets/sfx/pop.mp3"]
                     pop_file = next((p for p in pop_paths if os.path.exists(p)), None)
                     
                     if pop_file:
                         # Pop Volume: 1.0 (Standard)
                         p_clip = load_sfx_safe(pop_file, current_time, master_duration, volume_level=1.0)
                         if p_clip: sfx_audio_layers.append(p_clip)

            current_time += step_time

        # 7. COMPOSITE VISUALS (LOCKED SIZE)
        subs = []
        try:
            if timing_path and os.path.exists(timing_path):
                subs = create_perfect_captions(timing_path)
            if not subs:
                subs = create_estimated_captions(script_text, master_duration)
        except: subs = []

        # Lock the size here to guarantee 1080x1920
        final_video = CompositeVideoClip([video] + extra_layers + subs, size=(target_w, target_h))

        # 8. MERGE AUDIO
        if len(sfx_audio_layers) > 1:
            valid_layers = [c for c in sfx_audio_layers if c.start < master_duration]
            final_audio = CompositeAudioClip(valid_layers)
            final_audio = final_audio.set_duration(master_duration)
            final_video = final_video.set_audio(final_audio)
        
        # 9. FINAL DURATION CLAMP
        final_video = final_video.set_duration(master_duration)
        
        return final_video

    except Exception as e:
        print(f"      [Error] Scene processing failed: {e}")
        import traceback
        traceback.print_exc()
        return None
# --- SMART PLAYLIST GENERATOR ---
def create_background_music(mood_name, keywords, total_duration):
    base_folder = "songs"
    specific_folder = os.path.join(base_folder, mood_name)
    master_library = os.path.join(base_folder, "Master_Library")
    
    available_songs = []
    
    if os.path.exists(specific_folder):
        available_songs += [os.path.join(specific_folder, f) for f in os.listdir(specific_folder) if f.endswith(".mp3")]
        
    if os.path.exists(master_library):
        for f in os.listdir(master_library):
            if f.endswith(".mp3"):
                if any(k in f.lower() for k in keywords):
                    available_songs.append(os.path.join(master_library, f))
    
    available_songs = list(set(available_songs))
    
    if not available_songs: 
        print(f"   [Music] No songs found for mood '{mood_name}'.")
        return None
    
    mode = config.VIDEO_MODE if hasattr(config, 'VIDEO_MODE') else "Shorts"

    try:
        if mode == "Shorts" or len(available_songs) < 2:
            song_path = random.choice(available_songs)
            bg_music = AudioFileClip(song_path)
            bg_music = audio_loop(bg_music, duration=total_duration)
            bg_music = bg_music.fx(volumex, 0.50).fx(audio_fadeout, 2)
            print(f"   [Music] Looping track: {os.path.basename(song_path)}")
            return bg_music
        else:
            print(f"   [Music] DJ Playlist ({len(available_songs)} tracks available)...")
            playlist = []
            current_duration = 0
            random.shuffle(available_songs)
            
            song_index = 0
            while current_duration < total_duration:
                if song_index >= len(available_songs): 
                    song_index = 0
                    random.shuffle(available_songs)
                
                track_path = available_songs[song_index]
                track = AudioFileClip(track_path)
                track = track.fx(audio_fadein, 2).fx(audio_fadeout, 2)
                
                playlist.append(track)
                current_duration += track.duration - 2 
                song_index += 1
            
            full_music = concatenate_audioclips(playlist)
            full_music = full_music.subclip(0, total_duration)
            full_music = full_music.fx(volumex, 0.2).fx(audio_fadeout, 3)
            return full_music

    except Exception as e:
        print(f"   [Error] Music generation failed: {e}")
        return None

def combine_scenes(timeline, video_files, audio_files, session_id, music_data):
    mood_name, keywords = music_data
    print("3.5 Rendering Scenes Individually (Direct FFmpeg Mode)...")
    
    temp_dir = "temp/scenes"
    if not os.path.exists(temp_dir): os.makedirs(temp_dir)
    
    scene_files = [] 

    # 1. RENDER EACH SCENE
    try:
        total_scenes = len(timeline)
        for i in range(total_scenes):
            if i < len(audio_files): 
                print(f"   [Editor] Rendering Scene {i+1}/{total_scenes}...")
                
                current_video = video_files[i] if i < len(video_files) else video_files[-1]
                
                # --- PASS THE TIMING FILE HERE ---
                timing_file = f"temp/timing_{i}_{session_id}.json"
                
                clip = process_single_scene(
                    current_video, 
                    audio_files[i], 
                    timeline[i]['text'], 
                    is_first_scene=(i==0),
                    timing_path=timing_file  # <--- CRITICAL FIX
                )
                
                if clip:
                    scene_filename = os.path.join(temp_dir, f"scene_{session_id}_{i:03d}.mp4")
                    
                    # Force Standards to prevent stitching glitches
                    clip.write_videofile(
                        scene_filename, 
                        fps=24, 
                        codec='libx264', 
                        audio_codec='aac', 
                        ffmpeg_params=['-ac', '2', '-pix_fmt', 'yuv420p'],
                        preset='ultrafast', 
                        threads=4, 
                        verbose=False, 
                        logger=None
                    )
                    scene_files.append(scene_filename)
                    clip.close()
                    del clip
                    gc.collect()
    except Exception as e:
        print(f"   [Error] Scene rendering loop failed: {e}")

    # 2. OUTRO & 3. STITCHING (Standard Code Continues...)
    # (Just copy the rest of your combine_scenes logic here or leave it if you only pasted the block above)
    # ... [Rest of combine_scenes logic logic is fine, just ensure indentation matches]
    
    # 2. RENDER OUTRO (Universal)
    outro_path = "assets/outro.mp4"
    if os.path.exists(outro_path) and len(scene_files) > 0:
        try:
            is_long_form = hasattr(config, 'VIDEO_MODE') and config.VIDEO_MODE == "Long"
            target_w, target_h = (1920, 1080) if is_long_form else (1080, 1920)

            out_clip = VideoFileClip(outro_path)
            ratio_clip = out_clip.w / out_clip.h
            ratio_target = target_w / target_h
            if ratio_clip > ratio_target:
                new_h = target_h
                new_w = int(new_h * ratio_clip)
                out_clip = out_clip.resize(height=new_h).crop(x1=new_w/2 - target_w/2, width=target_w, height=target_h)
            else:
                new_w = target_w
                new_h = int(new_w / ratio_clip)
                out_clip = out_clip.resize(width=new_w).crop(y1=new_h/2 - target_h/2, width=target_w, height=target_h)
            
            if out_clip.audio is None:
                from moviepy.audio.AudioClip import AudioClip
                out_clip = out_clip.set_audio(AudioClip(lambda t: [0], duration=out_clip.duration, fps=44100))
            
            outro_filename = os.path.join(temp_dir, f"chunk_{session_id}_z_outro.mp4")
            out_clip.write_videofile(outro_filename, fps=24, codec='libx264', audio_codec='aac', ffmpeg_params=['-ac', '2', '-pix_fmt', 'yuv420p'], preset='ultrafast', threads=4, logger=None)
            scene_files.append(outro_filename)
            out_clip.close()
        except: pass

    # 3. STITCHING PHASE
    if not scene_files: return None
    
    list_file = f"temp/stitch_list_{session_id}.txt"
    with open(list_file, 'w', encoding='utf-8') as f:
        for vid in scene_files:
            abs_path = os.path.abspath(vid).replace('\\', '/')
            f.write(f"file '{abs_path}'\n")

    stitched_filename = f"temp/stitched_{session_id}.mp4" 
    
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        import subprocess
        cmd = [ffmpeg_exe, "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", stitched_filename]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"   [Stitch Error] {e}")
        return None

    # 4. FINAL LAYERS
    try:
        final_video_clip = VideoFileClip(stitched_filename)
        from moviepy.audio.fx.all import volumex
        bg_music = create_background_music(mood_name, keywords, final_video_clip.duration)
        final_audio_list = []
        if final_video_clip.audio: final_audio_list.append(final_video_clip.audio)
        if bg_music: final_audio_list.append(bg_music.fx(volumex, 0.30)) 

        # TING SFX
        ting_path = "assets/windchimes.mp3"
        if os.path.exists(ting_path):
            try:
                final_audio_list.append(AudioFileClip(ting_path).set_start(0.5).fx(volumex, 0.6))
            except: pass
        
        if final_audio_list:
            final_video_clip = final_video_clip.set_audio(CompositeAudioClip(final_audio_list))

        final_output_filename = f"finished_{session_id}.mp4"
        if "HINDI" in session_id: final_output_filename = f"finished_{session_id}_HINDI.mp4"
        
        final_video_clip.write_videofile(final_output_filename, codec='libx264', audio_codec='aac', fps=24, preset='ultrafast', threads=4, logger=None)
        final_video_clip.close()
        return final_output_filename

    except Exception as e:
        print(f"   [Error] Final processing failed: {e}")
        return stitched_filename
    
        # --- THUMBNAIL ENGINE (NEW) ---
def create_thumbnail(topic, session_id, background_image=None):
    """
    Generates a thumbnail.
    STRATEGY: Pollinations AI -> Pexels Stock Photo -> Dark Background.
    FIXED: 
    1. Removes '(Hindi)' from text. 
    2. Auto-wraps long text efficiently.
    3. Uses 'Impact' font for viral look.
    """
    import re
    
    # 1. CLEAN TOPIC FOR DISPLAY (Removes (Hindi), emojis, etc.)
    # This ensures the text on screen is clean
    display_topic = re.sub(r'\s*\(.*?\)', '', topic) # Removes (...) content
    display_topic = display_topic.replace("Hindi", "").replace("Hinglish", "").strip()
    display_topic = re.sub(r'[^a-zA-Z0-9\s\?]', '', display_topic) # Keep '?'
    
    print(f"   [Thumbnail] Generating smart thumbnail for: '{display_topic}'")
    
    # 2. DETECT MODE & SET DIMENSIONS
    try:
        import config
        is_long_mode = getattr(config, 'VIDEO_MODE', 'Shorts') == "Long"
    except:
        is_long_mode = False 

    if is_long_mode:
        w, h = 1280, 720
        ai_shape = "cinematic landscape" 
        orientation_prompt = "cinematic"
        pexels_orientation = "landscape"
        base_font_size = 90
    else:
        w, h = 720, 1280
        ai_shape = "Portrait"  
        orientation_prompt = "vertical"
        pexels_orientation = "portrait"
        base_font_size = 100
    
    output_path = f"temp/thumbnail_{session_id}.png"
    
    # Search query for images (keep it simple)
    short_query = " ".join(display_topic.split()[:4]) 

    try:
        # 3. AUTO-GENERATE BACKGROUND (If missing)
        if not background_image or not os.path.exists(background_image):
            
            # --- TIER 1: POLLINATIONS AI ---
            print(f"   [Thumbnail] Attempt 1: Generating AI Art ({w}x{h})...")
            try:
                import urllib.parse
                import random
                import requests
                
                prompt = f"mysterious {orientation_prompt} poster of {short_query}, dramatic lighting, hyperrealistic, 8k"
                encoded_prompt = urllib.parse.quote(prompt)
                
                url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={w}&height={h}&nologo=true&seed={random.randint(1,999)}"
                
                response = requests.get(url, timeout=45)
                if response.status_code == 200:
                    ai_temp_file = f"temp/thumb_art_{session_id}.png"
                    with open(ai_temp_file, 'wb') as f: f.write(response.content)
                    background_image = ai_temp_file
                    print("      [Success] AI Art Generated.")
                else:
                    print(f"      [Fail] Pollinations 502/Timeout. Switching to Stock.")
            except Exception as e:
                print(f"      [Fail] AI Error: {e}")

            # --- TIER 2: PEXELS STOCK PHOTO ---
            if not background_image or not os.path.exists(background_image):
                print(f"   [Thumbnail] Attempt 2: Searching Pexels Stock for '{short_query}'...")
                try:
                    import requests
                    headers = {'Authorization': config.PEXELS_API_KEY}
                    search_url = f"https://api.pexels.com/v1/search?query={short_query}&per_page=1&orientation={pexels_orientation}"
                    r = requests.get(search_url, headers=headers, timeout=10).json()
                    
                    if r.get('photos'):
                        img_url = r['photos'][0]['src']['large']
                        stock_temp_file = f"temp/thumb_stock_{session_id}.jpg"
                        with requests.get(img_url, stream=True) as req, open(stock_temp_file, 'wb') as f:
                            for chunk in req.iter_content(8192): f.write(chunk)
                        background_image = stock_temp_file
                        print("      [Success] Pexels Stock Photo found.")
                    else:
                        print("      [Fail] No stock photos found.")
                except Exception as e:
                    print(f"      [Fail] Pexels Error: {e}")

        # 4. SETUP BACKGROUND CLIP (SMART FILL LOGIC)
        if background_image and os.path.exists(background_image):
            bg_clip = ImageClip(background_image)
            
            img_ratio = bg_clip.w / bg_clip.h
            target_ratio = w / h
            
            if img_ratio > target_ratio:
                # Image is WIDER -> Match Height, Crop Sides
                new_h = h
                new_w = int(new_h * img_ratio)
                bg_clip = bg_clip.resize(height=new_h)
                bg_clip = bg_clip.crop(x_center=bg_clip.w/2, width=w)
            else:
                # Image is TALLER -> Match Width, Crop Top/Bottom
                new_w = w
                new_h = int(new_w / img_ratio)
                bg_clip = bg_clip.resize(width=new_w)
                bg_clip = bg_clip.crop(y_center=bg_clip.h/2, height=h)
            
            bg_clip = bg_clip.resize(width=w, height=h)
            bg = bg_clip.set_duration(1)
        else:
            print("   [Thumbnail] Attempt 3: Using Dark Background.")
            bg = ColorClip(size=(w, h), color=(15, 15, 20), duration=1)

        # 5. CREATIVE TEXT OVERLAY (THE FIX)
        # Use 'caption' method which automatically wraps text inside a box
        
        # Determine Font (Try Impact for memes/viral, else Arial)
        font_name = 'Impact' if 'Impact' in TextClip.list('font') else 'Arial-Bold'
        
        # Scale down font if text is very long
        if len(display_topic) > 20: 
            base_font_size = int(base_font_size * 0.8)
        
        txt_clip = TextClip(
            display_topic.upper(),
            fontsize=base_font_size, 
            color='white',           # White is cleaner than yellow
            font=font_name,
            stroke_color='black',
            stroke_width=6,          # Thick outline for readability
            align='center',
            method='caption',        # Auto-wrapping magic
            size=(int(w * 0.85), None) # Restrict width to 85% of screen
        ).set_position(('center', 'center'))

        # 6. RENDER
        thumb = CompositeVideoClip([bg, txt_clip]).set_duration(1)
        thumb.save_frame(output_path, t=0.5)
        
        thumb.close()
        try: bg.close()
        except: pass
        
        print(f"   [Thumbnail] Saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"   [Thumbnail Critical Error] {e}")
        return None