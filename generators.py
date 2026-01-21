# generators.py
import os
import time
import random
import asyncio
import requests
import json
import warnings
import re
import edge_tts
import config 
import sys
import threading

# --- IMPORT GROQ ---
try:
    from groq import Groq
except ImportError:
    print("\n[CRITICAL ERROR] You are missing the 'groq' library.")
    print("Please run: pip install groq")
    exit()

# --- SUPPRESS WARNINGS ---
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- TEMP FOLDER SETUP ---
TEMP_DIR = "temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# --- HELPER: CROSS-PLATFORM TIMED INPUT ---
def smart_input(prompt, timeout=60, default_value=None):
    """Waits for input for 'timeout' seconds. Returns default if no input."""
    print(prompt, end='', flush=True)
    
    result = [default_value]
    
    def get_input():
        try:
            result[0] = input()
        except: pass

    # Start input thread
    t = threading.Thread(target=get_input)
    t.daemon = True # Daemon kills thread when main program exits
    t.start()
    
    t.join(timeout)
    
    if t.is_alive():
        print(f"\n   [Auto-Pilot] No response. Defaulting to: {default_value}")
        return default_value
    
    # If user pressed Enter but typed nothing, use default
    if result[0] == "":
        return default_value
        
    return result[0]

# --- HELPERS ---
def clean_json_text(text):
    text = re.sub(r'```json', '', text)
    text = re.sub(r'```', '', text)
    if "{" in text:
        text = text[text.find("{"):text.rfind("}")+1]
    return text.strip()

def get_random_voice():
    if hasattr(config, 'VOICE_LIST') and config.VOICE_LIST:
        return random.choice(config.VOICE_LIST)
    return config.VOICE

# --- HISTORY READER ---
def get_past_topics():
    """Reads history.txt to find previously used topics."""
    history_path = config.HISTORY_FILE if hasattr(config, 'HISTORY_FILE') else "history.txt"
    if not os.path.exists(history_path):
        return []
    
    past_topics = []
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.split(" - ")
                if len(parts) >= 2:
                    past_topics.append(parts[1].strip())
    except: pass
    return past_topics

# --- GROQ ROTATION ENGINE ---
def groq_generate(prompt, json_mode=False):
    keys = config.GROQ_API_KEYS if hasattr(config, 'GROQ_API_KEYS') else [config.GROQ_API_KEY]
    
    models_to_try = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "llama3-70b-8192", 
        "mixtral-8x7b-32768"
    ]

    for i, key in enumerate(keys):
        client = Groq(api_key=key)
        
        for model in models_to_try:
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a professional YouTube Scriptwriter. Output strict JSON when asked."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=8000,
                    top_p=1,
                    stream=False,
                    response_format={"type": "json_object"} if json_mode else None
                )
                return completion.choices[0].message.content
                
            except Exception as e:
                continue 
            
    print("   [Groq Error] All Keys and Models failed.")
    return None

