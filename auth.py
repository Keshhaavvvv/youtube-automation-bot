import os
from google_auth_oauthlib.flow import InstalledAppFlow

# The permissions the bot needs
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/spreadsheets'
]

def authenticate():
    # Check if the secret file exists
    if not os.path.exists('client_secret.json'):
        print("ERROR: client_secret.json not found! Please check Step 2.")
        return

    # Start the login process
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json', SCOPES)
    
    # Open a browser window for you to log in
    creds = flow.run_local_server(port=0)

    # Save the login token
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    
    print("\nSUCCESS! 'token.json' has been created. You are ready for the next step.")

if __name__ == '__main__':
    authenticate()