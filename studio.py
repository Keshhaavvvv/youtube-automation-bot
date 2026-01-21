# studio.py
import os
import time
import shutil
import gc
import math
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy.editor import VideoFileClip
import config

# --- TEMP DIRECTORY ---
TEMP_DIR = "temp"

# --- GOOGLE SERVICES ---
def get_services():
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', [
                'https://www.googleapis.com/auth/youtube.upload',
                'https://www.googleapis.com/auth/drive.file',
                'https://www.googleapis.com/auth/spreadsheets'
            ])
            return build('sheets', 'v4', credentials=creds), build('youtube', 'v3', credentials=creds)
        except: return None, None
    return None, None

def update_sheet(service, topic, url):
    if not url: return
    try:
        # 1. Get Current Timestamp
        upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 2. Get Video Mode (Shorts/Long)
        mode = config.VIDEO_MODE if hasattr(config, 'VIDEO_MODE') else "Shorts"
        
        # 3. Prepare Row Data: [Date, Mode, Topic, Status, Link]
        row = [[upload_time, mode, f"{topic}", "Uploaded", url]]
        
        service.spreadsheets().values().append(
            spreadsheetId=config.SPREADSHEET_ID, range="Sheet1!A1",
            valueInputOption="USER_ENTERED", body={"values": row}
        ).execute()
        print(f"   Sheet Updated: {upload_time} | {mode}")
    except Exception as e: 
        print(f"   [Sheet Error] Could not update: {e}")

# --- AUTO-CHAPTER GENERATOR ---
def generate_seo_description(topic, video_path):
    """Creates a description with Timestamps (Chapters) for SEO."""
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        
        # Calculate timestamps
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

def upload_to_youtube(youtube, file_path, thumbnail_path, title, topic, script, tags):
    print(f"4. Uploading Video: {title}...")
    
    # Generate Smart Description
    final_description = generate_seo_description(topic, file_path)
    
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
        print(f"   Video Uploaded! ID: {response['id']}")
        
        # --- THUMBNAIL UPLOAD (DEBUG MODE) ---
        if thumbnail_path and os.path.exists(thumbnail_path):
             print(f"   [Thumbnail] Attempting upload: {thumbnail_path}")
             try:
                 youtube.thumbnails().set(videoId=response['id'], media_body=MediaFileUpload(thumbnail_path)).execute()
                 print("   [Thumbnail] Success! Custom thumbnail set.")
             except Exception as e:
                 print(f"   [Thumbnail Error] YouTube Rejected Image: {e}")
                 print("   (Note: YouTube API often blocks custom thumbnails for Shorts.)")
        else:
            print("   [Thumbnail] No file found to upload.")

        return f"https://youtu.be/{response['id']}"
    except Exception as e:
        print(f"   [Error] Upload Failed: {e}")
        return None

# --- FILE MANAGEMENT ---
def safe_move(src, dst):
    for i in range(5):
        try:
            # Ensure we are moving to a file path, not just a dir
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
    gc.collect()
    
    final_video = f"final_{session_id}.mp4"
    
    # 1. Handle Final Video
    if was_uploaded:
        if os.path.exists(final_video):
            if force_delete(final_video):
                print(f"   [Cleanup] Upload successful. Deleted {final_video}")
            else:
                print(f"   [Warning] Could not delete {final_video} (Locked)")
    else:
        if os.path.exists(final_video):
            target_dir = "pending_uploads"
            if not os.path.exists(target_dir): os.makedirs(target_dir)
            try:
                safe_move(final_video, target_dir)
                print(f"   [Saved] Upload failed. Video saved to {target_dir}/")
            except: pass

    # 2. Clean 'temp' Folder
    files_cleaned = 0
    if os.path.exists(TEMP_DIR):
        for f in os.listdir(TEMP_DIR):
            if session_id in f:
                file_path = os.path.join(TEMP_DIR, f)
                if force_delete(file_path):
                    files_cleaned += 1
    
    if files_cleaned > 0:
        print(f"   [Cleanup] Removed {files_cleaned} temporary files from {TEMP_DIR}/.")