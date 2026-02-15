# test_bot_hindi.py (The Hindi Inspector)
import asyncio
import os
import config 
import generators     
import media_engine   
import studio

# --- CONFIG OVERRIDE (FORCE HINDI MODE) ---
config.VIDEO_MODE = "Shorts" 
session_id = "TEST_RUN_HINDI"

# 🛑 FORCE HINDI VOICE 🛑
# This ensures generators.py triggers the "+25% Speed" and "Sync Shift" logic
config.VOICE = "hi-IN-SwaraNeural"
config.VOICE_LIST = ["hi-IN-SwaraNeural"] 

def run_hindi_system_check():
    print(f"---------------------------------------------------")
    print(f" 🇮🇳  HINDI SYSTEM DIAGNOSTIC TOOL")
    print(f"---------------------------------------------------")

    # 1. MOCK TIMELINE (Hindi Text)
    print(" 1. Creating Hindi Test Timeline...")
    
    timeline = [
        # {
        #     "text": "Namaste doston...", 
        #     "visual": "digital data stream" 
        # },
        {
             "text": "Ab hum ek impossible AI image generate karenge.", 
             # ADD "AI:" HERE TO TEST THE NEW LOGIC
            "visual": "AI: gandhi riding a bicycle on mars" 
        }
    ]
    
    print(f"    [Status] Loaded {len(timeline)} test scenes.")

    # 2. GENERATE AUDIO (Tests EdgeTTS + Speed Tweak + Sync Offset)
    print("\n 2. Testing Audio Engine (Hindi Speed +25%)...")
    # We use asyncio.run to call the async generator function
    audio_files = asyncio.run(generators.generate_segmented_audio(timeline, session_id))
    
    if len(audio_files) != len(timeline):
        print("    [FAIL] Audio generation count mismatch!")
        return
    else:
        print("    [PASS] Audio generated successfully.")

    # 3. DOWNLOAD MEDIA (Tests Pexels + AI Fallback)
    print("\n 3. Testing Visual Engine...")
    video_files = generators.download_specific_scenes(timeline, session_id)
    
    if len(video_files) != len(timeline):
        print("    [FAIL] Video download count mismatch!")
        return
    else:
        print("    [PASS] Visuals acquired.")
        # Check if the last file is a JPG (proving AI worked)
        if video_files[-1].endswith(".jpg"):
             print("    [PASS] AI Image Generator triggered successfully!")
        else:
             print("    [WARN] AI Image Generator might not have triggered (Pexels found a match?).")

    # 4. EDIT VIDEO (Tests Subtitles, Fonts, Sync)
    print("\n 4. Testing Editor (Hindi Fonts & Sync)...")
    
    # Use generic background music
    music_data = ("Mystery", ["mystery", "dark"])
    
    final_video = media_engine.combine_scenes(timeline, video_files, audio_files, session_id, music_data)
    
    if final_video and os.path.exists(final_video):
        print(f"\n---------------------------------------------------")
        print(f" ✅ HINDI TEST PASSED!")
        print(f" 📁 Output: {final_video}")
        print(f"---------------------------------------------------")
        print(f" PLEASE WATCH THE VIDEO AND VERIFY:")
        print(f" 1. SPEED: Is the voice fast and energetic?")
        print(f" 2. SYNC: Do the subtitles appear EXACTLY when spoken?")
        print(f" 3. FONT: Are the Hindi characters (मात्रा) correct?")
        print(f" 4. AI ART: Is the second scene a glass Taj Mahal?")
        print(f"---------------------------------------------------")
        
        # Cleanup Option
        choice = input(" > Delete test files? (y/n): ")
        if choice.lower() == 'y':
            studio.manage_session_files(session_id, True)
            # Also clean up the output video if desired
            if os.path.exists(final_video):
                os.remove(final_video)
                print("    [Deleted] Output video removed.")
    else:
        print(f"\n ❌ TEST FAILED: Video could not be rendered.")

if __name__ == "__main__":
    run_hindi_system_check()