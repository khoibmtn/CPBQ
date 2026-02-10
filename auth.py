"""
auth.py - Xác thực Google OAuth2 cho BigQuery
===============================================
Sử dụng browser-based OAuth2 flow (không cần gcloud CLI).
Lưu token tại ./credentials/token.json để tái sử dụng.
"""

import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scopes cần thiết cho BigQuery
SCOPES = [
    "https://www.googleapis.com/auth/bigquery",
    "https://www.googleapis.com/auth/cloud-platform",
]

# Paths
CREDS_DIR = os.path.join(os.path.dirname(__file__), "credentials")
TOKEN_PATH = os.path.join(CREDS_DIR, "token.json")
CLIENT_SECRET_PATH = os.path.join(CREDS_DIR, "client_secret.json")


def get_credentials() -> Credentials:
    """
    Lấy credentials đã lưu hoặc chạy OAuth2 flow mới.
    
    Yêu cầu: File credentials/client_secret.json (OAuth 2.0 Client ID từ GCP Console).
    
    Hướng dẫn tạo:
    1. Vào https://console.cloud.google.com/apis/credentials?project=qtktfinder
    2. Tạo OAuth 2.0 Client ID → Desktop application
    3. Tải file JSON → lưu tại credentials/client_secret.json
    """
    creds = None

    # Kiểm tra token đã lưu
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # Refresh hoặc tạo mới
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("  🔄 Đang refresh token...")
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET_PATH):
                print("❌ Không tìm thấy file: credentials/client_secret.json")
                print()
                print("📋 Hướng dẫn tạo OAuth 2.0 Client ID:")
                print("   1. Vào: https://console.cloud.google.com/apis/credentials?project=qtktfinder")
                print("   2. Click '+ CREATE CREDENTIALS' → 'OAuth client ID'")
                print("   3. Application type: 'Desktop app'")
                print("   4. Tải file JSON về")
                print(f"   5. Lưu tại: {CLIENT_SECRET_PATH}")
                raise FileNotFoundError(
                    f"Cần file OAuth client secret tại: {CLIENT_SECRET_PATH}"
                )

            print("  🌐 Mở trình duyệt để đăng nhập Google...")
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Lưu token
        os.makedirs(CREDS_DIR, exist_ok=True)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
        print("  ✅ Đã lưu token xác thực")

    return creds
