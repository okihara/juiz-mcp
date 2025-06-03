from typing import Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from models import GoogleCredentials
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import json


def get_google_credentials(user_id: str, db: Session) -> Optional[Credentials]:
    """データベースからGoogleクレデンシャルを取得してCredentialsオブジェクトを作成"""
    cred_record = db.query(GoogleCredentials).filter(GoogleCredentials.user_id == user_id).first()
    if not cred_record:
        return None
    
    # Credentialsオブジェクトを作成
    creds = Credentials(
        token=cred_record.access_token,
        refresh_token=cred_record.refresh_token,
        token_uri=cred_record.token_uri,
        client_id=cred_record.client_id,
        client_secret=cred_record.client_secret,
        scopes=json.loads(cred_record.scopes)
    )
    
    # トークンが期限切れの場合は更新
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # 更新されたトークンをデータベースに保存
        cred_record.access_token = creds.token
        if creds.expiry:
            cred_record.expiry = creds.expiry
        db.commit()
    
    return creds


def save_google_credentials(user_id: str, creds: Credentials, db: Session):
    """Googleクレデンシャルをデータベースに保存"""
    # 既存のクレデンシャルを検索
    cred_record = db.query(GoogleCredentials).filter(GoogleCredentials.user_id == user_id).first()
    
    if cred_record:
        # 既存のレコードを更新
        cred_record.access_token = creds.token
        cred_record.refresh_token = creds.refresh_token
        cred_record.expiry = creds.expiry
        cred_record.updated_at = datetime.now()
    else:
        # 新しいレコードを作成
        cred_record = GoogleCredentials(
            user_id=user_id,
            access_token=creds.token,
            refresh_token=creds.refresh_token,
            token_uri=creds.token_uri,
            client_id=creds.client_id,
            client_secret=creds.client_secret,
            scopes=json.dumps(creds.scopes),
            expiry=creds.expiry,
            created_at=datetime.now()
        )
        db.add(cred_record)
    
    db.commit()
    return cred_record


def get_google_calendar_service(user_id: str, db: Session):
    """Google Calendar APIサービスを取得"""
    creds = get_google_credentials(user_id, db)
    if not creds:
        return None
    
    return build('calendar', 'v3', credentials=creds)


def get_google_tasks_service(user_id: str, db: Session):
    """Google Tasks APIサービスを取得"""
    creds = get_google_credentials(user_id, db)
    if not creds:
        return None
    
    return build('tasks', 'v1', credentials=creds)


def start_google_oauth(user_id: str, client_id: str, client_secret: str, redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob") -> Dict:
    """Google OAuth認証フローを開始する"""
    try:
        from google_auth_oauthlib.flow import Flow
        
        # 認証に必要なスコープを設定
        scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/tasks'
        ]
        
        # OAuth フローを設定
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=scopes
        )
        flow.redirect_uri = redirect_uri
        
        # 認証URLを生成
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        return {
            "auth_url": auth_url,
            "user_id": user_id,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "message": "Please visit the auth_url and get the authorization code, then use complete_google_oauth to finish the setup."
        }
        
    except Exception as e:
        return {"error": f"Failed to start OAuth flow: {str(e)}"}


def complete_google_oauth(user_id: str, client_id: str, client_secret: str, auth_code: str, redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob") -> Dict:
    """Google OAuth認証フローを完了し、クレデンシャルを保存する"""
    try:
        from google_auth_oauthlib.flow import Flow
        from models import get_db
        
        # 認証に必要なスコープを設定
        scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/tasks'
        ]
        
        # OAuth フローを設定
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=scopes
        )
        flow.redirect_uri = redirect_uri
        
        # 認証コードを使用してトークンを取得
        flow.fetch_token(code=auth_code)
        creds = flow.credentials
        
        # データベースセッションを取得
        db = next(get_db())
        
        # クレデンシャルをデータベースに保存
        save_google_credentials(user_id, creds, db)
        
        return {
            "success": True,
            "message": f"Google authentication completed successfully for user {user_id}",
            "user_id": user_id
        }
        
    except Exception as e:
        return {"error": f"Failed to complete OAuth flow: {str(e)}"}


def check_google_credentials(user_id: str) -> Dict:
    """ユーザーのGoogleクレデンシャルの状態を確認する"""
    try:
        from models import get_db
        
        db = next(get_db())
        cred_record = db.query(GoogleCredentials).filter(GoogleCredentials.user_id == user_id).first()
        
        if not cred_record:
            return {
                "connected": False,
                "message": "No Google credentials found for this user"
            }
        
        # クレデンシャルが有効かどうかを確認
        creds = get_google_credentials(user_id, db)
        if creds:
            return {
                "connected": True,
                "user_id": user_id,
                "scopes": json.loads(cred_record.scopes),
                "created_at": cred_record.created_at.isoformat(),
                "updated_at": cred_record.updated_at.isoformat(),
                "message": "Google credentials are valid and connected"
            }
        else:
            return {
                "connected": False,
                "message": "Google credentials found but invalid or expired"
            }
            
    except Exception as e:
        return {"error": f"Failed to check credentials: {str(e)}"}