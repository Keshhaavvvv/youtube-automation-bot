import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

# STRICT scopes to ensure we get upload permissions
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/spreadsheets'  # Added since your screen showed it
]

def authenticate_user(token_file):
    creds = None
    
    # 1. Force delete old token to ensure fresh login
    if os.path.exists(token_file):
        os.remove(token_file)
        print(f"   🗑️  Deleted old {token_file} to force fresh login.")

    # 2. Check for client secret
    if not os.path.exists("client_secret.json"):
        print("   ❌ Error: 'client_secret.json' not found.")
        return

    # 3. Start Authentication
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_local_server(port=0)

    # 4. Save the new token
    with open(token_file, "wb") as token:
        pickle.dump(creds, token)
    print(f"   ✅ [Auth] Success! Saved credentials to '{token_file}'")

if __name__ == "__main__":
    print("\n--- DUAL CHANNEL AUTHENTICATION ---")
    print("1. Authenticate ENGLISH Channel (Main)")
    print("2. Authenticate HINDI Channel (Secondary/Manager)")
    
    choice = input("\nEnter 1 or 2: ").strip()
    
    if choice == "1":
        print("\n🔐 Authenticating ENGLISH Channel...")
        authenticate_user("token.json")
    elif choice == "2":
        print("\n🔐 Authenticating HINDI Channel...")
        authenticate_user("token_hindi.json")
    else:
        print("Invalid choice.")