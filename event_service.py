from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from models import EventItem as DBEventItem, get_db
from schemas import EventItem
from google_api import get_google_calendar_service


def _to_rfc3339_utc(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        # naive datetimeはローカルタイムゾーン（Asia/Tokyo）と仮定
        dt = dt.replace(tzinfo=timezone(timedelta(hours=9)))
    return dt.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')



def add_event(user_id: str, title: str, start_time: datetime, end_time: datetime, description: str = None, location: str = None, sync_to_google: bool = True) -> Dict:
    """カレンダーイベントを追加する"""
    # データベースセッションを取得
    db = next(get_db())
    
    # 新しいイベントアイテムを作成
    db_event = DBEventItem(
        user_id=user_id,
        title=title,
        description=description,
        start_time=start_time,
        end_time=end_time,
        location=location,
        created_at=datetime.now()
    )
    
    # データベースに追加して保存
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    # Google Calendarとの同期を試行
    google_event_id = None
    if sync_to_google:
        try:
            calendar_service = get_google_calendar_service(user_id, db)
            if calendar_service:
                # イベントボディを作成
                event_body = {
                    'summary': title,
                    'description': description or '',
                    'start': {
                        'dateTime': start_time.isoformat(),
                        'timeZone': 'Asia/Tokyo',
                    },
                    'end': {
                        'dateTime': end_time.isoformat(),
                        'timeZone': 'Asia/Tokyo',
                    },
                }
                
                if location:
                    event_body['location'] = location
                
                # Google Calendarにイベントを追加
                result = calendar_service.events().insert(
                    calendarId='primary',
                    body=event_body
                ).execute()
                google_event_id = result.get('id')
        except Exception as e:
            # Google API呼び出しでエラーが発生した場合、ログに記録するが処理は継続
            print(f"Google Calendar API error: {e}")
    
    # Pydanticモデルに変換して返す
    result = EventItem.from_orm(db_event).dict()
    if google_event_id:
        result['google_event_id'] = google_event_id
    return result


def get_event(user_id: str, event_id: int) -> Dict:
    """指定されたIDのイベントアイテムを取得する"""
    # データベースセッションを取得
    db = next(get_db())
    
    # 指定されたIDのイベントを取得
    event = db.query(DBEventItem).filter(DBEventItem.id == event_id).first()
    
    # イベントが存在しない場合
    if event is None:
        return {"error": f"Event with ID {event_id} not found"}
    
    # ユーザーのイベントかどうかを確認
    if event.user_id != user_id:
        return {"error": f"Event with ID {event_id} not found for user {user_id}"}
    
    # Pydanticモデルに変換して返す
    return EventItem.from_orm(event).dict()


def get_all_events(user_id: str, start_date: datetime, end_date: Optional[datetime] = None, include_google_calendar: bool = True) -> List[Dict]:
    """ユーザーの全てのイベントアイテムを取得する"""
    # データベースセッションを取得
    db = next(get_db())
    
    # ユーザーのイベントを検索するクエリを作成
    query = db.query(DBEventItem).filter(DBEventItem.user_id == user_id)
    
    # 日付範囲でフィルタリング
    if start_date:
        query = query.filter(DBEventItem.start_time >= start_date)
    if end_date:
        query = query.filter(DBEventItem.end_time <= end_date)
    
    # 開始日時でソート
    query = query.order_by(DBEventItem.start_time)
    
    # クエリを実行してイベントアイテムを取得
    events = query.all()
    result = [EventItem.from_orm(event).dict() for event in events]
    
    # Google Calendarからのイベントも取得
    if include_google_calendar:
        try:
            calendar_service = get_google_calendar_service(user_id, db)
            if calendar_service:
                # Google Calendarからイベントを取得
                request_params = {'calendarId': 'primary'}
                
                time_min_val = _to_rfc3339_utc(start_date)
                if time_min_val:
                    request_params['timeMin'] = time_min_val
                
                time_max_val = _to_rfc3339_utc(end_date)
                if time_max_val:
                    request_params['timeMax'] = time_max_val
                
                google_events = calendar_service.events().list(**request_params).execute()
                
                for google_event in google_events.get('items', []):
                    # 開始時刻と終了時刻を解析
                    start_time_str = google_event.get('start', {}).get('dateTime')
                    end_time_str = google_event.get('end', {}).get('dateTime')
                    
                    if start_time_str and end_time_str:
                        from datetime import datetime
                        import re
                        
                        # ISO形式の日時文字列をパース
                        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                        
                        # Google Eventを結果に追加
                        created_at_str = google_event.get('created')
                        created_at_dt = None
                        if created_at_str:
                            try:
                                created_at_dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                            except ValueError:
                                print(f"Warning: Could not parse google_event created_at: {created_at_str}")
                                created_at_dt = None # パース失敗時はNoneにする

                        result.append({
                            'id': f"google_{google_event.get('id')}",
                            'user_id': user_id,
                            'title': google_event.get('summary', ''),
                            'description': google_event.get('description', ''),
                            'start_time': start_time, # datetimeオブジェクトとして格納
                            'end_time': end_time,     # datetimeオブジェクトとして格納
                            'location': google_event.get('location', ''),
                            'created_at': created_at_dt, # パースされたdatetimeオブジェクトまたはNone
                            'source': 'google_calendar',
                            'google_event_id': google_event.get('id')
                        })
        except Exception as e:
            # Google API呼び出しでエラーが発生した場合、ログに記録するが処理は継続
            print(f"Google Calendar API error: {e}")
    
    # 開始時刻でソート
    result.sort(key=lambda x: x.get('start_time', ''))
    
    return result