from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from sqlalchemy.orm import Session
from models import GoogleCredentials
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os

def get_google_credentials(db: Session, user_id: str) -> Optional[Credentials]:
    """ユーザーのGoogle認証情報を取得"""
    cred_record = db.query(GoogleCredentials).filter(GoogleCredentials.user_id == user_id).first()
    if not cred_record:
        return None
    
    creds = Credentials(
        token=cred_record.access_token,
        refresh_token=cred_record.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
    )
    
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        cred_record.access_token = creds.token
        cred_record.token_expiry = creds.expiry
        cred_record.updated_at = datetime.now()
        db.commit()
    
    return creds

def sync_todo_to_google_tasks(creds: Credentials, title: str, description: str = None) -> Dict:
    """GoogleタスクにTodoを同期"""
    service = build('tasks', 'v1', credentials=creds)
    
    task = {
        'title': title,
        'notes': description or ''
    }
    
    result = service.tasks().insert(tasklist='@default', body=task).execute()
    return result

def sync_event_to_google_calendar(creds: Credentials, title: str, start_time: datetime, end_time: datetime, description: str = None, location: str = None) -> Dict:
    """Googleカレンダーにイベントを同期"""
    service = build('calendar', 'v3', credentials=creds)
    
    event = {
        'summary': title,
        'description': description or '',
        'location': location or '',
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Asia/Tokyo',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Asia/Tokyo',
        },
    }
    
    result = service.events().insert(calendarId='primary', body=event).execute()
    return result
