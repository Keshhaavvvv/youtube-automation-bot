# final_test_bot.py (The Simulator)
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

# --- CRITICAL: IMPORT CONFIG FIRST ---
import config 

# --- IMPORT TEAMS ---
import generators    # The Writer
import media_engine  # The Editor
import studio        # The Manager
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
    print(f" 🧪 FINAL SYSTEM TEST (NO UPLOAD MODE)")
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

def resume_workflow():
    """
    Advanced Rescue Logic (Copied from bot.py)
    """
    print(f"\n---------------------------------------------------")
    print(f" 🚑 SESSION RESCUE MODE")
    print(f"---------------------------------------------------")
    
    session_id = input(" > Enter the Session ID to resume (e.g., 9593): ").strip()
    if not session_id: return None, None, None, None, None

    # --- DATA RECONSTRUCTION ---
    print(f"   [Resume] Rebuilding timeline data for Session {session_id}...")
    recovered_timeline = []
    recovered_video_files = []
    recovered_audio_files = []
    
    i = 0
    while True:
        a_path = os.path.join("temp", f"audio_{i}_{session_id}.mp3")
        v_path = os.path.join("temp", f"clip_{i}_{session_id}.mp4")
        if not os.path.exists(v_path):
            v_path = os.path.join("temp", f"clip_{i}_{session_id}.png")
        if not os.path.exists(v_path):
            v_path = os.path.join("temp", f"clip_{i}_{session_id}.jpg")
            
        t_path = os.path.join("temp", f"timing_{i}_{session_id}.json")
        
        if os.path.exists(a_path) and os.path.exists(v_path):
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
        print("   [Error] No raw assets found. Cannot proceed.")
        return None, None, None, None, None

    print(f"   [Resume] Data recovered: {len(recovered_timeline)} scenes.")

    # --- CHECK 1: FINISHED VIDEO ---
    finished_path = f"finished_{session_id}.mp4"
    if os.path.exists(finished_path):
        print(f"   [Resume] Found finished video: {finished_path}")
        return finished_path, session_id, recovered_timeline, recovered_video_files, recovered_audio_files

    # --- CHECK 2: RENDERED SCENES ---
    scene_pattern = os.path.join("temp", "scenes", f"scene_{session_id}_*.mp4")
    scene_files = glob.glob(scene_pattern)
    
    if scene_files and len(scene_files) >= len(recovered_timeline):
        print(f"   [Resume] Found {len(scene_files)} rendered scenes. Stitching...")
        
        def sort_key(fname):
            base = os.path.basename(fname)
            try: return int(base.split('_')[-1].split('.')[0])
            except: return 999999
        scene_files.sort(key=sort_key)
        
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
            # Re-encode stitch for safety in resume too
            cmd = [ffmpeg_exe, "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c:v", "libx264", "-c:a", "aac", stitched_filename]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(stitched_filename):
                print("   [Resume] Stitching complete. Adding music...")
                from moviepy.editor import VideoFileClip, CompositeAudioClip
                from moviepy.audio.fx.all import volumex
                
                final_video_clip = VideoFileClip(stitched_filename)
                mood_name, keywords = ("Upbeat", ["upbeat", "happy"]) 
                bg_music = media_engine.create_background_music(mood_name, keywords, final_video_clip.duration)
                
                final_audio_list = [final_video_clip.audio]
                if bg_music: final_audio_list.append(bg_music.fx(volumex, 0.15))
                
                final_video_clip = final_video_clip.set_audio(CompositeAudioClip(final_audio_list))
                final_output_filename = f"finished_{session_id}.mp4"
                final_video_clip.write_videofile(final_output_filename, codec='libx264', audio_codec='aac', fps=24, preset='ultrafast', threads=4, logger=None)
                
                return final_output_filename, session_id, recovered_timeline, recovered_video_files, recovered_audio_files
        except Exception as e:
            print(f"   [Resume Error] Stitching failed: {e}")

    # --- CHECK 3: RE-RENDER ---
    print(f"   [Resume] Scenes missing. Re-rendering...")
    music_data = media_engine.get_music_mood()
    final_video = media_engine.combine_scenes(recovered_timeline, recovered_video_files, recovered_audio_files, session_id, music_data)
    
    return final_video, session_id, recovered_timeline, recovered_video_files, recovered_audio_files


