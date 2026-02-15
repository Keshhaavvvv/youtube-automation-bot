# translate_script.py
import os
import json
import config
from groq import Groq

# --- CONFIGURATION ---
# We use the existing keys from your config file
GROQ_API_KEY = config.GROQ_API_KEYS[0]

def get_hinglish_translation(english_script):
    client = Groq(api_key=GROQ_API_KEY)
    
    system_prompt = (
        "You are a professional YouTube scriptwriter for the Indian market. "
        "Your goal is to translate English scripts into viral 'Hinglish' (Hindi + English mix). "
        "\n\n"
        "RULES:"
        "\n1. Tone: Casual, Thrilling, Storytelling (Gen-Z/Millennial style)."
        "\n2. Vocabulary: Keep technical/impact words in English (e.g., 'Dark Web', 'Mystery', 'AI', 'Danger'). "
        "Translate connecting verbs and filler words into Hindi."
        "\n3. Output Format: JSON containing two versions:"
        "\n   - 'roman': Roman script (English alphabet) -> For Subtitles."
        "\n   - 'devanagari': Devanagari script (Hindi alphabet) -> For Audio Generation."
    )
    
    user_prompt = f"Translate this script:\n\n'{english_script}'"
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt + "\n\nOutput strict JSON."}
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

def run_test():
    print("---------------------------------------------------")
    print(" 🇮🇳 HINGLISH TRANSLATION TEST")
    print("---------------------------------------------------")
    
    # 1. The English Sample (A typical script your bot would write)
    english_sample = (
        "The dark web is not just a myth; it is a digital underworld. "
        "Hackers use it to sell stolen data and illegal secrets. "
        "But the scariest part is that your personal information might already be there. "
        "Once it is leaked, there is no turning back."
    )
    
    print(f" 📝 ORIGINAL ENGLISH:\n{english_sample}\n")
    print(" ⏳ Translating to Hinglish via Groq AI...")
    
    # 2. Call the AI
    result = get_hinglish_translation(english_sample)
    
    # 3. Display Results
    try:
        data = json.loads(result)
        
        print("\n---------------------------------------------------")
        print(" 🅰️  ROMAN HINGLISH (For Subtitles)")
        print("---------------------------------------------------")
        print(data.get('roman', 'Error parsing Roman text'))
        
        print("\n---------------------------------------------------")
        print(" 🕉️  DEVANAGARI HINGLISH (For Audio/TTS)")
        print("---------------------------------------------------")
        print(data.get('devanagari', 'Error parsing Devanagari text'))
        
    except:
        print("\n[Raw Output - Parsing Failed]")
        print(result)

if __name__ == "__main__":
    run_test()