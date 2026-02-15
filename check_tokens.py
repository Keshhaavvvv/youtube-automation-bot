import os
import pickle
import datetime
from google.auth.transport.requests import Request

def check_token(filename, channel_name):
    print(f"\n🔍 CHECKING: {channel_name} ({filename})")
    
    if not os.path.exists(filename):
        print(f"   ❌ FILE MISSING: {filename} not found.")
        print("      -> Run 'auth.py' to generate it.")
        return

    try:
        # Load the binary pickle file
        with open(filename, 'rb') as token:
            creds = pickle.load(token)

        # 1. Check if Valid
        is_valid = creds.valid
        status_icon = "✅" if is_valid else "⚠️"
        
        # 2. Check Expiry Time
        if creds.expiry:
            # FIX: Use modern timezone-aware UTC time
            now = datetime.datetime.now(datetime.timezone.utc)
            
            # Ensure expiry is also timezone-aware for comparison
            expiry = creds.expiry
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=datetime.timezone.utc)
            
            remaining = expiry - now
            
            # Format output string
            local_expiry = expiry.astimezone().strftime('%Y-%m-%d %H:%M:%S')
            
            if is_valid and remaining.total_seconds() > 0:
                print(f"   {status_icon} Status: Valid")
                days = remaining.days
                hours, remainder = divmod(remaining.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                print(f"   ⏳ Expires In: {days} days, {hours} hours, {minutes} mins")
                print(f"   📅 Exact Time: {local_expiry}")
                
                if days == 0 and hours < 1:
                    print("   🚨 WARNING: Token expires soon (Auto-refresh will handle this)")
                    
            else:
                print(f"   ⚠️ Status: Expired (Normal)")
                print(f"   ❌ EXPIRED: The token expired on {local_expiry}")
        else:
            print("   ℹ️  No expiry data found (Permanent Token?).")

        # 3. Check Refresh Token (The Lifeline)
        if creds.refresh_token:
            print("   ✅ Refresh Token: PRESENT") 
            print("      (System will auto-renew this instantly when running)")
        else:
            print("   ⛔ Refresh Token: MISSING")
            print("      (You MUST run 'auth.py' again)")

    except Exception as e:
        print(f"   ❌ ERROR: Could not read token file. It might be corrupt.")
        print(f"      Details: {e}")

# --- MAIN RUNNER ---
if __name__ == "__main__":
    print("===================================================")
    print(" 🔐 GOOGLE TOKEN HEALTH CHECK")
    print("===================================================")
    
    # Check English Token
    check_token("token.json", "ENGLISH CHANNEL")
    
    # Check Hindi Token
    check_token("token_hindi.json", "HINDI CHANNEL")
    
    print("\n===================================================")
    input(" Press Enter to exit...")