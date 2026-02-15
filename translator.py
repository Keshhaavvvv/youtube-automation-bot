import os
import json
import random
import re
import asyncio
import edge_tts
import config
from groq import Groq

# --- CONFIGURATION ---
TEMP_DIR = "temp"
if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)

# --- GROQ CLIENT ---
def get_groq_client():
    try:
        api_key = config.GROQ_API_KEYS[0] if hasattr(config, 'GROQ_API_KEYS') else config.GROQ_API_KEY
        return Groq(api_key=api_key)
    except:
        print("   [Error] Groq API Key missing in config.")
        return None

# --- HELPER: ROBUST JSON EXTRACTION ---
def extract_json_from_text(text):
    """Cleans AI output to find the valid JSON object."""
    try:
        # Try finding the first '{' and last '}'
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != -1:
            json_str = text[start:end]
            return json.loads(json_str)
        return json.loads(text) # Try direct parse
    except:
        return None

# --- TRANSLATION ENGINE (BATCH) ---
def translate_batch_to_hinglish(sentences):
    """Adapts English sentences into natural, conversational Hinglish (Batch Mode)."""
    client = get_groq_client()
    if not client: return None

    formatted_input = "\n".join([f"{i+1}. {s}" for i, s in enumerate(sentences)])
    
    system_prompt = (
        "You are India's #1 Viral YouTube Storyteller (like Dhruv Rathee or fierce campfire narrators).\n"
        "TASK: Adapt the provided English script into 'VIRAL URBAN HINGLISH'.\n"
        "Your goal is RETENTION. The audio must sound natural, punchy, and Indian.\n\n"
        "STRICT LINGUISTIC RULES:\n"
        "1. **NO 'Shuddh' (Pure) Hindi:** Don't say 'Vigyaan' or 'Takneek'. Say 'Science' and 'Tech'.\n"
        "2. **The 70/30 Rule:** Use Hindi for grammar/emotions (70%) and English for keywords/impact (30%).\n"
        "   - BAD: 'Yeh bohot rahasyamayi durghatna thi.' (Boring/Bookish)\n"
        "   - GOOD: 'Yeh accident... kaafi mysterious thi!' (Viral Style)\n"
        "3. **Conversational Fillers:** Use natural Indian fillers to bridge gaps:\n"
        "   - 'Arre bhai,', 'Socho ek baar...', 'Lekin wait...', 'Asal mein,', 'Kya aapko pata hai?'\n"
        "4. **Emotion First:** If the scene is scary, use shorter, darker sentences. If exciting, speed it up.\n"
        "5. **Technical Terms:** NEVER translate: AI, Internet, Algorithm, Space, Dark Web, Hack, Money.\n\n"
        "OUTPUT FORMAT (STRICT JSON):\n"
        "Return a JSON Object with a 'translations' list. Each item must have:\n"
        " - 'roman': The text written in English alphabets (Phonetic) for TTS reading.\n"
        " - 'devanagari': The text written in Hindi script for Subtitles.\n"
        "Example:\n"
        "{ \"translations\": [ {\"roman\": \"Bas ek galti... aur sab khatam.\", \"devanagari\": \"बस एक गलती... और सब ख़त्म।\"} ] }"
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Adapt these {len(sentences)} lines to Hinglish JSON:\n{formatted_input}"}
            ],
            temperature=0.7,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        content = completion.choices[0].message.content
        data = extract_json_from_text(content)
        
        if data and "translations" in data:
            return data["translations"]
        return None
        
    except Exception as e:
        print(f"   [Batch Translator Error] {e}")
        return None

# --- TRANSLATION ENGINE (SINGLE LINE BACKUP) ---
def translate_single_line(text):
    """Backup: Translates one line at a time if batch fails."""
    client = get_groq_client()
    if not client: return {"roman": text, "devanagari": text}

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Translate to Dramatic Hinglish. Return JSON: {\"roman\": \"...\", \"devanagari\": \"...\"}"},
                {"role": "user", "content": f"Translate: {text}"}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        data = extract_json_from_text(completion.choices[0].message.content)
        return data if data else {"roman": text, "devanagari": text}
    except:
        return {"roman": text, "devanagari": text}

