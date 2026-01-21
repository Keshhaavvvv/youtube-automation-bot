import google.generativeai as genai

# Your Key
GEMINI_API_KEY = "AIzaSyBCbEa62tK01iaGmfh4lKCJTN4nPaE0hA0"
genai.configure(api_key=GEMINI_API_KEY)

print("Checking available AI models for your key...")
try:
    count = 0
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
            count += 1
    
    if count == 0:
        print("No models found! Your API key might be restricted.")
    else:
        print("\nSUCCESS: Pick one of the names above (e.g., 'models/gemini-pro') and use it in bot.py")

except Exception as e:
    print(f"Error: {e}")