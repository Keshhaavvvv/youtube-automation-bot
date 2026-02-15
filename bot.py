# bot.py (The Manager)
import sys
import random
import asyncio
import socket
import os
import warnings
import traceback
import glob
import re
import json 
import shutil

# --- IMPORT TEAMS ---
import generators    # The Writer
import media_engine  # The Editor
import studio        # The Manager
import config        # Config
import translator    # The Language Brain

# --- SYSTEM CONFIG ---
socket.setdefaulttimeout(30)
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '2'
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding='utf-8')

def select_video_mode():
    """Asks the user to select the video format or resume."""
    print(f"---------------------------------------------------")
    print(f" SELECT VIDEO MODE")
    print(f"---------------------------------------------------")
    print(" 1. Shorts (Vertical 9:16, ~60 sec)")
    print(" 2. Long Form (Horizontal 16:9, ~10 mins)")
    print(" 3. 🚑 RESUME CRASHED SESSION")
    
    choice = generators.smart_input(" > Enter choice (1-2): ", timeout=60, default_value="2").strip()
    
    if choice == "3":
        return "RESUME"
    if choice == "2":
        config.VIDEO_MODE = "Long"
        print(f"   [System] Mode set to: LONG FORM (Horizontal)")
        return "NEW"
    else:
        config.VIDEO_MODE = "Shorts"
        print(f"   [System] Mode set to: SHORTS (Vertical)")
        return "NEW"

def select_language_mode():
    """Asks which channels to target (English, Hindi, or Both)."""
    print(f"---------------------------------------------------")
    print(f" SELECT TARGET AUDIENCE")
    print(f"---------------------------------------------------")
    print(" 1. 🇺🇸 English Channel Only")
    print(" 2. 🇮🇳 Hindi Channel Only")
    print(" 3. 🌍 BOTH (Dual-Channel Automation)")
    
    choice = generators.smart_input(" > Enter choice (1-3) [Auto: 3]: ", timeout=60, default_value="3").strip()
    
    if choice == "1": 
        print("   [System] Target set to: ENGLISH ONLY")
        return "ENGLISH_ONLY"
    if choice == "2": 
        print("   [System] Target set to: HINDI ONLY")
        return "HINDI_ONLY"
    
    print("   [System] Target set to: BOTH (Dual-Channel)")
    return "BOTH"