# --- SMART TOPIC SELECTOR (AUTO-PILOT) ---
def get_smart_topic(force_random=False):
    if force_random: return "Dark Psychology Facts"

    print("\n---------------------------------------------------")
    print(" TOPIC SELECTION (Auto-Default: Brainstorm in 60s)")
    print("---------------------------------------------------")
    print(" 1. Brainstorm Viral Niches (Dark/Psych/Tech)")
    print(" 2. Type my own topic")
    
    choice = smart_input(" > Enter choice (1 or 2): ", timeout=60, default_value="1").strip()
    
    if choice == "2":
        print("\n---------------------------------------------------")
        user_topic = input(" > Enter Topic Name: ").strip()
        print("---------------------------------------------------")
        return user_topic
    
    # --- BRAINSTORM MODE ---
    print("\n   [AI] Reading history to avoid repeats...")
    past_topics = get_past_topics()
    
    # --- UPDATED CATEGORIES FOR TIER 1 & 2 CONTENT ---
    print(f"   [AI] Brainstorming 10 high-retention ideas...")
    
    prompt = (
        f"Generate 20 highly viral, click-worthy YouTube video topics. "
        f"Strictly rotate between these 5 categories:\n"
        f"1. Dark Curiosities (Uncomfortable facts, disturbing history)\n"
        f"2. Psychology & Inner Monologue (Why we feel alone, deja vu, mental habits)\n"
        f"3. Existential Philosophy (Modern loneliness, the fear of being forgotten)\n"
        f"4. AI & Tech Consequences (Scary future predictions, no tutorials)\n"
        f"5. Internet Culture Analysis (The pressure of being seen, digital addiction)\n\n"
        f"Style: Titles should be mysterious and provoking (e.g., 'The sound that makes you panic', 'Why you replay conversations').\n"
        f"CRITICAL: Do NOT include these topics (already done): {past_topics}\n"
        f"Output format: JSON with a single key 'topics' containing a list of strings."
    )
    
    json_resp = groq_generate(prompt, json_mode=True)
    ideas = []
    
    if json_resp:
        try:
            data = json.loads(clean_json_text(json_resp))
            ideas = data.get("topics", [])
        except: pass
    
    if not ideas:
        print("   [Error] Could not generate ideas. Please type manually.")
        return input(" > Enter Topic Name: ").strip()
    
    print("\n---------------------------------------------------")
    print(" VIRAL IDEA GENERATOR (High Retention)")
    print("---------------------------------------------------")
    for i, idea in enumerate(ideas):
        print(f" {i+1}. {idea}")
    print(f" {len(ideas)+1}. [Type my own instead]")
    print("---------------------------------------------------")
    
    # Random default choice for automation
    random_choice = str(random.randint(1, len(ideas)))
    
    selection_input = smart_input(f" > Choose an option (1-{len(ideas)+1}) [Auto: {random_choice}]: ", timeout=60, default_value=random_choice).strip()
    
    try:
        selection = int(selection_input)
        if 1 <= selection <= len(ideas):
            selected_topic = ideas[selection-1]
            print(f"   [Selected] {selected_topic}")
            return selected_topic
        else:
            return input(" > Enter Topic Name: ").strip()
    except:
        return input(" > Enter Topic Name: ").strip()

# --- SCRIPT WRITER ---
def generate_viral_script(topic):
    mode = config.VIDEO_MODE if hasattr(config, 'VIDEO_MODE') else "Shorts"
    print(f"\n   [Groq AI] Writing {mode} script for '{topic}'...")
    
    if mode == "Shorts":
        # --- UPDATED SCRIPT PROMPT FOR TIER 1 & 2 STYLES ---
        prompt = (
            f"Write a viral YouTube Shorts script about '{topic}'.\n"
            f"Determine the best style from these options based on the topic:\n"
            f"1. DARK/CURIOSITY: Atmospheric, detached tone. 'This experiment broke human trust...'\n"
            f"2. PSYCHOLOGY: Second-person ('You'). Validating but haunting. 'Why you replay conversations...'\n"
            f"3. PHILOSOPHY: Deep, existential questions. 'If nobody remembers you...'\n"
            f"4. TECH: Fear-based/Impact-based. 'AI already decides this...'\n\n"
            f"Rules:\n"
            f"- NO introductory fluff ('Hello guys'). Start immediately with the hook.\n"
            f"- Short, punchy sentences. Let silence breathe.\n"
            f"- End with a lingering thought or loop.\n"
            f"- Length: 150-200 words max.\n"
            f"- Output ONLY the voiceover text. No scene headers."
        )
        return groq_generate(prompt)
    
    else:
        # Multi-Part Strategy for Long Form
        print("   [Groq AI] Using Multi-Part Strategy to ensure 10+ min length...")
        parts = [
            "Part 1: The Hook & The Uncomfortable Truth (Introduction)",
            "Part 2: The Deep Dive / The Psychological Mechanism (The Core)",
            "Part 3: The Future Consequences & Existential Conclusion (The Outro)"
        ]
        
        full_script = ""
        for part in parts:
            print(f"      -> Generating {part}...")
            prompt = (
                f"Write {part} of a deep-dive documentary script about '{topic}'.\n"
                f"Style: High-end documentary (Lemmino/Vsauce style). Intellectual, slightly dark, and captivating.\n"
                f"Length: Approx 700-800 words.\n"
                f"Constraint: Write ONLY the narrator's text. No scene directions. Do not repeat the intro if this is Part 2 or 3."
            )
            chunk = groq_generate(prompt)
            if chunk: full_script += chunk + "\n\n"
            else: print(f"      [Warning] {part} failed to generate.")
        
        if len(full_script.split()) < 500:
            print("   [Error] Generated script was too short.")
            return None
            
        print(f"   [Groq AI] Success! Total Script length: {len(full_script.split())} words.")
        return full_script

