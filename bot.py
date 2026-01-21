# bot.py (The Manager)
import sys
import random
import asyncio
import socket
import os
import warnings
import traceback

# --- IMPORT TEAMS ---
import generators    # The Writer (Script, Audio, Scenes)
import media_engine  # The Editor (Stitching, Music)
import effects       # The Artist (Thumbnails, Overlays)
import studio        # The Manager (Uploads, Sheets, Cleanup)
import config        # Config to change modes

# --- SYSTEM CONFIG ---
socket.setdefaulttimeout(30)
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '2'
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding='utf-8')

def select_video_mode():
    """Asks the user to select the video format before starting."""
    print(f"---------------------------------------------------")
    print(f" SELECT VIDEO MODE (Auto: Long Form in 60s)")
    print(f"---------------------------------------------------")
    print(" 1. Shorts (Vertical 9:16, ~60 sec)")
    print(" 2. Long Form (Horizontal 16:9, ~10 mins)")
    
    # Auto-select Long Form (2) after 60 seconds
    choice = generators.smart_input(" > Enter choice (1 or 2): ", timeout=60, default_value="2").strip()
    
    if choice == "2":
        config.VIDEO_MODE = "Long"
        print(f"   [System] Mode set to: LONG FORM (Horizontal)")
    else:
        config.VIDEO_MODE = "Shorts"
        print(f"   [System] Mode set to: SHORTS (Vertical)")

if __name__ == "__main__":
    print(f"---------------------------------------------------")
    print(f" SYSTEM STARTUP")
    print(f"---------------------------------------------------")

    # --- STEP 0: SELECT MODE ---
    select_video_mode()

    session_id = str(random.randint(1000, 9999))
    was_uploaded = False

    try:
        # 1. Connect to Services
        sheets, youtube = studio.get_services()
        
        if sheets and youtube:
            print(f"   [System] Session ID: {session_id}")

            # 2. Get Topic & Scenes
            # (Timeout logic is handled inside generators.get_smart_topic)
            topic = generators.get_smart_topic(force_random=False)
            
            # The generator looks at config.VIDEO_MODE to decide length
            title, timeline, tags = generators.generate_scene_data(topic)
            
            if timeline:
                # --- NEW LOCATION: SELECT MUSIC HERE ---
                # We ask for music preference BEFORE starting the heavy downloads.
                # This allows the user to configure everything and walk away.
                music_data = media_engine.get_music_mood()

                # 3. Assets
                # Now the bot does the heavy lifting (Audio & Video)
                audio_files = asyncio.run(generators.generate_segmented_audio(timeline, session_id))
                
                # The downloader looks at config.VIDEO_MODE for orientation
                video_files = generators.download_specific_scenes(timeline, session_id)
                
                if audio_files and video_files:
                    
                    # 4. Edit Video 
                    # We pass the 'music_data' we selected earlier
                    final_video = media_engine.combine_scenes(timeline, video_files, audio_files, session_id, music_data)
                    
                    if final_video and os.path.exists(final_video):
                        # --- NEW: HUMAN REVIEW GATE (TIMED) ---
                        print(f"\n   ---------------------------------------------------")
                        print(f"   [REVIEW] Video generated successfully: {final_video}")
                        print(f"   Please open the folder and watch the video file now.")
                        
                        # Determine timeout based on mode
                        if config.VIDEO_MODE == "Long":
                            wait_time = 600 # 10 mins
                            mode_str = "10 mins"
                        else:
                            wait_time = 120 # 2 mins
                            mode_str = "2 mins"
                            
                        print(f"   Auto-Upload in {mode_str} if no response.")
                        print(f"   ---------------------------------------------------")
                        
                        # Default is 'y' (Upload) if user walks away
                        upload_choice = generators.smart_input("   > Upload this video to YouTube? (y/n): ", timeout=wait_time, default_value="y").strip().lower()

                        if upload_choice == 'y':
                            print("\n   [System] Proceeding with Upload...")
                            
                            # 6. Thumbnail (Only generate if we are uploading)
                            # This now saves to temp/thumbnail_ID.jpg
                            thumbnail_file = effects.generate_thumbnail(final_video, topic, session_id)
                            
                            # 7. Upload
                            # studio.py handles the description generation and tagging
                            video_link = studio.upload_to_youtube(youtube, final_video, thumbnail_file, title, topic, "", tags)
                            
                            if video_link:
                                studio.update_sheet(sheets, topic, video_link)
                                was_uploaded = True
                                print(f"\n [SUCCESS] Video Uploaded: {video_link}")
                            else:
                                was_uploaded = False # Keeps file for manual upload
                                print(f"\n [SAVED] Video saved locally (Upload failed).")
                        
                        else:
                            print("\n   [System] Upload aborted by user.")
                            # We mark as 'uploaded' (true) to trigger the DELETION cleanup in studio.py
                            # This ensures the final video is deleted if the user said "No" to keeping it.
                            # If you want to KEEP the video but not upload, change this to False.
                            print(f"   [System] Deleting {final_video}...")
                            was_uploaded = True 
                            
                    else:
                        print("\n[ERROR] Video editing failed or file not found.")
                else:
                    print("\n[ERROR] Skipped: Could not generate assets.")
            else:
                 print("\n[ERROR] Timeline generation failed.")

        else:
            print("\n[ERROR] Authentication failed. Please Delete 'token.json' and run auth.py again.")

    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
        traceback.print_exc()

    finally:
        # --- GUARANTEED CLEANUP ---
        # This will now clean the 'temp' folder correctly
        print("\n---------------------------------------------------")
        studio.manage_session_files(session_id, was_uploaded)
        print(" JOB FINISHED.")
        print("---------------------------------------------------")