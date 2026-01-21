# media_engine.py
import os
import random
import warnings
import math
import json
import glob
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips, TextClip, CompositeVideoClip, ImageClip, concatenate_audioclips
from moviepy.audio.fx.all import audio_loop, volumex, audio_fadeout, audio_fadein
from moviepy.video.fx.all import fadein, fadeout
import effects 
import config 
import generators # Importing for smart_input

# Suppress Warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- CONFIG: SMART SFX LIBRARY ---
SMART_SFX_MAP = {
    "money": "cash.mp3",
    "rich": "cash.mp3",
    "profit": "cash.mp3",
    "scary": "horror_hit.mp3",
    "dark": "horror_hit.mp3",
    "mystery": "mystery_swoosh.mp3",
    "idea": "ding.mp3",
    "solution": "ding.mp3",
    "fast": "whoosh_fast.mp3",
    "speed": "whoosh_fast.mp3",
    "computer": "type.mp3",
    "hack": "glitch.mp3",
    "error": "glitch.mp3"
}

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

# --- 1. PERFECT ENGINE (Metadata Based) ---
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
        
        if (current_duration > 0.4 and len(chunk_text) >= 1) or len(chunk_text) >= 3 or i == len(words)-1:
            full_text = " ".join(chunk_text).upper().strip()
            try:
                text_color = '#FF4500' if any(x in full_text for x in ['NOT', 'NEVER', 'STOP', 'HUGE']) else '#FFD700'
                
                txt = TextClip(
                    full_text, 
                    fontsize=font_size, 
                    color=text_color, 
                    font='Arial', 
                    stroke_color='black', 
                    stroke_width=3, 
                    method='label'
                )
                
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
        
        try:
            txt = TextClip(
                chunk.upper(), 
                fontsize=font_size, 
                color='#FFD700', 
                font='Arial', 
                stroke_color='black', 
                stroke_width=3, 
                method='label'
            )
            
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

# --- HELPER: GET SMART SFX ---
def get_smart_sfx_path(script_text):
    """Scans script for keywords and returns a specific SFX path if found."""
    text_lower = script_text.lower()
    sfx_folder = "assets/sfx"
    
    # Check for keywords
    for keyword, filename in SMART_SFX_MAP.items():
        if keyword in text_lower:
            specific_path = os.path.join(sfx_folder, filename)
            if os.path.exists(specific_path):
                return specific_path
    
    # Fallback 1: Randomized Transitions
    transition_folder = "assets/transitions"
    if os.path.exists(transition_folder):
        options = [os.path.join(transition_folder, f) for f in os.listdir(transition_folder) if f.endswith(".mp3")]
        if options: return random.choice(options)
        
    # Fallback 2: Default Transition
    default_path = "assets/transition.mp3"
    if os.path.exists(default_path): return default_path
    
    return None

# --- SCENE PROCESSING (OPTIMIZED: SCALE-TO-FILL + SMART SFX) ---
def process_single_scene(video_path, audio_path, script_text, is_first_scene=False):
    mode = config.VIDEO_MODE if hasattr(config, 'VIDEO_MODE') else "Shorts"
    settings = config.VIDEO_SETTINGS[mode]
    target_w, target_h = settings["resolution"]
    
    try:
        # 1. Audio
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        
        # 2. Add Smart SFX
        if not is_first_scene:
            sfx_path = get_smart_sfx_path(script_text)
            
            if sfx_path and os.path.exists(sfx_path):
                try:
                    trans_snd = AudioFileClip(sfx_path).fx(volumex, 0.5)
                    audio_clip = CompositeAudioClip([audio_clip, trans_snd.set_start(0)])
                except: pass
        
        # 3. Video Processing
        if video_path.endswith(".jpg"):
            # --- IMAGES ---
            clip = ImageClip(video_path)
            
            ratio_w = target_w / clip.w
            ratio_h = target_h / clip.h
            scale_factor = max(ratio_w, ratio_h)
            
            clip = clip.resize(scale_factor)
            clip = clip.crop(x_center=clip.w / 2, y_center=clip.h / 2, width=target_w, height=target_h)
            clip = clip.set_duration(duration)
            
        else:
            # --- VIDEOS ---
            clip = VideoFileClip(video_path)
            if clip.duration < duration: clip = clip.loop(duration=duration)
            else: clip = clip.subclip(0, duration)
            
            ratio_w = target_w / clip.w
            ratio_h = target_h / clip.h
            scale_factor = max(ratio_w, ratio_h)
            
            # Smart Resize
            if abs(scale_factor - 1.0) > 0.001:
                clip = clip.resize(scale_factor)
                
            clip = clip.crop(x_center=clip.w / 2, y_center=clip.h / 2, width=target_w, height=target_h)

        # --- 4. CINEMATIC FADE (Long Form Only) ---
        if mode == "Long":
            clip = clip.fx(fadein, 0.5)

        clip = clip.set_audio(audio_clip)
        
        # TIMING PATH ADJUSTMENT:
        # Since audio is in temp/, timing is also in temp/.
        # .replace("audio_", "timing_") works correctly on "temp/audio_0.mp3" -> "temp/timing_0.json"
        timing_path = audio_path.replace("audio_", "timing_").replace(".mp3", ".json")
        caption_clips = create_perfect_captions(timing_path)
        
        if not caption_clips:
            caption_clips = create_estimated_captions(script_text, duration)
        
        final_scene = CompositeVideoClip([clip, *caption_clips]).set_duration(duration)
        return final_scene

    except Exception as e:
        print(f"   [Error] Scene processing failed: {e}")
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
            bg_music = bg_music.fx(volumex, 0.1).fx(audio_fadeout, 2)
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
            full_music = full_music.fx(volumex, 0.1).fx(audio_fadeout, 3)
            return full_music

    except Exception as e:
        print(f"   [Error] Music generation failed: {e}")
        return None

