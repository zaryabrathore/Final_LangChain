import os
import sys
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from app.config import settings

def main():
    print("=" * 60)
    print(" Google Workspace OAuth Token Generator for LangGraph Agent")
    print("=" * 60)

    client_id = settings.google_client_id
    client_secret = settings.google_client_secret

    if not client_id or not client_secret or "your_" in client_id.lower() or "your_" in client_secret.lower():
        print("❌ Error: Valid GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in backend/.env")
        return

    scopes = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.compose'
    ]

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"]
        }
    }

    try:
        print("\nOpening browser for Google login...")
        flow = InstalledAppFlow.from_client_config(client_config, scopes)
        creds = flow.run_local_server(port=8090, prompt='consent', access_type='offline')

        if creds and creds.refresh_token:
            refresh_token = creds.refresh_token
            print(f"\n✅ OAuth Authorization Successful!")
            print(f"Refresh Token: {refresh_token}")

            # Update backend/.env file automatically
            env_path = os.path.join(os.path.dirname(__file__), ".env")
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                new_lines = []
                token_updated = False
                for line in lines:
                    if line.startswith("GOOGLE_REFRESH_TOKEN="):
                        new_lines.append(f"GOOGLE_REFRESH_TOKEN={refresh_token}\n")
                        token_updated = True
                    else:
                        new_lines.append(line)
                
                if not token_updated:
                    new_lines.append(f"GOOGLE_REFRESH_TOKEN={refresh_token}\n")
                
                with open(env_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                
                print(f"✅ Updated GOOGLE_REFRESH_TOKEN in backend/.env")
            else:
                print(f"⚠️ Could not find .env file at {env_path}")
        else:
            print("⚠️ Warning: No refresh token returned. Try revoking app access and running again.")
    except Exception as e:
        print(f"\n❌ OAuth Error: {e}")

if __name__ == "__main__":
    main()
