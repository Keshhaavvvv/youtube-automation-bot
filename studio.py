# studio.py
import os
import time
import shutil
import gc
import pickle # <--- Added for reading binary tokens
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request # Needed for refreshing
from moviepy.editor import VideoFileClip
import config

# --- TEMP DIRECTORY ---
TEMP_DIR = "temp"

# --- GOOGLE SERVICES (MULTI-CHANNEL) ---
def get_services(profile="english"):
    """
    Authenticates based on the profile ('english' or 'hindi').
    Loads credentials using Pickle (Binary).
    """
    token_file = 'token_hindi.json' if profile == 'hindi' else 'token.json'
    
    print(f"   [Studio] Connecting to {profile.upper()} channel ({token_file})...")
    
    creds = None
    
    if os.path.exists(token_file):
        try:
            # FIX: Open in Binary Mode ('rb') and use pickle.load
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            print(f"   [Auth Error] Could not load credentials: {e}")
            return None, None
            
    # Refresh if expired
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"   [Auth] Token expired and refresh failed: {e}")
                return None, None
        else:
            print("   [Auth] No valid token found. Please run auth.py.")
            return None, None

    try:
        return build('sheets', 'v4', credentials=creds), build('youtube', 'v3', credentials=creds)
    except Exception as e:
        print(f"   [Service Error] {e}")
        return None, None

def update_sheet(service, topic, url, profile="english"):
    if not url: return
    try:
        # 1. Get Current Timestamp
        upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 2. Get Video Mode
        mode = config.VIDEO_MODE if hasattr(config, 'VIDEO_MODE') else "Shorts"
        
        # 3. Determine Target Sheet Tab
        sheet_range = "Hindi_Uploads!A1" if profile == "hindi" else "Sheet1!A1"
        
        # 4. Prepare Row Data
        row = [[upload_time, mode, f"{topic}", "Uploaded", url]]
        
        service.spreadsheets().values().append(
            spreadsheetId=config.SPREADSHEET_ID, 
            range=sheet_range,
            valueInputOption="USER_ENTERED", 
            body={"values": row}
        ).execute()
        print(f"   [Sheet] Updated '{sheet_range}' for {profile.upper()}.")
    except Exception as e: 
        print(f"   [Sheet Error] Could not update: {e}")

# --- AUTO-CHAPTER GENERATOR ---
def generate_seo_description(topic, video_path):
    """Creates a description with Timestamps (Chapters) for SEO."""
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        
        t_body = int(duration * 0.20)
        t_conclusion = int(duration * 0.85)
        
        def fmt_time(seconds):
            m, s = divmod(seconds, 60)
            return f"{int(m):02d}:{int(s):02d}"

        description = f"""{topic}

In this video, we explore the fascinating truth behind {topic}.

TIMESTAMPS:
00:00 - Introduction
{fmt_time(t_body)} - The Deep Dive
{fmt_time(t_conclusion)} - Conclusion & Summary

#shorts #facts #{topic.split()[0].lower()} #documentary #learning
"""
        return description.strip()
    except:
        return f"{topic}\n\n#shorts #facts"

def upload_to_youtube(youtube, file_path, thumbnail_path, title, description, script_placeholder, tags, profile="english"):
    """
    Uploads video to the connected YouTube channel.
    """
    print(f"4. Uploading to {profile.upper()} Channel: {title}...")
    
    # --- SMART DESCRIPTION LOGIC ---
    final_description = description
    if len(description) < 50:
        print("   [SEO] Generating auto-description/chapters...")
        final_description = generate_seo_description(description, file_path)
    
    try:
        body = {
            'snippet': {
                'title': title,
                'description': final_description,
                'tags': tags,
                'categoryId': '22' 
            },
            'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
        }
        
        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
        response = request.execute()
        
        video_id = response['id']
        print(f"   [Success] Video ID: {video_id}")
        
        # --- THUMBNAIL UPLOAD ---
        if thumbnail_path and os.path.exists(thumbnail_path):
             print(f"   [Thumbnail] Uploading: {thumbnail_path}")
             try:
                 youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumbnail_path)).execute()
                 print("   [Thumbnail] Set successfully.")
             except Exception as e:
                 print(f"   [Thumbnail Warning] {e}")
        else:
            print("   [Thumbnail] Skipped (No file).")

        return f"https://youtu.be/{video_id}"
        
    except Exception as e:
        print(f"   [Upload Error] {e}")
        return None

# --- FILE MANAGEMENT ---
def safe_move(src, dst):
    for i in range(5):
        try:
            shutil.move(src, os.path.join(dst, os.path.basename(src)))
            return True
        except Exception as e:
            time.sleep(1)
    return False

def force_delete(file_path):
    gc.collect() 
    for i in range(5):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except PermissionError:
            time.sleep(1)
            gc.collect()
        except Exception:
            return False
    return False

def manage_session_files(session_id, was_uploaded):
    print("   [File Manager] Cleaning up session files...")
    import gc
    gc.collect()
    
    TEMP_DIR = "temp" # Ensure this is defined
    
    # 1. HANDLE FINAL VIDEOS (Main Folder)
    video_patterns = [
        f"finished_{session_id}.mp4", 
        f"finished_{session_id}_HINDI.mp4",
        f"finished_{session_id}",
        f"finished_{session_id}_HINDI_HINDI"
    ]
    
    for final_video in video_patterns:
        if os.path.exists(final_video):
            if was_uploaded:
                if force_delete(final_video):
                    print(f"   [Cleanup] Deleted {final_video}")
            else:
                target_dir = "pending_uploads"
                if not os.path.exists(target_dir): os.makedirs(target_dir)
                try:
                    safe_move(final_video, target_dir)
                    print(f"   [Saved] Moved {final_video} to {target_dir}/")
                except: pass

    # 2. AGGRESSIVE ROOT CLEANUP
    files_cleaned = 0
    try:
        for f in os.listdir('.'):
            if (session_id in f) or ("TEMP_MPY" in f and session_id in f):
                if f.startswith("finished_") and not was_uploaded: continue
                if os.path.isfile(f):
                    if force_delete(f):
                        files_cleaned += 1
                        print(f"   [Cleanup] Deleted stray file: {f}")
    except Exception as e:
        print(f"   [Warning] Root cleanup scan failed: {e}")

    # 3. CLEAN 'TEMP' FOLDER (Audio, Images, Description)
    if os.path.exists(TEMP_DIR):
        for f in os.listdir(TEMP_DIR):
            # --- THE FIX: Check for session ID OR explicit 'description.txt' ---
            if session_id in f or f == "description.txt":
                file_path = os.path.join(TEMP_DIR, f)
                if force_delete(file_path):
                    files_cleaned += 1
                    
    # 4. CLEAN 'TEMP/SCENES' FOLDER
    scenes_dir = os.path.join(TEMP_DIR, "scenes")
    if os.path.exists(scenes_dir):
        for f in os.listdir(scenes_dir):
            if session_id in f:
                file_path = os.path.join(scenes_dir, f)
                if force_delete(file_path):
                    files_cleaned += 1
    
    if files_cleaned > 0:
        print(f"   [Cleanup] Removed {files_cleaned} temporary assets.")