if __name__ == "__main__":
    print(f"---------------------------------------------------")
    print(f" SYSTEM STARTUP (TEST SIMULATION)")
    print(f"---------------------------------------------------")

    mode_action = select_video_mode()
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
            # [TEST MODE] Bypass actual Auth check to ensure generation works even without credentials
            print(f"   [System] Session ID: {session_id}")
            print(f"   [TEST MODE] Bypassing Google Auth for generation phase...")
            sheets = "MockSheet"
            youtube = "MockYouTube"

            if sheets and youtube:
                topic = generators.get_smart_topic(force_random=False)
                raw_title, timeline, tags = generators.generate_scene_data(topic)
                
                if timeline:
                    english_timeline = timeline
                    
                    music_data = media_engine.get_music_mood()
                    english_music = music_data
                    
                    audio_files = asyncio.run(generators.generate_segmented_audio(timeline, session_id))
                    english_audio = audio_files
                    
                    video_files = generators.download_specific_scenes(timeline, session_id)
                    english_videos = video_files
                    
                    if audio_files and video_files:
                        final_video = media_engine.combine_scenes(timeline, video_files, audio_files, session_id, music_data)
                        if final_video: hindi_ready = True
                    else: print("\n[ERROR] Asset generation failed.")
                else: print("\n[ERROR] Timeline generation failed.")

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
            
            # Try to recover topic
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
    english_desc = "Watch to learn more."
    english_tags = ["#Viral", "#Shorts"]

    # 1. Define Viral Keywords (English)
    viral_keywords_en = ["Facts", "Mystery", "Trending", "Amazing", "Science", "History", "fyp"]

    if final_video and os.path.exists(final_video):
        print(f"\n   ---------------------------------------------------")
        print(f"   [REVIEW] English Video ready: {final_video}")
        print(f"   ---------------------------------------------------")
        
        # Load Metadata
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
        viral_hashtags_en = "#Shorts #Viral #Facts #Trending #Documentary #fyp #Mystery"

        final_english_desc = f"{english_title}\n\n{english_desc}\n\n{viral_hashtags_en}"

        # --- TEST MODE SIMULATION ---
        wait_time = 10
        upload_choice = generators.smart_input(f"   > [TEST] Simulate Upload English? (y/n) [Auto-Yes {wait_time}s]: ", timeout=wait_time, default_value="y").strip().lower()

        if upload_choice == 'y':
            print("\n   [TEST MODE] Simulating English Upload...")
            
            # Create Thumbnail (Still do this to test if it works)
            thumbnail_file = media_engine.create_thumbnail(topic, session_id, background_image=None)
            
            # --- SIMULATION ---
            video_link = "https://youtube.com/watch?v=TEST_SIMULATION_LINK"
            print(f"   [TEST MODE] Upload 'Success'. Link: {video_link}")
            print(f"   [TEST MODE] Sheet update skipped.")
            
            was_uploaded = True
            print(f"\n [SUCCESS] English Simulation Complete.")
        else:
            print("\n   [System] English upload aborted.")
            was_uploaded = True 
            
    else:
        if mode_action == "NEW": print("\n[ERROR] English Video creation failed.")

    # --- AUTOMATIC HINDI TWIN RENDER ---
    if hindi_ready and english_timeline and english_videos:
        print("\n===================================================")
        print(" 🇮🇳 AUTOMATIC HINDI TWIN-RENDER STARTING")
        print("===================================================")
        
        # 1. Translate Script
        print("   [System] Translating script to Hinglish...")
        hindi_timeline = translator.create_hindi_timeline(english_timeline)
        
        if hindi_timeline:
            # 2. Translate Title & Description
            print("   [System] Translating Title & Description...")
            hindi_meta = translator.translate_batch_to_hinglish([english_title, english_desc])
            
            hindi_title = english_title + " (Hinglish)" 
            hindi_desc_body = english_desc
            
            if hindi_meta and len(hindi_meta) >= 2:
                hindi_title = hindi_meta[0].get('roman', english_title)
                hindi_desc_body = hindi_meta[1].get('roman', english_desc)
            
            viral_hashtags_hi = "#Shorts #Viral #Facts #Rahasya #Hindi #Trending #India"
            final_hindi_desc = f"{hindi_title}\n\n{hindi_desc_body}\n\n{viral_hashtags_hi}"
            final_hindi_tags = ["#Hindi", "#Facts"]

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
                    
                    # 5. TEST MODE SIMULATION
                    wait_time = 10
                    hindi_choice = generators.smart_input(f"   > [TEST] Simulate Upload Hindi? (y/n) [Auto-Yes {wait_time}s]: ", timeout=wait_time, default_value="y").strip().lower()

                    if hindi_choice == 'y':
                        print("   [TEST MODE] Simulating Hindi Upload...")
                        h_link = "https://youtube.com/watch?v=TEST_HINDI_LINK"
                        print(f"   [TEST MODE] Upload 'Success'. Link: {h_link}")
                        print(f"\n   🇮🇳 [SUCCESS] Hindi Simulation Complete.")
                    else:
                        print("\n   [System] Hindi upload aborted.")

                else: print("   [Error] Hindi Render Failed.")
            else: print("   [Error] Hindi Audio Failed.")
        else: print("   [Error] Translation Failed.")

    # --- CLEANUP ---
    if 'session_id' in locals() and session_id:
        print("\n---------------------------------------------------")
        # In test mode, we might want to keep files to inspect them.
        # studio.manage_session_files(session_id, locals().get('was_uploaded', False))
        print(" [TEST MODE] Cleanup skipped so you can inspect files in 'temp/'")
        print(" JOB FINISHED.")
        print("---------------------------------------------------")