def resume_workflow():
    """
    Advanced Rescue Logic: 
    1. Checks for finished video.
    2. Checks for rendered scenes (FFmpeg) to fast-stitch.
    3. Reconstructs timeline data for Hindi translation.
    """
    print(f"\n---------------------------------------------------")
    print(f" 🚑 SESSION RESCUE MODE")
    print(f"---------------------------------------------------")
    
    session_id = input(" > Enter the Session ID to resume (e.g., 9593): ").strip()
    if not session_id: return None, None, None, None, None

    # --- DATA RECONSTRUCTION (Needed for Hindi) ---
    print(f"   [Resume] Rebuilding timeline data for Session {session_id}...")
    recovered_timeline = []
    recovered_video_files = []
    recovered_audio_files = []
    
    i = 0
    while True:
        # Check for asset files to rebuild the list
        a_path = os.path.join("temp", f"audio_{i}_{session_id}.mp3")
        # Visuals might be video or image
        v_path = os.path.join("temp", f"clip_{i}_{session_id}.mp4")
        if not os.path.exists(v_path):
            v_path = os.path.join("temp", f"clip_{i}_{session_id}.png")
        if not os.path.exists(v_path):
            v_path = os.path.join("temp", f"clip_{i}_{session_id}.jpg")
            
        t_path = os.path.join("temp", f"timing_{i}_{session_id}.json")
        
        # If we have at least audio and visual, we can recover this scene's existence
        if os.path.exists(a_path) and os.path.exists(v_path):
            # Try to recover text
            text_content = "Scene audio."
            if os.path.exists(t_path):
                try:
                    with open(t_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        text_content = " ".join([d['word'] for d in data])
                except: pass
            
            recovered_timeline.append({'text': text_content, 'visual': 'recovered'})
            recovered_audio_files.append(a_path)
            recovered_video_files.append(v_path)
            i += 1
        else:
            break
            
    if not recovered_timeline:
        print("   [Error] No raw assets found. Cannot proceed with Hindi later.")
        return None, None, None, None, None

    print(f"   [Resume] Data recovered: {len(recovered_timeline)} scenes.")

    # --- CHECK 1: IS ENGLISH VIDEO ALREADY DONE? ---
    finished_path = f"finished_{session_id}.mp4"
    if os.path.exists(finished_path):
        print(f"   [Resume] Found finished video: {finished_path}")
        return finished_path, session_id, recovered_timeline, recovered_video_files, recovered_audio_files

    # --- CHECK 2: ARE SCENES RENDERED? (FFMPEG STITCHING) ---
    # Look for temp/scenes/scene_{session_id}_*.mp4
    scene_pattern = os.path.join("temp", "scenes", f"scene_{session_id}_*.mp4")
    scene_files = glob.glob(scene_pattern)
    
    if scene_files and len(scene_files) >= len(recovered_timeline):
        print(f"   [Resume] Found {len(scene_files)} rendered scenes. Stitching immediately...")
        
        # Sort scenes
        def sort_key(fname):
            base = os.path.basename(fname)
            try: return int(base.split('_')[-1].split('.')[0])
            except: return 999999
        scene_files.sort(key=sort_key)
        
        # Manual FFmpeg Stitch (Fast)
        list_file = f"temp/stitch_list_{session_id}.txt"
        with open(list_file, 'w', encoding='utf-8') as f:
            for vid in scene_files:
                abs_path = os.path.abspath(vid).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")

        stitched_filename = f"temp/stitched_{session_id}.mp4"
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        import subprocess
        
        try:
            cmd = [ffmpeg_exe, "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", stitched_filename]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(stitched_filename):
                print("   [Resume] Stitching complete. Adding music...")
                
                from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
                from moviepy.audio.fx.all import volumex, audio_fadeout, audio_fadein
                
                final_video_clip = VideoFileClip(stitched_filename)
                
                print("   [Resume] Auto-selecting background music...")
                mood_name, keywords = ("Upbeat", ["upbeat", "happy", "fun", "pop"]) 
                bg_music = media_engine.create_background_music(mood_name, keywords, final_video_clip.duration)
                
                final_audio_list = [final_video_clip.audio]
                if bg_music: final_audio_list.append(bg_music.fx(volumex, 0.15))
                
                final_video_clip = final_video_clip.set_audio(CompositeAudioClip(final_audio_list))
                
                final_output_filename = f"finished_{session_id}.mp4"
                final_video_clip.write_videofile(final_output_filename, codec='libx264', audio_codec='aac', fps=24, preset='ultrafast', threads=4, logger=None)
                
                return final_output_filename, session_id, recovered_timeline, recovered_video_files, recovered_audio_files
        except Exception as e:
            print(f"   [Resume Error] Stitching failed: {e}")

    # --- CHECK 3: FULL RE-RENDER (Last Resort) ---
    print(f"   [Resume] Scenes missing. Re-rendering from raw assets...")
    
    try:
        from moviepy.editor import VideoFileClip
        if recovered_video_files[0].endswith(".mp4"):
            clip = VideoFileClip(recovered_video_files[0])
            if clip.w < clip.h: config.VIDEO_MODE = "Shorts"
            else: config.VIDEO_MODE = "Long"
            clip.close()
    except: pass
    
    music_data = media_engine.get_music_mood()
    final_video = media_engine.combine_scenes(recovered_timeline, recovered_video_files, recovered_audio_files, session_id, music_data)
    
    return final_video, session_id, recovered_timeline, recovered_video_files, recovered_audio_files


if __name__ == "__main__":
    print(f"---------------------------------------------------")
    print(f" SYSTEM STARTUP")
    print(f"---------------------------------------------------")

    mode_action = select_video_mode()
    
    # --- SELECT LANGUAGE TARGET ---
    target_lang = "BOTH"
    if mode_action == "NEW":
        target_lang = select_language_mode()
    elif mode_action == "RESUME":
        target_lang = "BOTH" 

    final_video = None
    topic = "Resumed Video" 
    
    hindi_ready = False
    english_timeline = None
    english_videos = None
    english_music = None
    english_audio = None
    
    # --- NEW SESSION ---
    if mode_action == "NEW":
        session_id = str(random.randint(1000, 9999))
        was_uploaded = False

        try:
            # Smart Auth: Connect to Hindi immediately if Hindi Only
            startup_profile = "hindi" if target_lang == "HINDI_ONLY" else "english"
            sheets, youtube = studio.get_services(profile=startup_profile)
            
            if sheets and youtube:
                print(f"   [System] Session ID: {session_id}")
                
                topic = generators.get_smart_topic(force_random=False)
                
                # --- FIX: SAVE TO HISTORY IMMEDIATELY ---
                try:
                    history_path = getattr(config, 'HISTORY_FILE', 'history.txt')
                    with open(history_path, "a", encoding="utf-8") as f:
                        f.write(topic + "\n")
                    print(f"   [History] Topic saved to exclusion list: {topic}")
                except Exception as e:
                    print(f"   [History Warning] Could not save topic: {e}")
                # ----------------------------------------

                raw_title, timeline, tags = generators.generate_scene_data(topic)
                
                if timeline:
                    # Capture data for Hindi Render
                    english_timeline = timeline
                    music_data = media_engine.get_music_mood()
                    english_music = music_data
                    
                    audio_files = asyncio.run(generators.generate_segmented_audio(timeline, session_id))
                    english_audio = audio_files
                    
                    video_files = generators.download_specific_scenes(timeline, session_id)
                    english_videos = video_files
                    
                    if audio_files and video_files:
                        # --- OPTIMIZATION: SKIP ENGLISH RENDER IF HINDI ONLY ---
                        if target_lang == "HINDI_ONLY":
                            print("\n   [Optimization] Skipping English Render (Target: Hindi Only).")
                            print("   [System] Assets preserved for Hindi Twin-Render.")
                            final_video = "SKIPPED_ENGLISH" # Flag to signal success without file
                            hindi_ready = True
                        else:
                            # Standard Render
                            final_video = media_engine.combine_scenes(timeline, video_files, audio_files, session_id, music_data)
                            if final_video: hindi_ready = True
                    else: print("\n[ERROR] Asset generation failed.")
                else: print("\n[ERROR] Timeline generation failed.")
            else: print("\n[ERROR] Auth failed.")

        except Exception as e:
            print(f"\n[CRITICAL ERROR] {e}")
            traceback.print_exc()

    # --- RESUME SESSION ---
    elif mode_action == "RESUME":
        final_video, session_id, r_timeline, r_videos, r_audio = resume_workflow()
        
        if final_video and r_timeline:
            print(f"   [System] Session {session_id} successfully restored.")
            english_timeline = r_timeline
            english_videos = r_videos
            english_audio = r_audio
            hindi_ready = True
            english_music = ("Upbeat", ["upbeat"]) 
            sheets, youtube = studio.get_services(profile="english")
            try:
                if os.path.exists("temp/description.txt"):
                    with open("temp/description.txt", "r", encoding="utf-8") as f:
                        c = f.read()
                        if "TITLE:" in c: topic = c.split("TITLE:")[1].split("\n")[0].strip()
            except: pass
        else:
            print("[Error] Resume failed.")
            sys.exit()

    # --- FINAL STEPS (ENGLISH) ---
    english_title = topic
    
    # 1. Stronger Default Description
    english_desc = (
        "🤯 The truth is stranger than fiction... \n\n"
        "If you love deep dives, dark history, and unexplained mysteries, "
        "you are in the right place.\n\n"
        "👇 SUBSCRIBE FOR DAILY TRUTH 👇"
    )
    
    # 2. Viral Hashtags Base
    english_tags = ["#Shorts", "#Viral", "#Facts", "#Mystery", "#DeepDive", "#ShortsFeed", "#Curiosity"]

    # 3. Expanded Viral Keyword Bank
    viral_keywords_en = [
        "Facts", "Mystery", "Documentary", "Educational", "Trending", "Amazing", 
        "Science", "History", "Unexplained", "DidYouKnow", "fyp",
        "DarkPsychology", "Scary", "Horror", "Creepy", "TrueCrime", "Conspiracy",
        "Paranormal", "GlitchInTheMatrix", "SimulationTheory", "MandelaEffect",
        "Technology", "AI", "Future", "Space", "Universe", "Aliens", "DeepWeb",
        "MindBlowing", "Shocking", "Forbidden", "Secret", "Hidden", "Truth"
    ]
    
    # SMART ENGLISH TAG GENERATION
    import re
    clean_words = re.sub(r'[^\w\s]', '', topic).split()
    topic_derived_tags = [f"#{w}" for w in clean_words if len(w) > 3 or w.upper() in ["AI", "UFO", "CIA", "FBI"]]

    # Niche Detection (English)
    topic_lower = topic.lower()
    niche_tags = []
    if any(x in topic_lower for x in ["ai", "robot", "gpt", "future", "tech"]): niche_tags.extend(["#AI", "#FutureTech"])
    if any(x in topic_lower for x in ["space", "mars", "moon", "earth", "alien"]): niche_tags.extend(["#Space", "#Cosmos"])
    if any(x in topic_lower for x in ["scary", "death", "ghost", "dark", "crime"]): niche_tags.extend(["#Horror", "#Creepy"])
    
    all_hashtags = list(set(english_tags + topic_derived_tags + niche_tags))
    random.shuffle(all_hashtags)
    viral_hashtags_en = " ".join(all_hashtags[:25])


    # Only process English if it actually exists (and wasn't skipped)
    if final_video and os.path.exists(final_video) and final_video != "SKIPPED_ENGLISH":
        print(f"\n   ---------------------------------------------------")
        print(f"   [REVIEW] English Video ready: {final_video}")
        print(f"   ---------------------------------------------------")
        
        try:
            if os.path.exists("temp/description.txt"):
                with open("temp/description.txt", "r", encoding="utf-8") as f:
                    c = f.read()
                    if "TITLE:" in c: english_title = c.split("TITLE:")[1].split("DESCRIPTION:")[0].strip()
                    if "DESCRIPTION:" in c: english_desc = c.split("DESCRIPTION:")[1].split("TAGS:")[0].strip()
                    if "TAGS:" in c: english_tags = [t.strip() for t in c.split("TAGS:")[1].split(",")]
        except: pass

        combined_tags_en = list(set(english_tags + viral_keywords_en))
        final_english_tags = combined_tags_en[:18] 
        final_english_desc = f"""{english_title}\n\n{english_desc}\n\n SUBSCRIBE FOR MORE MYSTERIES\n{viral_hashtags_en}"""

        upload_choice = "y"
        if mode_action == "RESUME":
            print("\n   [Resume Check] Did you ALREADY upload the English video?")
            already_done = generators.smart_input("   > (y/n): ", timeout=60, default_value="n").strip().lower()
            if already_done == 'y': upload_choice = "n"

        if upload_choice == "y":
            wait_time = 600 if config.VIDEO_MODE == "Long" else 120
            upload_choice = generators.smart_input(f"   > Upload English? (y/n) [Auto-Yes {wait_time}s]: ", timeout=wait_time, default_value="y").strip().lower()

        if upload_choice == 'y':
            print("\n   [System] Uploading English Version...")
            thumbnail_file = media_engine.create_thumbnail(topic, session_id, background_image=None)
            video_link = studio.upload_to_youtube(youtube, final_video, thumbnail_file, english_title, final_english_desc, "", final_english_tags, profile="english")
            
            if video_link:
                studio.update_sheet(sheets, topic, video_link, profile="english")
                was_uploaded = True
                print(f"\n [SUCCESS] English Uploaded: {video_link}")
            else:
                was_uploaded = False 
                print(f"\n [SAVED] English saved locally.")
        else:
            print("\n   [System] English upload aborted.")
            was_uploaded = True 

    else:
        if mode_action == "NEW" and final_video != "SKIPPED_ENGLISH": 
             print("\n[ERROR] English Video creation failed.")

    # --- AUTOMATIC HINDI TWIN RENDER ---
    if target_lang in ["BOTH", "HINDI_ONLY"]:
        if hindi_ready and english_timeline and english_videos:
            print("\n===================================================")
            print(" 🇮🇳 AUTOMATIC HINDI TWIN-RENDER STARTING")
            print("===================================================")
            
            # 1. Translate Script
            print("   [System] Translating script to Hinglish...")
            hindi_timeline = translator.create_hindi_timeline(english_timeline)
            
            if hindi_timeline:
                # 2. Translate Meta
                print("   [System] Translating Title & Description...")
                hindi_meta = translator.translate_batch_to_hinglish([english_title, english_desc])
                
                hindi_title = english_title + " (Hinglish)" 
                hindi_desc_body = english_desc
                if hindi_meta and len(hindi_meta) >= 2:
                    hindi_title = hindi_meta[0].get('roman', english_title)
                    hindi_desc_body = hindi_meta[1].get('roman', english_desc)
                
                # --- SMART HINDI TAG GENERATOR ---
                # A. Base Viral Tags (Hindi)
                base_hashtags_hi = [
                    "#Shorts", "#Viral", "#Facts", "#Hindi", "#Rahasya", 
                    "#AmazingFacts", "#UnknownFacts", "#ShortsIndia", 
                    "#Trend", "#Gyan", "#YtShorts"
                ]

                # B. Extract Keywords (Hindi/Hinglish)
                topic_derived_tags_hi = [f"#{w}" for w in clean_words if len(w) > 3]

                # C. Niche-Specific Expansion (Hindi)
                niche_tags_hi = []
                
                # Horror/Mystery
                if any(x in topic_lower for x in ["scary", "ghost", "dark", "death", "mystery", "haunted", "khaufnak", "bhoot"]):
                    niche_tags_hi.extend(["#Khaufnak", "#Bhoot", "#HorrorStory", "#Darr", "#Rahasya", "#Paranormal"])
                
                # Space/Science
                if any(x in topic_lower for x in ["space", "universe", "alien", "moon", "mars", "earth", "science"]):
                    niche_tags_hi.extend(["#Antariksh", "#Brahmand", "#Vigyan", "#Aliens", "#SpaceFacts", "#NASA"])

                # Tech/AI
                if any(x in topic_lower for x in ["ai", "tech", "future", "robot", "internet"]):
                    niche_tags_hi.extend(["#Future", "#AI", "#Technology", "#Vigyan", "#Hacking"])

                # D. Combine & Shuffle Hashtags
                all_hashtags_hi = list(set(base_hashtags_hi + topic_derived_tags_hi + niche_tags_hi))
                random.shuffle(all_hashtags_hi)
                viral_hashtags_hi = " ".join(all_hashtags_hi[:25])

                # E. Update Keywords (Tags)
                viral_keywords_hi = [
                    "Rahasya", "Facts Hindi", "Kahani", "Romanchak", "Viral India", 
                    "Hindi Story", "Amazing Facts", "Gyan", "Knowledge", "Ajab Gajab",
                    "Khaufnak", "Asli Sach", "Vigyan", "Antariksh"
                ]
                
                combined_tags_hi = list(set(english_tags + viral_keywords_hi + viral_keywords_en))
                final_hindi_tags = combined_tags_hi[:25] 

                final_hindi_desc = f"""{hindi_title}

🤯 Ye sach aapko hairan kar dega... (This truth will shock you)

{hindi_desc_body}

🔥 Topics Covered:
- {topic}
- Unexplained Mysteries
- Dark Psychology
- Future Tech & AI
 SUBSCRIBE FOR DAILY DARK TRUTH 

{viral_hashtags_hi}"""

                hindi_session_id = session_id + "_HINDI"
                
                # 3. Generate Audio
                print("   [System] Generating Hindi Audio (Swara/Madhur)...")
                hindi_audio_files = asyncio.run(translator.generate_hindi_audio(hindi_timeline, hindi_session_id))
                
                if hindi_audio_files:
                    # 4. Render Video
                    print("   [System] Rendering Hindi Video (Reusing Visuals)...")
                    final_hindi_video = media_engine.combine_scenes(hindi_timeline, english_videos, hindi_audio_files, hindi_session_id, english_music)
                    
                    if final_hindi_video:
                        print(f"\n   ✅ HINDI VIDEO GENERATED: {final_hindi_video}")
                        
                        try:
                            hindi_thumb = media_engine.create_thumbnail(topic + " (Hindi)", hindi_session_id, background_image=None)
                        except: hindi_thumb = None
                        
                        wait_time = 600 if config.VIDEO_MODE == "Long" else 120
                        hindi_choice = generators.smart_input(f"   > Upload Hindi? (y/n) [Auto-Yes {wait_time}s]: ", timeout=wait_time, default_value="y").strip().lower()

                        if hindi_choice == 'y':
                            print("   [System] Uploading to Hindi Channel...")
                            h_sheets, h_youtube = studio.get_services(profile="hindi")
                            if h_youtube:
                                h_link = studio.upload_to_youtube(h_youtube, final_hindi_video, hindi_thumb, hindi_title, final_hindi_desc, "", final_hindi_tags, profile="hindi")
                                if h_link:
                                    studio.update_sheet(h_sheets, hindi_title, h_link, profile="hindi")
                                    print(f"\n   🇮🇳 [SUCCESS] Hindi Version Uploaded: {h_link}")
                                else:
                                    print("\n   [Warning] Hindi Upload failed. File saved.")
                            else:
                                print("\n   [Error] Could not auth Hindi Channel.")
                        else:
                            print("\n   [System] Hindi upload aborted. Video saved locally.")
                    else: print("   [Error] Hindi Render Failed.")
                else: print("   [Error] Hindi Audio Failed.")
            else: print("   [Error] Translation Failed.")
    else:
        print("\n   [System] Skipping Hindi Render (Mode: English Only).")

    # --- CLEANUP ---
    if 'session_id' in locals() and session_id:
        if 'topic' in locals() and topic:
            try:
                history_path = getattr(config, 'HISTORY_FILE', 'history.txt')
                with open(history_path, "a", encoding="utf-8") as f:
                    f.write(topic + "\n")
            except: pass

        print("\n---------------------------------------------------")
        studio.manage_session_files(session_id, locals().get('was_uploaded', False))
        print(" JOB FINISHED.")
        print("---------------------------------------------------")