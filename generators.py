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
import xml.etree.ElementTree as ET
import urllib.parse 
import math


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

# --- IMPROVED TREND FETCHER (Business + Tech + General) ---
def fetch_google_trends():
    """Fetches a mix of Business, Tech, and General trends to find 'Internet' worthy topics."""
    print("   [System] Scanning the Internet for viral topics...")
    
    # We fetch 3 different RSS feeds to get a good mix (Money, Tech, General)
    # topic=b (Business/Finance), topic=tc (Technology), topic=h (Top Stories)
    urls = [
        "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en", # Tech/Internet
        "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",   # Finance/Gold
        "https://news.google.com/rss?topic=h&hl=en-US&gl=US&ceid=US:en"                               # General Viral
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    all_trends = []
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                # Grab top 5 from each category
                count = 0
                for item in root.findall('.//item'):
                    title = item.find('title').text
                    # Cleanup: Remove source name (e.g., " - CNN")
                    if "-" in title: title = title.rsplit("-", 1)[0].strip()
                    all_trends.append(title)
                    count += 1
                    if count >= 5: break
        except: continue

    # Shuffle to mix business, tech, and general news
    if all_trends:
        random.shuffle(all_trends)
        # Remove duplicates
        return list(set(all_trends))
    
    print("   [Error] Could not fetch news sources.")
    return None

# --- SMART TOPIC SELECTOR (5 Options) ---
# --- HELPER: READ HISTORY ---
def get_past_topics():
    """Reads the history file to create an exclusion list."""
    # Checks config for file path, defaults to history.txt
    try:
        import config
        history_path = getattr(config, 'HISTORY_FILE', 'history.txt')
    except: 
        history_path = 'history.txt'

    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                # Return non-empty lines
                return [line.strip() for line in f.readlines() if len(line.strip()) > 5]
        except: pass
    return []

# --- HELPER: FETCH REAL TRENDS (RSS) ---
# def fetch_google_trends():
#     """Fetches real-time trends from Google RSS without external libs."""
#     try:
#         # US Daily Trends RSS
#         url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
#         response = requests.get(url, timeout=10)
#         if response.status_code == 200:
#             root = ET.fromstring(response.content)
#             # Parse XML
#             items = []
#             for item in root.findall(".//item"):
#                 title = item.find("title").text
#                 news_items = item.findall(".//ht:news_item_title", namespaces={'ht': 'https://trends.google.com/trends/trendingsearches/daily'})
#                 for news in news_items:
#                     items.append(f"{title}: {news.text}")
#             return items[:15] # Return top 15
#     except Exception as e:
#         print(f"   [Trends Error] {e}")
#     return []

# # --- HELPER: INTERNAL AI GENERATOR ---
# def groq_generate_internal(prompt, json_mode=False):
#     """Wrapper for Groq API calls."""
#     client = get_groq_client()
#     if not client: return None
    
#     try:
#         completion = client.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.7,
#             response_format={"type": "json_object"} if json_mode else None
#         )
#         return completion.choices[0].message.content
#     except Exception as e:
#         print(f"   [AI Error] {e}")
#         return None
# # --- HELPER: GET GROQ CLIENT ---
# def get_groq_client():
#     """Initializes and returns the Groq client using config keys."""
#     try:
#         # Check for list of keys or single key
#         api_key = None
#         if hasattr(config, 'GROQ_API_KEYS') and config.GROQ_API_KEYS:
#             api_key = config.GROQ_API_KEYS[0]
#         elif hasattr(config, 'GROQ_API_KEY'):
#             api_key = config.GROQ_API_KEY
            
#         if not api_key:
#             print("   [Error] No Groq API Key found in config.py")
#             return None
            
#         return Groq(api_key=api_key)
#     except Exception as e:
#         print(f"   [Error] Could not initialize Groq: {e}")
#         return None

# --- MAIN FUNCTION: GET SMART TOPIC ---
def get_smart_topic(force_random=False):
    if force_random: return "Dark Psychology Facts"
    
    print("\n---------------------------------------------------")
    print(" TOPIC SELECTION")
    print("---------------------------------------------------")
    print(" 1. 🌍 Real-Time Viral Events (News, Finance, Tech)")
    print(" 2. 🧠 AI Brainstorm (Deep, Psychological, Analytical)")
    print(" 3. ✍️ Type my own topic")
    
    choice = smart_input(" > Enter choice (1-3) [Auto: 1]: ", timeout=60, default_value="1").strip()
    
    # OPTION 3: MANUAL
    if choice == "3":
        print("\n---------------------------------------------------")
        return input(" > Enter Topic Name: ").strip()
    
    # OPTION 1: REAL TRENDS (Your Old Working Logic)
    if choice == "1":
        raw_trends = fetch_google_trends()
        if raw_trends:
            print(f"   [System] Found {len(raw_trends)} raw headlines. Filtering for 'Viral Potential'...")
            
            prompt = (
                f"You are a Viral Content Strategist for a high-growth YouTube channel. "
                f"Here is a list of raw real-time news headlines: {raw_trends}\n\n"
                
                f"TASK: Filter this list and extract the top 10 topics with the highest 'Viral Potential'.\n"
                f"Then, rewrite them into clickbait-style hooks that provoke curiosity, fear, or excitement.\n\n"
                
                f"SELECTION RULES:\n"
                f"1. ❌ IGNORE: Local politics, weather, minor sports scores, routine corporate earnings, and boring press releases.\n"
                f"2. ✅ PRIORITIZE: catastrophic financial news (Crypto/Stock crashes), major AI breakthroughs, Tech CEO drama (Musk/Zuck), Global Mysteries, or 'The End of' something popular.\n\n"
                
                f"REWRITING RULES (Make them CLICKABLE):\n"
                f"- Use 'The Curiosity Gap': Don't give away the answer, make them ask 'Why?'.\n"
                f"- Use Strong Verbs: Destroyed, Exposed, Finally, Secret, Warning.\n"
                f"- Format: Short, punchy hooks (under 8 words).\n"
                f"- EXAMPLES of good outputs:\n"
                f"  * 'Why Bitcoin Just Crashed to Zero'\n"
                f"  * 'The Dark Truth About AI Video'\n"
                f"  * 'Apple is Finally Killing the iPhone'\n"
                f"  * 'Do Not Update Your PC Until You Watch This'\n\n"
                
                f"OUTPUT JSON FORMAT: {{ \"topics\": [\"Hook 1\", \"Hook 2\", \"Hook 3\", \"Hook 4\", \"Hook 5\"] }}"
            )
            
            # Use internal wrapper if defined, otherwise standard
            try:
                json_resp = groq_generate_internal(prompt, json_mode=True)
            except:
                json_resp = groq_generate(prompt, json_mode=True)
            
            if json_resp:
                try:
                    # Handle cleanup if function exists, else raw
                    try: 
                        clean_text = clean_json_text(json_resp)
                    except: 
                        clean_text = json_resp

                    data = json.loads(clean_text)
                    trends_ideas = data.get("topics", [])
                    
                    if trends_ideas:
                        print("\n   ---------------------------------------------------")
                        print("   🔥 TRENDING NOW (Select the best one)")
                        print("   ---------------------------------------------------")
                        for i, idea in enumerate(trends_ideas):
                            print(f"   {i+1}. {idea}")
                        print("   ---------------------------------------------------")
                        
                        selection = smart_input(f"   > Select topic (1-{len(trends_ideas)}) [Auto: 1]: ", timeout=45, default_value="1").strip()
                        try:
                            idx = int(selection) - 1
                            if 0 <= idx < len(trends_ideas): return trends_ideas[idx]
                        except: return trends_ideas[0]
                except: pass
            print("   [Error] AI filtering failed. Using raw top trend.")
            return raw_trends[0]
        else:
            print("   [System] Internet unreachble. Falling back to Brainstorm.")

    # OPTION 2: BRAINSTORM (Updated with Exclusion Logic)
    print("\n   [AI] Analyzing history to generate UNIQUE Deep Dive ideas...")
    
    # 1. Get History to prevent repeats
    past_topics = get_past_topics()
    # Limit history to last 50 to save tokens, join into a string
    history_context = ", ".join(past_topics[-50:]) if past_topics else "None"

    # 2. Advanced Prompt with "Exclusion List"
    prompt = (
        f"Generate 10 HIGH-RETENTION YouTube Short topics.\n"
        f"THEME: Deep Psychology, Modern Paradoxes, Dark Tech, Analytical History, Existential Questions.\n"
        f"TONE: Intellectual, Melancholic, Revealing, 'The Truth About...'\n\n"
        f"REFERENCE EXAMPLES (Do similar style):\n"
        f"- 'Why do we feel empty after good news?'\n"
        f"- 'The science behind A4 size paper'\n"
        f"- 'Modern jets vs WW1 jets'\n"
        f"- 'The pain of becoming yourself'\n"
        f"- 'Why algorithms know us better than friends?'\n"
        f"- 'Nothing about Mariana trench is normal'\n\n"
        
        f"⛔ CRITICAL EXCLUSION LIST (DO NOT REPEAT THESE):\n"
        f"[{history_context}]\n\n"
        
        f"Output strictly JSON: {{ \"topics\": [\"Topic 1\", \"Topic 2\", \"Topic 3\", \"Topic 4\", \"Topic 5\"] }}"
    )

    try:
        json_resp = groq_generate_internal(prompt, json_mode=True)
    except:
        json_resp = groq_generate(prompt, json_mode=True)
    
    ideas = []
    if json_resp:
        try:
            try: 
                clean_text = clean_json_text(json_resp)
            except: 
                clean_text = json_resp
            data = json.loads(clean_text)
            ideas = data.get("topics", [])
        except: pass
    
    if not ideas: return input(" > Enter Topic Name: ").strip()
    
    print("\n---------------------------------------------------")
    for i, idea in enumerate(ideas): print(f" {i+1}. {idea}")
    print("---------------------------------------------------")
    
    selection_input = smart_input(f" > Choose an option (1-{len(ideas)}) [Auto: 1]: ", timeout=60, default_value="1").strip()
    try:
        selection = int(selection_input)
        if 1 <= selection <= len(ideas): return ideas[selection-1]
    except: return ideas[0]

# --- GROQ ROTATION ENGINE ---
def groq_generate(prompt, json_mode=False):
    keys = config.GROQ_API_KEYS if hasattr(config, 'GROQ_API_KEYS') else [config.GROQ_API_KEY]
    models_to_try = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama3-70b-8192", "mixtral-8x7b-32768"]

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
# --- SCRIPT WRITER (FIXED: Handles JSON wrapping automatically) ---
def generate_viral_script(topic):
    mode = config.VIDEO_MODE if hasattr(config, 'VIDEO_MODE') else "Shorts"
    print(f"\n   [Groq AI] Writing {mode} script for '{topic}'...")
    
    if mode == "Shorts":
        prompt = (f"Write a viral YouTube Shorts script about '{topic}'.\n"
                  f"Style: Dark, Psychological, Fast-paced. No fluff.\n"
                  f"Length: 110-120 words. Output ONLY voiceover text.\n\n"
                  
                  f"CRITICAL RULES FOR THE PERFECT LOOP:\n"
                  f"1. [THE HOOK]: Start with a mind-blowing fact/question. (e.g., 'You've been lying to yourself.')\n"
                  f"2. [THE BODY]: Fast facts, 'But wait', 'Here's the twist'.\n"
                  f"3. [THE LOOP CONNECTOR]: The END of the script must flow naturally back into the START.\n"
                  f"   - BAD ENDING: 'Subscribe for more.'\n"
                  f"   - BAD ENDING: Repeating the Hook word-for-word.\n"
                  f"   - PERFECT ENDING: Ends with a connector phrase like '...and that is exactly why...'\n"
                  f"     (This leads perfectly back to the start: 'You've been lying to yourself.')\n\n"
                  
                  f"CONSTRAINT: Do NOT write the Hook again at the end. Just write the connector sentence that leads to it.\n"
                  f"Do NOT wrap it in JSON. Do NOT add 'Here is the script'. Just the spoken text.")
        
        raw_script = groq_generate(prompt)
        
        # --- CLEANING & LOOP SAFETY NET ---
        if raw_script:
            # 1. Clean basic junk
            raw_script = raw_script.strip().strip('"').strip("'")
            if ":" in raw_script[:20]: # Remove "Narrator:" prefixes
                raw_script = raw_script.split(":", 1)[1].strip()
            
            # 2. JSON Fallback (just in case)
            if "{" in raw_script and "}" in raw_script:
                try:
                    cleaned = clean_json_text(raw_script)
                    data = json.loads(cleaned)
                    raw_script = list(data.values())[0]
                except: pass

            # 3. SAFETY NET: Check for Double Hook
            # If the AI ignored us and repeated the first sentence at the end, cut it off.
            sentences = raw_script.split('.')
            sentences = [s.strip() for s in sentences if len(s.strip()) > 5] # Filter empty/short
            
            if len(sentences) > 2:
                first_sentence = sentences[0].lower()
                last_sentence = sentences[-1].lower()
                
                # Fuzzy match: if last sentence contains >50% of first sentence
                # or if it starts with the same 5 words
                first_words = " ".join(first_sentence.split()[:5])
                
                if first_words in last_sentence or first_sentence in last_sentence:
                    print("   [Script Fix] AI repeated the hook at the end. Removing it for seamless loop.")
                    # Rebuild script without the last sentence
                    # We have to be careful not to delete punctuation, so we look for the last occurrence
                    last_dot_index = raw_script.rfind('.')
                    if last_dot_index != -1:
                        # Find the second to last dot to cut off the final sentence
                        second_last_dot = raw_script.rfind('.', 0, last_dot_index)
                        if second_last_dot != -1:
                            raw_script = raw_script[:second_last_dot+1] # Keep the dot
                            
        return raw_script

    else:
        # --- UPGRADED LONG FORM LOGIC ---
        print("   [Groq AI] Using Multi-Part Strategy for High-End Documentary...")
        
        # We define a specific "Vibe" for the whole documentary
        style_guide = (
            "TONE: High-end investigative journalism (like Lemmino/Vsauce/Veritasium). "
            "Intellectual, slightly melancholic, and deeply analytical. "
            "Avoid generic YouTube intros like 'Welcome back'. Start cold. "
            "Use rhetorical questions and existential philosophy."
        )

        parts = [
            {
                "name": "Part 1: The Cold Open & The Hook",
                "prompt": (f"{style_guide}\n\n"
                           f"TASK: Write Part 1 of a documentary about '{topic}'.\n"
                           f"Structure:\n"
                           f"1. A cold open that sets a mysterious or disturbing scene.\n"
                           f"2. Introduce the central paradox or question.\n"
                           f"3. End this part with a cliffhanger transition.\n"
                           f"Length: 400 words.")
            },
            {
                "name": "Part 2: The Deep Dive & Psychology",
                "prompt": (f"{style_guide}\n\n"
                           f"TASK: Write Part 2 (The Meat) about '{topic}'.\n"
                           f"Structure:\n"
                           f"1. Analyze the psychology/science behind the topic.\n"
                           f"2. Provide specific examples, studies, or historical cases.\n"
                           f"3. Focus on the 'Why' - why does this happen? Why do we feel this way?\n"
                           f"Length: 600 words.")
            },
            {
                "name": "Part 3: The Existential Conclusion",
                "prompt": (f"{style_guide}\n\n"
                           f"TASK: Write Part 3 (The Conclusion) about '{topic}'.\n"
                           f"Structure:\n"
                           f"1. Zoom out to the bigger picture (Society/Human Nature).\n"
                           f"2. Ask a final lingering philosophical question.\n"
                           f"3. Do NOT ask for likes/subscribes. End with a profound statement.\n"
                           f"Length: 300 words.")
            }
        ]
        
        full_script = ""
        for p in parts:
            print(f"      -> Generating {p['name']}...")
            chunk = groq_generate(p['prompt'])
            if chunk: 
                # Clean chunk just in case
                chunk = chunk.replace("Part 1:", "").replace("Part 2:", "").replace("Part 3:", "").strip()
                full_script += chunk + "\n\n"
        
        # Validation
        if len(full_script.split()) < 300:
             print("   [Error] Generated script was too short. Retrying...")
             return None
             
        return full_script

def get_user_or_ai_script(topic):
    print("---------------------------------------------------")
    print(" SCRIPT SOURCE")
    print("---------------------------------------------------")
    print(" 1. Write it for me (AI)")
    print(" 2. I will paste it manually")
    choice = smart_input(" > Enter choice (1 or 2) [Auto: 1]: ", timeout=30, default_value="1").strip()
    if choice == "1":
        script = generate_viral_script(topic)
        if script: return script
        print("   [!] AI failed. Switching to manual input.")
    script = input(" > ").strip()
    while len(script) < 20: script = input(" > ").strip()
    return script

# --- BATCHED VISUAL GENERATOR ---
def get_visuals_from_ai_batch(sentences, topic):
    """Asks Groq to generate visuals. Adds 'AI:' prefix for surreal scenes."""
    prompt = (
        f"I have a video script about '{topic}'. Here are {len(sentences)} sentences from it.\n"
        f"For EACH sentence, provide ONE visual search term.\n"
        f"Rules:\n"
        f"1. If the scene is realistic (people, cities, nature), just give the search term (e.g., 'busy street').\n"
        f"2. If the scene is Abstract, Sci-Fi, Fantasy, or Impossible to film (e.g., 'glass taj mahal', 'famous person doing something','Trump'), PREFIX it with 'AI: ' (e.g., 'AI: glowing cyber brain').\n"
        f"3. Output strictly a JSON object: {{ \"visuals\": [\"term1\", \"term2\", ...] }}\n"
        f"4. The list must have exactly {len(sentences)} items.\n\n"
        f"Sentences:\n" + "\n".join([f"{i+1}. {s}" for i, s in enumerate(sentences)])
    )
    
    json_resp = groq_generate(prompt, json_mode=True)
    visuals = []
    
    if json_resp:
        try:
            data = json.loads(clean_json_text(json_resp))
            visuals = data.get("visuals", [])
        except: pass
        
    if len(visuals) != len(sentences):
        return [extract_visual_keyword_python(s) for s in sentences]
        
    return visuals

def extract_visual_keyword_python(sentence):
    """Better Python Fallback: Picks longest meaningful word."""
    clean = re.sub(r'[^\w\s]', '', sentence.lower())
    words = clean.split()
    stopwords = ["the", "is", "are", "was", "to", "of", "and", "a", "in", "that", "it", "for", "on", "with", "as", "by", "at", "this", "when", "what", "where"]
    meaningful_words = [w for w in words if w not in stopwords and len(w) > 3]
    if not meaningful_words: return "dark cinematic background"
    # Return the LONGEST word (usually most specific)
    return max(meaningful_words, key=len)

# --- TIMELINE GENERATOR (STOCK VIDEO ONLY) ---
def generate_timeline_batched(topic, script):
    print("   [System] Generating Timeline (Stock Footage Mode)...")
    
    # 1. Clean and split script
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', script) if len(s) > 5]
    total_scenes = len(sentences)
    print(f"   [System] Identified {total_scenes} scenes. Processing in batches...")
    
    timeline = []
    batch_size = 15 
    
    total_batches = math.ceil(total_scenes / batch_size)
    
    for i in range(0, total_scenes, batch_size):
        batch = sentences[i : i + batch_size]
        current_batch_num = (i // batch_size) + 1
        
        print(f"      -> Processing Batch {current_batch_num}/{total_batches} ({len(batch)} scenes)...")
        
        # --- PROMPT: The "Director" Instructions (STOCK ONLY) ---
        prompt = (
            f"You are a Video Editor searching for footage. I will give you {len(batch)} script sentences.\n"
            f"Topic: {topic}\n"
            f"Sentences: {json.dumps(batch)}\n\n"
            f"Generate a visual search term for each sentence.\n"
            f"RULES:\n"
            f"1. FOR REALISTIC SCENES (Cities, Nature, People): Return a simple search term (e.g., 'busy street').\n"
            f"2. FOR ABSTRACT/HISTORICAL/FANTASY (e.g., 'Ancient Rome', 'Cyber Brain', 'Monster'): Prefix with '[AI]' (e.g., '[AI] Ancient Roman soldier angry').\n"
            f"3. USE [AI] SPARINGLY! Only for things that don't exist in stock footage.\n"
            f"4. Return ONLY a JSON list of strings: ['term 1', '[AI] term 2', ...]\n"
        )
        
        try:
            response = groq_generate(prompt)
            visuals = json.loads(clean_json_text(response))
            
            # Safety: Ensure list length matches
            if len(visuals) != len(batch):
                while len(visuals) < len(batch): visuals.append(topic)
                visuals = visuals[:len(batch)]
                
        except Exception as e:
            print(f"      [Error] Batch failed: {e}. Using defaults.")
            visuals = [topic] * len(batch)
        
        for text, visual in zip(batch, visuals):
            # Clean any accidental "AI:" tags just in case
            clean_visual = visual.replace("AI:", "").strip()
            timeline.append({'text': text, 'visual': clean_visual})
            
    print(f"   [Success] Timeline generated with {len(timeline)} scenes.")
    return timeline

# --- SEO & SCENE GENERATOR (UPDATED: High-Retention Metadata) ---
def generate_scene_data(topic):
    final_script = get_user_or_ai_script(topic)
    print(f"\n2. Analyzing Script & Generating SEO Metadata...")
    
    # STEP 1: ADVANCED SEO PROMPT
    # We explicitly tell Groq to write a long, keyword-rich description.
    prompt = (
        f"You are a YouTube Algorithm Expert. Generate viral metadata for a Short about '{topic}'.\n"
        f"Script snippet: {final_script[:150]}...\n\n"
        f"REQUIREMENTS:\n"
        f"1. TITLE: Clickbaity, short, punchy (under 60 chars). No quotes.\n"
        f"2. DESCRIPTION: Write a compelling 3-part description:\n"
        f"   - Part A: The Hook (e.g. 'You won't believe what happens when...')\n"
        f"   - Part B: Keywords/Context (Use words like 'Mystery', 'Facts', 'Dark', 'Truth').\n"
        f"   - Part C: Hashtags (Include exactly these 5: #Shorts #{topic.replace(' ', '')} #Viral #Facts #Mystery).\n"
        f"3. TAGS: List 20 high-volume search keywords for this niche (comma-separated, NO hashtags in this list, just phrases).\n\n"
        f"OUTPUT STRICT JSON:\n"
        f"{{ \"title\": \"...\", \"description\": \"...\", \"tags\": [\"keyword1\", \"keyword2\", ...] }}"
    )

    # Defaults in case AI fails
    title = topic
    desc = f"Watch this viral video about {topic}. #Shorts"
    tags = ["Viral", "Shorts", "Mystery", "Facts", "Dark Psychology"]

    json_response = groq_generate(prompt, json_mode=True)
    
    if json_response:
        try:
            data = json.loads(clean_json_text(json_response))
            title = data.get("title", topic)
            desc = data.get("description", desc)
            tags = data.get("tags", tags)
            
            # Safety Check: Ensure #Shorts is always in the description
            if "#Shorts" not in desc:
                desc += "\n\n#Shorts #Viral #DarkFacts"
                
            print("   [Success] Viral SEO Metadata Generated.")
        except Exception as e:
            print(f"   [Error] SEO Generation failed: {e}")

    # Save to file (So the Uploader can read it later)
    try:
        with open("temp/description.txt", "w", encoding="utf-8") as f:
            # We join tags with commas for the text file
            tag_string = ", ".join(tags) if isinstance(tags, list) else str(tags)
            f.write(f"TITLE: {title}\nDESCRIPTION: {desc}\n\nTAGS: {tag_string}\n")
    except: pass

    # STEP 2: TIMELINE (BATCHED)
    # This part remains the same to generate your video visuals
    timeline = generate_timeline_batched(topic, final_script)
    
    return topic, timeline, tags

# --- AUDIO ENGINE (WITH ELASTIC SYNC) ---
async def generate_segmented_audio(timeline, session_id):
    """Generates TTS audio files for each scene in the timeline."""
    print(f"2.5 Generating Audio & Timing for {len(timeline)} scenes...")
    selected_voice = get_random_voice()
    audio_files = []

    # Ensure we have the tool to measure audio duration
    from moviepy.editor import AudioFileClip

    for i, scene in enumerate(timeline):
        text = scene['text']
        clean_text = re.sub(r'[#*]', '', text).strip()
        filename = os.path.join(TEMP_DIR, f"audio_{i}_{session_id}.mp3")
        timing_filename = os.path.join(TEMP_DIR, f"timing_{i}_{session_id}.json")
        
        # 1. SPEED SETTINGS
        if "hi-" in selected_voice:
            rate = "+30%" 
        else:
            rate = "+10%"

        communicate = edge_tts.Communicate(clean_text, selected_voice, rate=rate)
        word_timings = []
        
        try:
            with open(filename, "wb") as file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio": 
                        file.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        start = chunk["offset"] / 10_000_000
                        dur = chunk["duration"] / 10_000_000
                        word_timings.append({"word": chunk["text"], "start": start, "end": start + dur})
        
            # 2. ELASTIC SYNC FIX (Crucial for Hindi/Hinglish)
            if os.path.exists(filename) and word_timings:
                try:
                    # Measure the ACTUAL generated audio length
                    audioclip = AudioFileClip(filename)
                    real_duration = audioclip.duration
                    audioclip.close()
                    
                    # Measure the THEORETICAL timestamp length
                    last_timestamp_end = word_timings[-1]['end']
                    
                    # Calculate Stretch Factor
                    # If audio is 5.0s but timestamps end at 4.5s, factor is 1.11
                    if last_timestamp_end > 0:
                        stretch_factor = real_duration / last_timestamp_end
                        
                        # Apply stretch to every word to sync perfectly
                        for w in word_timings:
                            w['start'] = w['start'] * stretch_factor
                            w['end'] = w['end'] * stretch_factor
                except Exception as e:
                    print(f"   [Sync Warning] Could not apply elastic sync: {e}")

            # Save corrected timing file
            with open(timing_filename, "w", encoding='utf-8') as f: 
                json.dump(word_timings, f)
                
            if os.path.exists(filename): 
                audio_files.append(filename)

        except Exception as e: 
            print(f"   [Error] Audio gen failed for segment {i}: {e}")

    print(f"   [Success] Generated {len(audio_files)} audio segments.")
    return audio_files

# --- AI IMAGE GENERATOR (HYBRID: Hugging Face -> Pollinations Backup) ---
import urllib.parse  # <--- MAKE SURE THIS IS IMPORTED AT THE TOP
import requests
import re
import random
import config

def generate_ai_image(query, filename, mode):
    # 1. CLEAN QUERY
    safe_query = re.sub(r'[^a-zA-Z0-9\s,]', '', query)
    
    # 2. DEFINE RESOLUTIONS
    if mode in ["Shorts", "Portrait"]:
        width, height = 720, 1280
    else:
        width, height = 1280, 720

    # Simplify the prompt for the URL to avoid timeouts
    # We add "hyperrealistic" to ensure quality without complex tokens
    prompt = f"hyperrealistic photo of {safe_query}, cinematic lighting, 8k"

    # ==============================================================================
    # ATTEMPT 1: POLLINATIONS.AI (Standard Model)
    # ==============================================================================
    print(f"      [AI Art] Trying Pollinations (Free): '{safe_query}'...")
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        seed = random.randint(1, 99999)
        
        # REMOVED '&model=flux' -> Defaults to standard (Faster/Stable)
        poly_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={seed}"
        
        # Increased timeout to 90s just in case
        response = requests.get(poly_url, timeout=90)
        
        if response.status_code == 200 and len(response.content) > 1024:
            with open(filename, 'wb') as f: f.write(response.content)
            print("      [Success] Generated via Pollinations.")
            return filename
        else:
            print(f"      [Fail] Pollinations Status: {response.status_code}")

    except Exception as e:
        print(f"      [Warning] Pollinations failed: {e}")

    # ==============================================================================
    # ATTEMPT 2: HUGGING FACE (Backup)
    # ==============================================================================
    if hasattr(config, 'HF_API_KEY') and config.HF_API_KEY.startswith("hf_"):
        print(f"      [AI Art] Trying Hugging Face Backup...")
        headers = {"Authorization": f"Bearer {config.HF_API_KEY}"}
        # Use a more detailed prompt for HF since it handles it well
        hf_prompt = f"cinematic shot of {safe_query}, highly detailed, 8k masterpiece"
        payload = {"inputs": hf_prompt}
        api_url = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"

        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                with open(filename, 'wb') as f: f.write(response.content)
                print("      [Success] Generated via Hugging Face.")
                return filename
            else:
                print(f"      [Skip] HF Status: {response.status_code}")
        except:
            pass

    print("      [Fail] All AI methods failed. Switching to Stock.")
    return None

 # In generators.py -> Replace the entire download_specific_scenes function

def download_specific_scenes(timeline, session_id):
    print(f"3. Downloading Media (Stock Mode Only)...")
    
    # Setup Config & Temp Dir
    mode = config.VIDEO_MODE if hasattr(config, 'VIDEO_MODE') else "Shorts"
    orientation = config.VIDEO_SETTINGS[mode]["orientation"]
    TEMP_DIR = "temp"
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
    
    video_files = []
    headers = {'Authorization': config.PEXELS_API_KEY}
    
    # 1. SET QUOTA LIMITS (Kept for future reference)
    if mode == "Shorts":
        ai_quota = getattr(config, 'MAX_AI_IMAGES_SHORTS', 4)
    else:
        ai_quota = getattr(config, 'MAX_AI_IMAGES_LONG', 15)
        
    ai_generated_count = 0

    for i, scene in enumerate(timeline):
        raw_query = scene['visual']
        
        # 2. DECIDE: AI OR STOCK?
        # Clean the query immediately so we can use it for Stock search
        clean_query = raw_query.replace("[AI]", "").replace("[ai]", "").replace("hyperrealistic", "").strip()
        
        filename = os.path.join(TEMP_DIR, f"clip_{i}_{session_id}.mp4") # Default video container
        ai_filename = os.path.join(TEMP_DIR, f"clip_{i}_{session_id}.png") # AI Image container
        found = False

        # --- PATH A: AI GENERATION (DISABLED / COMMENTED OUT) ---
        # use_ai = False
        # if "[AI]" in raw_query.upper():
        #     if ai_generated_count < ai_quota:
        #         print(f"   [Scene {i+1}] 🤖 AI Tag detected... but AI Mode is DISABLED.")
        #         # use_ai = True 
        #     else:
        #         print(f"   [Quota Limit] Max AI images ({ai_quota}) reached. Switching to Stock.")
        
        # if use_ai:
        #     print(f"   [Scene {i+1}] 🤖 Generating AI Art: '{clean_query}'")
        #     ai_path = generate_ai_image(clean_query, ai_filename, mode)
        #     if ai_path and os.path.exists(ai_path):
        #         video_files.append(ai_path)
        #         ai_generated_count += 1
        #         found = True
        #         print(f"      [Success] AI Image created. (Quota: {ai_generated_count}/{ai_quota})")
        #     else:
        #         print("      [Fallback] AI failed. Switching to Stock.")
        # --------------------------------------------------------

        # --- PATH B: STOCK FOOTAGE (Default) ---
        if not found:
            print(f"   [Scene {i+1}] 🎥 Searching Stock: '{clean_query}'")
            
            # 1. PEXELS VIDEO
            try:
                r = requests.get(f"https://api.pexels.com/videos/search?query={clean_query}&per_page=15&orientation={orientation}", headers=headers, timeout=10).json()
                valid = [v for v in r.get('videos', []) if v['duration'] >= 4]
                
                # Filter by aspect ratio to avoid bad crops
                if mode == "Shorts": 
                    valid = [v for v in valid if v['width'] <= v['height']]
                else: 
                    valid = [v for v in valid if v['height'] <= v['width']]
                
                if valid:
                    link = random.choice(valid[:3])['video_files'][0]['link']
                    with requests.get(link, stream=True) as req, open(filename, 'wb') as f:
                        for chunk in req.iter_content(8192): f.write(chunk)
                    video_files.append(filename)
                    found = True
                    print("      [Success] Pexels Video found.")
            except: pass

            # 2. PIXABAY VIDEO (Backup)
            if not found and hasattr(config, 'PIXABAY_API_KEY'):
                try:
                    ori = "vertical" if orientation == "portrait" else "horizontal"
                    r = requests.get(f"https://pixabay.com/api/videos/?key={config.PIXABAY_API_KEY}&q={clean_query}&video_type=film&orientation={ori}", timeout=10).json()
                    valid = [v for v in r.get('hits', []) if v['duration'] >= 4]
                    if valid:
                        link = random.choice(valid[:3])['videos']['medium']['url']
                        with requests.get(link, stream=True) as req, open(filename, 'wb') as f:
                            for chunk in req.iter_content(8192): f.write(chunk)
                        video_files.append(filename)
                        found = True
                        print("      [Success] Pixabay Video found.")
                except: pass
            
            # 3. PEXELS PHOTO (Final Safety Net)
            if not found:
                try:
                    img_filename = os.path.join(TEMP_DIR, f"clip_{i}_{session_id}.jpg")
                    r = requests.get(f"https://api.pexels.com/v1/search?query={clean_query}&per_page=1", headers=headers, timeout=10).json()
                    if r.get('photos'):
                        k = 'portrait' if orientation == 'portrait' else 'landscape'
                        link = r['photos'][0]['src'][k]
                        with requests.get(link, stream=True) as req, open(img_filename, 'wb') as f:
                            for chunk in req.iter_content(8192): f.write(chunk)
                        video_files.append(img_filename)
                        found = True
                        print("      [Success] Stock Photo found (Fallback).")
                except: pass
        
        # FINAL CHECK: Black Screen Failsafe
        if not found:
            print("      [Fail] No media found. Using Black Screen placeholder.")
            from moviepy.editor import ColorClip
            black_path = os.path.join(TEMP_DIR, f"clip_{i}_{session_id}.jpg")
            # Create a 720x1280 (Shorts) or 1280x720 (Long) black image
            w, h = (720, 1280) if mode == "Shorts" else (1280, 720)
            ColorClip(size=(w, h), color=(0,0,0), duration=5).save_frame(black_path, t=1)
            video_files.append(black_path)

        time.sleep(1) # Polite delay
        
    return video_files