def get_user_or_ai_script(topic):
    print("---------------------------------------------------")
    print(" SCRIPT SOURCE")
    print("---------------------------------------------------")
    print(" 1. Write it for me (AI)")
    print(" 2. I will paste it manually")
    
    # Auto-select AI writing if no input
    choice = smart_input(" > Enter choice (1 or 2) [Auto: 1]: ", timeout=30, default_value="1").strip()
    
    if choice == "1":
        script = generate_viral_script(topic)
        if script: return script
        print("   [!] AI failed. Switching to manual input.")
        
    print("---------------------------------------------------")
    print(" PASTE YOUR SCRIPT BELOW (Plain text, no emojis)")
    print("---------------------------------------------------")
    script = input(" > ").strip()
    while len(script) < 20:
        print("   [!] Script too short. Please paste the full script.")
        script = input(" > ").strip()
    return script

# --- SCENE GENERATOR ---
def extract_visual_keyword(sentence):
    clean = re.sub(r'[^\w\s]', '', sentence.lower())
    words = clean.split()
    stopwords = ["the", "is", "are", "was", "to", "of", "and", "a", "in", "that", "it", "for"]
    meaningful_words = [w for w in words if w not in stopwords and len(w) > 3]
    if not meaningful_words: return "abstract cinematic background"
    return meaningful_words[0]

def fallback_scene_generation(topic, script):
    print("   [Fallback] Generating scenes manually...")
    mode = config.VIDEO_MODE if hasattr(config, 'VIDEO_MODE') else "Shorts"
    max_scenes = config.VIDEO_SETTINGS[mode]["max_scenes"]
    
    sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', script) if len(s) > 5]
    is_long = len(script.split()) > 500
    group_size = 4 if is_long else 1
    
    timeline = []
    temp_text = ""
    count = 0
    
    for s in sentences:
        if is_long:
            if count < group_size:
                temp_text += s + " "
                count += 1
                continue
            else:
                s = temp_text + s
                temp_text = ""
                count = 0
        
        visual = extract_visual_keyword(s)
        timeline.append({'text': s.strip(), 'visual': visual})
        if len(timeline) >= max_scenes: break
        
    return timeline

