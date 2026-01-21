# effects.py
import os
import time
import warnings
import random
import requests
import urllib.parse
from PIL import Image, ImageDraw, ImageFont

# Suppress Warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from moviepy.editor import VideoFileClip, AudioFileClip, TextClip
from moviepy.video.fx.all import mask_color
from moviepy.audio.fx.all import volumex
from moviepy.config import change_settings

# --- NEW AI LIBRARY ---
from google import genai
import config 

# --- SETUP ---
if os.path.exists(config.IMAGEMAGICK_PATH):
    change_settings({"IMAGEMAGICK_BINARY": config.IMAGEMAGICK_PATH})

if not hasattr(Image, 'ANTIALIAS'): Image.ANTIALIAS = Image.LANCZOS

# --- TEMP DIRECTORY ---
TEMP_DIR = "temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# --- HELPER: GET AI CLIENT ---
def get_client():
    api_key = config.GEMINI_API_KEY
    if hasattr(config, 'API_KEYS') and config.API_KEYS:
        api_key = random.choice(config.API_KEYS)
    return genai.Client(api_key=api_key)

# --- OVERLAYS ---

def create_watermark(duration):
    """Creates the channel name overlay, positioned based on mode."""
    try:
        # Determine Mode
        mode = config.VIDEO_MODE if hasattr(config, 'VIDEO_MODE') else "Shorts"
        
        # Position Logic
        if mode == "Shorts":
            # Vertical: Bottom Center
            position = ('center', 1600)
            fontsize = 40
        else:
            # Horizontal: Bottom Right Corner
            position = ('right', 'bottom') 
            fontsize = 30 # Smaller for long form
            
        watermark = TextClip(
            config.CHANNEL_NAME, 
            fontsize=fontsize, 
            color='white', 
            font='Arial', 
            bg_color='black'
        )
        
        # Add some padding if horizontal
        if mode == "Long":
             watermark = watermark.margin(right=20, bottom=20, opacity=0)

        watermark = watermark.set_opacity(0.6).set_pos(position).set_duration(duration)
        return watermark
    except:
        return None

def create_subscribe_overlay(total_duration):
    """Creates the Green Screen Subscribe animation + Bell Sound."""
    subscribe_path = "assets/subscribe.mp4"
    bell_path = "assets/bell.mp3"
    
    cta_clip = None
    bell_audio = None

    if not os.path.exists(subscribe_path):
        return None, None

    try:
        # Determine Mode for Sizing & Position
        mode = config.VIDEO_MODE if hasattr(config, 'VIDEO_MODE') else "Shorts"

        # Load and Mask Green Screen
        cta = VideoFileClip(subscribe_path)
        cta = cta.fx(mask_color, color=[0, 255, 0], s=5, thr=100)
        
        # Resize based on mode
        if mode == "Shorts":
            cta = cta.resize(width=800)
            pos_y = 1400 # Lower third of vertical
        else:
            cta = cta.resize(width=600) # Smaller for horizontal
            pos_y = 800 # Bottom center of 1080p height
        
        # --- TIMING FIX ---
        cta_duration = cta.duration
        start_time = total_duration - cta_duration
        
        if start_time < 0: 
            start_time = 0
            cta = cta.subclip(0, total_duration)

        cta = cta.set_start(start_time).set_position(('center', pos_y))
        cta_clip = cta
        
        # Load Bell Sound
        if os.path.exists(bell_path):
            bell_audio = AudioFileClip(bell_path).fx(volumex, 0.8).set_start(start_time)
            
        return cta_clip, bell_audio

    except Exception as e:
        print(f"   [Effects] Error creating overlay: {e}")
        return None, None

# --- THUMBNAILS ---

def download_ai_image(prompt, filename, width, height):
    """Downloads a generated image from Pollinations.ai"""
    try:
        # Enhance prompt for better visual quality
        enhanced_prompt = f"{prompt}, cinematic lighting, hyperrealistic, 8k, detailed, dramatic atmosphere"
        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        
        # Seed for randomness
        seed = random.randint(1, 99999)
        
        # Construct URL
        # Model 'flux' is excellent for general art
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=flux&seed={seed}&nologo=true"
        
        print(f"   [AI Art] Requesting image for: '{prompt}'...")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print(f"   [AI Art] Failed. Status Code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   [AI Art] Error downloading: {e}")
        return False

def generate_thumbnail(video_path, topic, session_id):
    print("3.75 Generating Thumbnail...")
    thumb_text = topic.upper()
    mode = config.VIDEO_MODE if hasattr(config, 'VIDEO_MODE') else "Shorts"
    
    # 1. Generate Catchy Title using Gemini
    for _ in range(3):
        try:
            client = get_client()
            resp = client.models.generate_content(
                model='gemini-2.0-flash', 
                contents=f"4-word shocking text for '{topic}'. Uppercase. No quotes."
            )
            thumb_text = resp.text.strip()
            break
        except: time.sleep(2)

    # --- SAVE TO TEMP FOLDER ---
    frame_path = os.path.join(TEMP_DIR, f"thumbnail_{session_id}.jpg")
    image_source = "video_frame" # Track source for debugging

    # 2. Try Generating AI Art Background
    try:
        if mode == "Shorts":
            w, h = 1080, 1920
        else:
            w, h = 1920, 1080
            
        success = download_ai_image(topic, frame_path, w, h)
        
        if success:
            image_source = "ai_generated"
            print("   [Thumbnail] Using AI-Generated Art.")
        else:
            raise Exception("AI Image Gen failed")

    except Exception as e:
        # 3. Fallback: Capture Frame from Video
        print(f"   [Thumbnail] Fallback to video frame due to: {e}")
        try:
            clip = VideoFileClip(video_path)
            clip.save_frame(frame_path, t=clip.duration * 0.3)
            clip.close()
            image_source = "video_frame"
        except:
            print("   [Thumbnail] Critical Error: Could not generate any thumbnail.")
            return None

    # 4. Add Text Overlay
    try:
        img = Image.open(frame_path)
        draw = ImageDraw.Draw(img)
        
        # Dynamic Font Logic
        if mode == "Shorts":
            font_size = int(img.width / 8)
        else:
            font_size = int(img.width / 10)
        
        # Attempt to load font
        try:
            font = ImageFont.truetype("arialbd.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", font_size)
            except:
                font = ImageFont.load_default()

        # Calculate Text Position (Center)
        try:
            left, top, right, bottom = draw.textbbox((0, 0), thumb_text, font=font)
            text_w = right - left
            text_h = bottom - top
        except:
            text_w = font_size * len(thumb_text) * 0.5
            text_h = font_size

        text_x = (img.width - text_w) / 2
        text_y = (img.height / 2) - text_h 

        stroke_width = 6
        
        # Draw Text with Stroke (Outline)
        for adj_x in range(-stroke_width, stroke_width+1):
            for adj_y in range(-stroke_width, stroke_width+1):
                 draw.text((text_x+adj_x, text_y+adj_y), thumb_text, font=font, fill="black")
        
        draw.text((text_x, text_y), thumb_text, font=font, fill="yellow")
        
        img.save(frame_path)
        print(f"   Thumbnail saved: {frame_path} (Source: {image_source})")
        return frame_path

    except Exception as e:
        print(f"   Error finishing thumbnail: {e}")
        return None