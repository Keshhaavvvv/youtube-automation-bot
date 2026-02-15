# test_bot.py (The Inspector)
import asyncio
import os
import random
import sys

# --- IMPORT YOUR TEAMS ---
import generators    
import media_engine  
import config        
import studio

# --- CONFIG OVERRIDE (FORCE FAST MODE) ---
config.VIDEO_MODE = "Shorts" # Renders faster
session_id = "TEST_RUN"

def run_system_check():
    print(f"---------------------------------------------------")
    print(f" 🛠️  SYSTEM DIAGNOSTIC TOOL (Fast Check)")
    print(f"---------------------------------------------------")

    # 1. MOCK TIMELINE (Hardcoded to test specific features)
    print(" 1. Creating Test Timeline...")
    
    timeline = [
        {
            "text": "This is a system check. We are testing the digital sync.", 
            "visual": "matrix code" 
            # TEST: 'digital' should be CYAN. 'matrix code' gets a video.
        },
        {
            # FIX: Added [AI] tag here to force image generation
            "text": "Finally, generating an impossible AI image now.", 
            "visual": "[AI] gandhi riding a bicycle on mars"
            # TEST: This MUST fail Pexels and trigger Pollinations AI Image.
        }
    ]
    
    print(f"    [Status] Loaded {len(timeline)} test scenes.")

    # 2. GENERATE AUDIO (Tests EdgeTTS + Sync)
    print("\n 2. Testing Audio Engine...")
    audio_files = asyncio.run(generators.generate_segmented_audio(timeline, session_id))
    
    if len(audio_files) != len(timeline):
        print("    [FAIL] Audio generation count mismatch!")
        return
    else:
        print("    [PASS] Audio generated successfully.")

    # 3. DOWNLOAD MEDIA (Tests Pexels + AI Fallback)
    print("\n 3. Testing Visual Engine (Video + AI Art)...")
    video_files = generators.download_specific_scenes(timeline, session_id)
    
    if len(video_files) != len(timeline):
        print("    [FAIL] Video download count mismatch!")
        return
    else:
        print("    [PASS] Visuals acquired.")
        # Check if the last file is a PNG/JPG (proving AI worked)
        if video_files[-1].lower().endswith((".jpg", ".png", ".jpeg")):
             print("    [PASS] AI Image Generator triggered successfully!")
        else:
             print("    [WARN] AI Image Generator might not have triggered.")

    # 4. EDIT VIDEO (Tests Subtitles, Colors, SFX, Sync)
    print("\n 4. Testing Editor (Subtitles, SFX, Sync)...")
    
    # Force 'Thrilling' music for the test
    music_data = ("Thrilling", ["thrill", "dark"])
    
    final_video = media_engine.combine_scenes(timeline, video_files, audio_files, session_id, music_data)
    
    if final_video and os.path.exists(final_video):
        print(f"\n---------------------------------------------------")
        print(f" ✅ TEST PASSED!")
        print(f" 📁 Output: {final_video}")
        print(f"---------------------------------------------------")
        print(f" PLEASE WATCH THE VIDEO AND VERIFY:")
        print(f" 1. Is 'DIGITAL' Cyan? Is 'WARNING' Red? Is 'MONEY' Green?")
        print(f" 2. Did the bell/type sound play on 'computer'?")
        print(f" 3. Is the LAST scene a static AI image?")
        print(f" 4. Is the lip-sync perfect?")
        print(f"---------------------------------------------------")
        
        # Cleanup
        choice = input(" > Delete test files? (y/n): ")
        if choice.lower() == 'y':
            studio.manage_session_files(session_id, True)
    else:
        print(f"\n ❌ TEST FAILED: Video could not be rendered.")

if __name__ == "__main__":
    run_system_check()