# --- TIMELINE CONVERTER (SMART HYBRID MODE) ---
def create_hindi_timeline(english_timeline):
    print("   [Translator] Converting Script to Hinglish...")
    
    english_texts = [scene['text'] for scene in english_timeline]
    total_scenes = len(english_timeline)
    
    # 1. TRY BATCH TRANSLATION (Fast Start)
    print("   [Translator] Attempting Batch Translation...")
    translations = translate_batch_to_hinglish(english_texts)
    
    batch_count = len(translations) if translations else 0
    print(f"   [Translator] Batch returned {batch_count}/{total_scenes} scenes.")

    hindi_timeline = []
    
    # 2. PROCESS SCENES (Hybrid Loop)
    for i in range(total_scenes):
        scene = english_timeline[i]
        new_scene = scene.copy()
        
        if i < batch_count:
            # METHOD A: Use Fast Batch Data
            trans = translations[i]
            new_scene['text'] = trans.get('roman', scene['text']) 
            new_scene['audio_text'] = trans.get('devanagari', scene['text'])
        else:
            # METHOD B: Fill Gaps with Line-by-Line (Slow but Complete)
            print(f"     > Filling gap for scene {i+1}/{total_scenes}...")
            trans = translate_single_line(scene['text'])
            new_scene['text'] = trans.get('roman', scene['text'])
            new_scene['audio_text'] = trans.get('devanagari', scene['text'])
            
        hindi_timeline.append(new_scene)

    print(f"   [Translator] Successfully converted {len(hindi_timeline)}/{total_scenes} scenes.")
    return hindi_timeline

# --- HINDI AUDIO ENGINE (WITH ELASTIC SYNC) ---
async def generate_hindi_audio(timeline, session_id):
    print(f"   [Translator] Generating Hindi Audio (Swara/Madhur)...")
    
    # Randomly pick a male or female voice
    voice = random.choice(["hi-IN-SwaraNeural", "hi-IN-MadhurNeural"])
    print(f"   [Translator] Voice Selected: {voice}")
    
    audio_files = []
    
    # Import locally to avoid circular dependencies
    from moviepy.editor import AudioFileClip
    
    for i, scene in enumerate(timeline):
        # Use Devanagari text for audio generation
        text_to_speak = scene.get('audio_text', scene['text'])
        # Cleanup special characters
        text_to_speak = re.sub(r'[#*]', '', text_to_speak).strip()
        
        fname = os.path.join(TEMP_DIR, f"hindi_audio_{i}_{session_id}.mp3")
        tname = os.path.join(TEMP_DIR, f"hindi_timing_{i}_{session_id}.json")
        
        try:
            # Generate Audio
            communicate = edge_tts.Communicate(text_to_speak, voice, rate="+30%")
            word_timings = []
            
            with open(fname, "wb") as file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        file.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        start = chunk["offset"] / 10000000
                        dur = chunk["duration"] / 10000000
                        word_timings.append({"word": chunk["text"], "start": start, "end": start + dur})
                        
            # --- ELASTIC SYNC FIX (Prevents Hindi Drift) ---
            if os.path.exists(fname) and word_timings:
                try:
                    # 1. Measure ACTUAL audio file duration
                    audioclip = AudioFileClip(fname)
                    real_duration = audioclip.duration
                    audioclip.close()
                    
                    # 2. Measure TIMESTAMP duration
                    last_timestamp_end = word_timings[-1]['end']
                    
                    # 3. Calculate Stretch Factor
                    if last_timestamp_end > 0:
                        stretch = real_duration / last_timestamp_end
                        
                        # 4. Stretch timings to match audio
                        for w in word_timings:
                            w['start'] = w['start'] * stretch
                            w['end'] = w['end'] * stretch
                            
                except Exception as e:
                    print(f"   [Sync Warning] Could not sync scene {i}: {e}")
            
            # Save corrected timing
            with open(tname, "w", encoding='utf-8') as f:
                json.dump(word_timings, f)
            
            if os.path.exists(fname):
                audio_files.append(fname)
                
        except Exception as e:
            print(f"   [Translator Error] Audio failed for scene {i}: {e}")
            # Fallback Silent Audio
            try:
                from moviepy.audio.AudioClip import AudioArrayClip
                import numpy as np
                silence = AudioArrayClip(np.zeros((44100 * 2, 2)), fps=44100)
                silence.write_audiofile(fname, logger=None)
                audio_files.append(fname)
            except: pass
            
    return audio_files