def combine_scenes(timeline, video_files, audio_files, session_id, music_data):
    mood_name, keywords = music_data
    
    print("3.5 Stitching Scenes & Mixing Audio...")
    scene_clips = []
    final_comp = None
    cta_clip = None
    bell_audio = None
    
    outro_path = "assets/outro.mp4" 
    has_fixed_outro = os.path.exists(outro_path)
    
    try:
        for i in range(len(timeline)):
            if i < len(audio_files): 
                print(f"   [Editor] Rendering Scene {i+1}...")
                current_video = video_files[i] if i < len(video_files) else video_files[-1]
                is_last_scene = (i == len(timeline) - 1)
                
                if is_last_scene and has_fixed_outro and config.VIDEO_MODE == "Shorts":
                    print("   [Editor] Using Fixed Outro Clip (Shorts).")
                    current_video = outro_path

                clip = process_single_scene(current_video, audio_files[i], timeline[i]['text'], is_first_scene=(i==0))
                if clip: scene_clips.append(clip)
        
        if not scene_clips: return None

        final_video = concatenate_videoclips(scene_clips, method="compose")
        total_duration = final_video.duration
        
        final_layers = [final_video]
        
        watermark = effects.create_watermark(total_duration)
        if watermark: final_layers.append(watermark)

        cta_clip, bell_audio = effects.create_subscribe_overlay(total_duration)
        if cta_clip: 
            final_layers.append(cta_clip)
            if bell_audio: print("   [SFX] Adding Bell Sound...")

        final_comp = CompositeVideoClip(final_layers)

        full_audio = final_comp.audio 
        bg_music = create_background_music(mood_name, keywords, total_duration)
        
        audio_list = [full_audio]
        if bg_music: audio_list.append(bg_music)
        if bell_audio: audio_list.append(bell_audio)
        
        final_comp = final_comp.set_audio(CompositeAudioClip(audio_list))

        output_filename = f"final_{session_id}.mp4"
        
        # --- TURBO CHARGE (DYNAMIC THREADS) ---
        max_threads = os.cpu_count()
        if not max_threads: max_threads = 4
        
        print(f"   STARTING RENDER (Turbo Mode - {max_threads} Threads)...")
        # Optimization: Changed FPS from 30 to 24 (Cinematic Standard)
        final_comp.write_videofile(output_filename, codec='libx264', audio_codec='aac', fps=24, preset='ultrafast', logger='bar', threads=max_threads)
        
        return output_filename

    except Exception as e:
        print(f"   [Error] Editing failed: {e}")
        return None

    finally:
        print("   [Editor] Releasing file locks...")
        try:
            for c in scene_clips: c.close()
        except: pass
        try:
            if cta_clip: cta_clip.close()
        except: pass
        try:
            if bell_audio: bell_audio.close()
        except: pass
        try:
            if final_comp: final_comp.close()
        except: pass