def generate_scene_data(topic):
    final_script = get_user_or_ai_script(topic)
    print(f"\n2. Analying Script & Generating Visuals...")
    
    mode = config.VIDEO_MODE if hasattr(config, 'VIDEO_MODE') else "Shorts"
    settings = config.VIDEO_SETTINGS[mode]
    
    # --- UPDATED VISUAL PROMPT FOR ABSTRACT/STOCK FRIENDLINESS ---
    prompt = (
        f"You are a video editor. I have a script about '{topic}'.\n"
        f"SCRIPT: \"{final_script[:15000]}\"...\n\n" 
        f"Task: Break this script into a JSON timeline. Max {settings['max_scenes']} scenes.\n"
        f"Style: Cinematic, Abstract, Stock-Footage Friendly.\n"
        f"CRITICAL INSTRUCTION: For psychological, emotional, philosophical, or existential lines, "
f"you MUST use ATMOSPHERIC, SYMBOLIC, or ABSTRACT visuals instead of literal physical actions. "
f"These visuals should evoke mood, inner tension, memory, isolation, time, identity, or cognition. "
f"Examples include but are not limited to: "
f"'ticking clock', 'melting clock', 'broken stopwatch', 'hourglass leaking sand', "
f"'rain-streaked window', 'fogged glass', 'condensation on glass', 'water droplets crawling downward', "
f"'empty train platform at night', 'abandoned bus stop', 'lonely streetlight flickering', "
f"'crowd moving in slow motion', 'faces blurred in a crowd', 'crowd with hollow eyes', "
f"'dark silhouette against neon lights', 'faceless figure', 'shadow stretching unnaturally long', "
f"'reflection that moves out of sync', 'distorted mirror reflection', 'cracked mirror', "
f"'galaxy spiraling inward', 'collapsing star', 'black hole swallowing light', 'nebula breathing slowly', "
f"'neural network pulsing', 'glowing synapses misfiring', 'wires tangled like veins', "
f"'static-filled television', 'signal interference', 'glitching screen', 'flickering fluorescent light', "
f"'slowly rotating ceiling fan', 'fan casting moving shadows', "
f"'dust floating in a sunbeam', 'ash drifting through air', "
f"'door slightly ajar', 'hallway stretching endlessly', 'stairs descending into darkness', "
f"'heartbeat visualized as ripples', 'EKG line flatlining then returning', "
f"'waves crashing in darkness', 'ocean seen from above at night', "
f"'birds frozen mid-air', 'leaves falling upward', "
f"'empty room humming', 'room breathing subtly', "
f"'city lights blinking like neurons', 'traffic seen as glowing veins', "
f"'eclipse covering the sun', 'sun flickering like a dying bulb', "
f"'rain falling upward', 'snow in slow motion', "
f"'time-lapse of decaying fruit', 'flower wilting in reverse', "
f"'paper burning in reverse', 'ink bleeding through paper', "
f"'candle flame trembling', 'candle extinguishing itself', "
f"'clock hands spinning uncontrollably', 'clock frozen at one moment', "
f"'blurred memories layered over the present', 'ghosted double exposure faces', "
f"'fog swallowing a figure', 'figure dissolving into smoke', "
f"'subway tunnel rushing endlessly', 'train lights vanishing into darkness'. "
f"AVOID literal depictions such as walking, talking, fighting, touching, or explicit physical gestures. "
f"PRIORITIZE metaphor, mood, symbolism, and internal states rendered visually.\n"
f"Output JSON Format:\n"
        f"Output JSON Format:\n"
        f"{{ \"title\": \"Viral Title\", \"tags\": [\"tag1\", \"tag2\"], "
        f"\"timeline\": [ {{ \"text\": \"sentence from script\", \"visual\": \"2-word visual search term\" }} ] }}"
    )

    json_response = groq_generate(prompt, json_mode=True)
    
    if json_response:
        try:
            data = json.loads(clean_json_text(json_response))
            timeline = data.get("timeline", [])
            if timeline:
                print(f"   [Success] Groq generated {len(timeline)} scenes.")
                return topic, timeline, data.get('tags', [])
        except:
            print("   [Error] JSON parsing failed.")
            
    print("   [Groq Failure] Switching to Manual Mode.")
    timeline = fallback_scene_generation(topic, final_script)
    return topic, timeline, ['viral', topic]

