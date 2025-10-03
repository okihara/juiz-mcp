from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from models import get_db
from google_api import get_google_calendar_service


def _to_rfc3339_utc(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        # naive datetimeはローカルタイムゾーン（Asia/Tokyo）と仮定
        dt = dt.replace(tzinfo=timezone(timedelta(hours=9)))
    return dt.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def _create_event_dict(google_event: Dict, user_id: str) -> Dict:
    """Google CalendarイベントからEvent辞書を作成するヘルパー関数"""
    # 開始時刻と終了時刻を解析
    start_time_str = google_event.get('start', {}).get('dateTime')
    end_time_str = google_event.get('end', {}).get('dateTime')

    start_time = None
    end_time = None
    if start_time_str:
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
    if end_time_str:
        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))

    # 作成日時を解析
    created_at_str = google_event.get('created')
    created_at_dt = None
    if created_at_str:
        try:
            created_at_dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        except ValueError:
            print(f"Warning: Could not parse google_event created_at: {created_at_str}")

    return {
        'id': f"google_{google_event.get('id')}",
        'user_id': user_id,
        'title': google_event.get('summary', ''),
        'description': google_event.get('description', ''),
        'start_time': start_time,
        'end_time': end_time,
        'location': google_event.get('location', ''),
        'created_at': created_at_dt,
        'source': 'google_calendar',
        'google_event_id': google_event.get('id')
    }


def add_event(user_id: str, title: str, start_time: datetime, end_time: datetime = None, description: str = None, location: str = None, sync_to_google: bool = True) -> Dict:
    """Google Calendarにカレンダーイベントを追加する"""
    # データベースセッションを取得（Credentials用）
    db = next(get_db())

    # end_timeが指定されていない場合は、start_timeから1時間後に設定
    if end_time is None:
        end_time = start_time + timedelta(hours=1)

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

            return _create_event_dict(result, user_id)
        return {"error": "Google Calendar service not available"}
    except Exception as e:
        return {"error": f"Google Calendar API error: {e}"}


def get_event(user_id: str, event_id: str) -> Dict:
    """指定されたIDのイベントアイテムをGoogle Calendarから取得する"""
    # データベースセッションを取得（Credentials用）
    db = next(get_db())

    # Google Event IDを抽出（「google_」プレフィックスを削除）
    google_event_id = event_id.replace('google_', '') if event_id.startswith('google_') else event_id

    try:
        calendar_service = get_google_calendar_service(user_id, db)
        if calendar_service:
            # 指定されたIDのイベントを取得
            google_event = calendar_service.events().get(
                calendarId='primary',
                eventId=google_event_id
            ).execute()

            return _create_event_dict(google_event, user_id)
        return {"error": "Google Calendar service not available"}
    except Exception as e:
        return {"error": f"Event with ID {event_id} not found: {e}"}


def get_all_events(user_id: str, start_date: datetime, end_date: Optional[datetime] = None, include_google_calendar: bool = True) -> List[Dict]:
    """Google Calendarからユーザーの全てのイベントアイテムを取得する"""
    # データベースセッションを取得（Credentials用）
    db = next(get_db())

    result = []

    try:
        calendar_service = get_google_calendar_service(user_id, db)
        if calendar_service:
            # Google Calendarからイベントを取得
            request_params = {'calendarId': 'primary', 'maxResults': 10, 'singleEvents': True}

            time_min_val = _to_rfc3339_utc(start_date)
            if time_min_val:
                request_params['timeMin'] = time_min_val

            time_max_val = _to_rfc3339_utc(end_date)
            if time_max_val:
                request_params['timeMax'] = time_max_val

            print(f"[get_all_events] user_id: {user_id}, time_min: {time_min_val}, time_max: {time_max_val}")

            google_events = calendar_service.events().list(**request_params).execute()

            # 取得したイベント数をログ出力
            items = google_events.get('items', [])
            print(f"[get_all_events] user_id: {user_id}, fetched {len(items)} events from Google Calendar")

            for google_event in google_events.get('items', []):
                # 開始時刻と終了時刻が存在するイベントのみ追加
                if google_event.get('start', {}).get('dateTime') and google_event.get('end', {}).get('dateTime'):
                    event_dict = _create_event_dict(google_event, user_id)
                    result.append(event_dict)
                    # 各イベントの詳細をログ出力
                    print(f"[get_all_events] event: {event_dict.get('title')} | start: {event_dict.get('start_time')} | end: {event_dict.get('end_time')}")
    except Exception as e:
        # Google API呼び出しでエラーが発生した場合、ログに記録するが処理は継続
        print(f"Google Calendar API error: {e}")

    # 開始時刻でソート
    result.sort(key=lambda x: x.get('start_time') or datetime.min)

    print(f"[get_all_events] Returning {len(result)} events after filtering and sorting")

    return result