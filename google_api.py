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