# --- AUDIO ENGINE ---
async def generate_segmented_audio(timeline, session_id):
    print(f"2.5 Generating Audio & Timing for {len(timeline)} scenes...")
    selected_voice = get_random_voice()
    audio_files = []
    
    for i, scene in enumerate(timeline):
        text = scene['text']
        # CLEAN TEXT to fix "Metadata Empty" error
        clean_text = re.sub(r'[#*]', '', text).strip()
        
        # --- SAVE TO TEMP FOLDER ---
        filename = os.path.join(TEMP_DIR, f"audio_{i}_{session_id}.mp3")
        timing_filename = os.path.join(TEMP_DIR, f"timing_{i}_{session_id}.json")
        
        # --- SPEED: +10% ---
        rate = "+10%" 
        
        communicate = edge_tts.Communicate(clean_text, selected_voice, rate=rate)
        word_timings = []
        
        try:
            with open(filename, "wb") as file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        file.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        start_time = chunk["offset"] / 10_000_000
                        duration = chunk["duration"] / 10_000_000
                        word_timings.append({
                            "word": chunk["text"],
                            "start": start_time,
                            "end": start_time + duration
                        })
            
            with open(timing_filename, "w", encoding='utf-8') as f:
                json.dump(word_timings, f)
            
            if os.path.exists(filename):
                audio_files.append(filename)
                print(f"   [Audio] Segment {i+1} ready.")
        except Exception as e:
            print(f"   [Error] Audio gen failed for segment {i}: {e}")
        
    return audio_files

def download_specific_scenes(timeline, session_id):
    print(f"3. Downloading Media for Scenes...")
    mode = config.VIDEO_MODE if hasattr(config, 'VIDEO_MODE') else "Shorts"
    orientation = config.VIDEO_SETTINGS[mode]["orientation"]
    
    video_files = []
    headers = {'Authorization': config.PEXELS_API_KEY}
    
    print(f"   [System] Downloading {orientation.upper()} clips for {mode} mode.")
    
    for i, scene in enumerate(timeline):
        query = scene['visual']
        print(f"   [Scene {i+1}] Searching for: '{query}'...")
        
        # --- SAVE TO TEMP FOLDER ---
        filename = os.path.join(TEMP_DIR, f"clip_{i}_{session_id}.mp4")
        found = False
        
        try:
            url = f"https://api.pexels.com/videos/search?query={query}&per_page=15&orientation={orientation}"
            resp = requests.get(url, headers=headers).json()
            
            # --- STRICT ASPECT RATIO FILTER ---
            valid = []
            for v in resp.get('videos', []):
                if v['duration'] < 4: continue
                
                # Check dimensions against mode
                w, h = v['width'], v['height']
                if mode == "Shorts" and w > h: continue # Skip landscape for shorts
                if mode == "Long" and h > w: continue   # Skip portrait for long
                
                valid.append(v)

            if valid:
                video = random.choice(valid[:3]) if len(valid) >= 3 else valid[0]
                link = video['video_files'][0]['link']
                with requests.get(link, stream=True) as r:
                    with open(filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
                video_files.append(filename)
                found = True
        except: pass
        
        if not found and hasattr(config, 'PIXABAY_API_KEY'):
            try:
                pixabay_orient = "vertical" if orientation == "portrait" else "horizontal"
                url = f"https://pixabay.com/api/videos/?key={config.PIXABAY_API_KEY}&q={query}&video_type=film&orientation={pixabay_orient}"
                resp = requests.get(url).json()
                valid = [v for v in resp.get('hits', []) if v['duration'] >= 4]
                if valid:
                    link = random.choice(valid[:3])['videos']['medium']['url']
                    with requests.get(link, stream=True) as r:
                        with open(filename, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
                    video_files.append(filename)
                    found = True
            except: pass
            
        if not found:
            print("      -> Video failed. Using Image.")
            # --- SAVE IMAGE TO TEMP FOLDER ---
            filename = os.path.join(TEMP_DIR, f"clip_{i}_{session_id}.jpg")
            try:
                url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"
                resp = requests.get(url, headers=headers).json()
                if resp.get('photos'):
                    key = 'portrait' if orientation == 'portrait' else 'landscape'
                    link = resp['photos'][0]['src'][key]
                    with requests.get(link, stream=True) as r:
                        with open(filename, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
                    video_files.append(filename)
            except: pass
            
        time.sleep(1)

    return video_files