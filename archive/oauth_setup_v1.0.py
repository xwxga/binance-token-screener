#!/usr/bin/env python3
"""
OAuth Setup for Binance Token Screener v1.0
One-time setup script for OAuth authentication

Author: Augment Agent
Version: 1.0
Date: 2025-07-14
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import gspread

def main():
    """OAuth Setup Main Function"""
    print("🎯 OAuth Setup for Binance Token Screener v1.0")
    print("=" * 80)
    
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    oauth_creds_file = 'oauth_credentials.json'
    token_file = 'token.json'
    
    # Check OAuth credentials
    if not os.path.exists(oauth_creds_file):
        print("❌ oauth_credentials.json not found")
        print("Please ensure the file exists in current directory")
        return False
    
    print("✅ OAuth credentials file found")
    
    creds = None
    
    # Check existing token
    if os.path.exists(token_file):
        print("📋 Checking existing token...")
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
        if creds and creds.valid:
            print("✅ Existing token is valid")
        elif creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            try:
                creds.refresh(Request())
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
                print("✅ Token refreshed successfully")
            except Exception as e:
                print(f"❌ Token refresh failed: {e}")
                creds = None
    
    # New authorization if needed
    if not creds or not creds.valid:
        print("\n🌐 Starting OAuth authorization...")
        print("Browser will open for authorization")
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(oauth_creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
            
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
            
            print("✅ OAuth authorization successful!")
        except Exception as e:
            print(f"❌ OAuth authorization failed: {e}")
            return False
    
    # Test connection
    try:
        gc = gspread.authorize(creds)
        drive_service = build('drive', 'v3', credentials=creds)
        about = drive_service.about().get(fields='user,storageQuota').execute()
        
        user = about.get('user', {})
        print(f"\n👤 User: {user.get('displayName', 'N/A')} ({user.get('emailAddress', 'N/A')})")
        
        quota = about.get('storageQuota', {})
        if quota:
            limit = int(quota.get('limit', 0))
            usage = int(quota.get('usage', 0))
            if limit > 0:
                usage_percent = (usage / limit) * 100
                print(f"📊 Storage: {usage_percent:.1f}% used ({usage / (1024**3):.2f} GB / {limit / (1024**3):.2f} GB)")
        
        print("\n🎉 OAuth setup complete!")
        print("✅ Ready to run: python binance_token_screener_v1.0.py")
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    main()
