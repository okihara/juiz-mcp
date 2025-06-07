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
    if not cred_record or not cred_record.token_json:
        return None
    
    try:
        info = json.loads(cred_record.token_json)
        creds = Credentials.from_authorized_user_info(info)
    except json.JSONDecodeError:
        # TODO: エラーログを出すなど検討
        return None
    
    # トークンが期限切れの場合は更新
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # 更新されたトークンをデータベースに保存
            cred_record.token_json = creds.to_json()
            cred_record.updated_at = datetime.now()
            db.commit()
        except Exception as e:
            # TODO: トークンリフレッシュ失敗時のエラーハンドリングを検討
            print(f"Failed to refresh token for user {user_id}: {e}") # 例: ログ出力
            pass # エラーがあっても、元のcredsで試みる場合もある
    
    return creds


def save_google_credentials(user_id: str, creds: Credentials, db: Session):
    """Googleクレデンシャルをデータベースに保存"""
    cred_record = db.query(GoogleCredentials).filter(GoogleCredentials.user_id == user_id).first()
    
    token_data_json = creds.to_json() # CredentialsオブジェクトをJSON文字列に変換

    if cred_record:
        # 既存のレコードを更新
        cred_record.token_json = token_data_json
        cred_record.updated_at = datetime.now()
    else:
        # 新しいレコードを作成
        cred_record = GoogleCredentials(
            user_id=user_id,
            token_json=token_data_json,
            created_at=datetime.now(),
            updated_at=datetime.now()
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
        creds = get_google_credentials(user_id, db)
        
        if not creds:
            return {
                "connected": False,
                "message": "No Google credentials found or they are invalid for this user"
            }
        
        # created_at と updated_at を取得するために再度DB問い合わせ（credsオブジェクトには含まれないため）
        cred_meta_info = db.query(GoogleCredentials.created_at, GoogleCredentials.updated_at).filter(GoogleCredentials.user_id == user_id).first()

        if cred_meta_info:
            return {
                "connected": True,
                "user_id": user_id,
                "scopes": creds.scopes, # Credentialsオブジェクトからscopesを取得
                "created_at": cred_meta_info.created_at.isoformat() if cred_meta_info.created_at else None,
                "updated_at": cred_meta_info.updated_at.isoformat() if cred_meta_info.updated_at else None,
                "message": "Google credentials are valid and connected"
            }
        else:
            # credsはあるがメタ情報がない場合 (通常は起こり得ないが念のため)
            return {
                "connected": True, # creds自体は有効なのでconnectedはTrueとする
                "user_id": user_id,
                "scopes": creds.scopes,
                "created_at": None,
                "updated_at": None,
                "message": "Google credentials are valid, but metadata (created/updated dates) is missing."
            }
            
    except Exception as e:
        return {"error": f"Failed to check Google credentials: {str(e)}"}