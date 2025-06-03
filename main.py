
from fastmcp.server import FastMCP
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
from models import TodoItem as DBTodoItem, EventItem as DBEventItem, GoogleCredentials, get_db
import json
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Pydanticモデル（APIレスポンス用）
class TodoItem(BaseModel):
    id: int
    user_id: str
    title: str
    description: Optional[str] = None
    completed: bool = False
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True
        from_attributes = True

# イベントのPydanticモデル（APIレスポンス用）
class EventItem(BaseModel):
    id: int
    user_id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True
        from_attributes = True

# Create an MCP server
mcp = FastMCP("Todo")

# Google API関連のヘルパー関数
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

@mcp.resource("echo://{message}")
def echo_resource(message: str) -> str:
    """Echo a message as a resource"""
    return f"Resource echo: {message}"


@mcp.tool()
def echo_tool(message: str) -> str:
    """Echo a message as a tool"""
    return f"Tool echo: {message}"

@mcp.prompt()
def echo_prompt(message: str) -> str:
    """Create an echo prompt"""
    return f"Please process this message: {message}"

# TODOを追加するエンドポイント
@mcp.tool()
def add_todo(user_id: str, title: str, description: str = None, sync_to_google: bool = True) -> Dict:
    """TODOアイテムを追加する
    
    Args:
        user_id: ユーザーID
        title: TODOのタイトル
        description: TODOの詳細説明（オプション）
        sync_to_google: GoogleタスクAPIとの同期を行うかどうか
        
    Returns:
        追加されたTODOアイテム
    """
    # データベースセッションを取得
    db = next(get_db())
    
    # 新しいTODOアイテムを作成
    db_todo = DBTodoItem(
        user_id=user_id,
        title=title,
        description=description,
        created_at=datetime.now()
    )
    
    # データベースに追加して保存
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    
    # Google Tasksとの同期を試行
    google_task_id = None
    if sync_to_google:
        try:
            tasks_service = get_google_tasks_service(user_id, db)
            if tasks_service:
                # デフォルトのタスクリストを取得
                tasklists = tasks_service.tasklists().list().execute()
                if tasklists.get('items'):
                    tasklist_id = tasklists['items'][0]['id']
                    
                    # Google Tasksにタスクを追加
                    task_body = {
                        'title': title,
                        'notes': description or '',
                    }
                    result = tasks_service.tasks().insert(
                        tasklist=tasklist_id,
                        body=task_body
                    ).execute()
                    google_task_id = result.get('id')
        except Exception as e:
            # Google API呼び出しでエラーが発生した場合、ログに記録するが処理は継続
            print(f"Google Tasks API error: {e}")
    
    # Pydanticモデルに変換して返す
    result = TodoItem.from_orm(db_todo).dict()
    if google_task_id:
        result['google_task_id'] = google_task_id
    return result

# 全てのTODOを取得するエンドポイント
@mcp.tool()
def get_all_todos(user_id: str, filter_status: str = "all", include_google_tasks: bool = True) -> List[Dict]:
    """ユーザーの全てのTODOアイテムを取得する
    
    Args:
        user_id: ユーザーID
        filter_status: フィルターオプション。'completed'または'active'を指定可能
        include_google_tasks: Google Tasksからのタスクも含めるかどうか
    
    Returns:
        TODOアイテムのリスト
    """
    # データベースセッションを取得
    db = next(get_db())
    
    # ユーザーのTODOを検索するクエリを作成
    query = db.query(DBTodoItem).filter(DBTodoItem.user_id == user_id)
    
    # フィルターステータスに基づいてクエリを絞り込む
    if filter_status == "completed":
        query = query.filter(DBTodoItem.completed == True)
    elif filter_status == "active":
        query = query.filter(DBTodoItem.completed == False)
    elif filter_status == "all" or filter_status is None:
        pass  # フィルタリングなし
    else:
        return {"error": f"Invalid filter status: {filter_status}. Use 'all', 'completed', or 'active'."}
    
    # クエリを実行してTODOアイテムを取得
    todos = query.all()
    result = [TodoItem.from_orm(todo).dict() for todo in todos]
    
    # Google Tasksからのタスクも取得
    if include_google_tasks:
        try:
            tasks_service = get_google_tasks_service(user_id, db)
            if tasks_service:
                # デフォルトのタスクリストを取得
                tasklists = tasks_service.tasklists().list().execute()
                if tasklists.get('items'):
                    tasklist_id = tasklists['items'][0]['id']
                    
                    # Google Tasksからタスクを取得
                    google_tasks = tasks_service.tasks().list(tasklist=tasklist_id).execute()
                    
                    for google_task in google_tasks.get('items', []):
                        # フィルターステータスに応じてGoogle Tasksをフィルタリング
                        is_completed = google_task.get('status') == 'completed'
                        
                        if filter_status == "completed" and not is_completed:
                            continue
                        elif filter_status == "active" and is_completed:
                            continue
                        
                        # Google Taskを結果に追加
                        result.append({
                            'id': f"google_{google_task.get('id')}",
                            'user_id': user_id,
                            'title': google_task.get('title', ''),
                            'description': google_task.get('notes', ''),
                            'completed': is_completed,
                            'created_at': google_task.get('updated'),
                            'source': 'google_tasks',
                            'google_task_id': google_task.get('id')
                        })
        except Exception as e:
            # Google API呼び出しでエラーが発生した場合、ログに記録するが処理は継続
            print(f"Google Tasks API error: {e}")
    
    return result

# 特定のTODOを取得するエンドポイント
@mcp.tool()
def get_todo(user_id: str, todo_id: int) -> Dict:
    """指定されたIDのTODOアイテムを取得する
    
    Args:
        user_id: ユーザーID
        todo_id: 取得するTODOのID
        
    Returns:
        TODOアイテム
    """
    # データベースセッションを取得
    db = next(get_db())
    
    # 指定されたIDのTODOを取得
    todo = db.query(DBTodoItem).filter(DBTodoItem.id == todo_id).first()
    
    # TODOが存在しない場合
    if todo is None:
        return {"error": f"Todo with ID {todo_id} not found"}
    
    # ユーザーのTODOかどうかを確認
    if todo.user_id != user_id:
        return {"error": f"Todo with ID {todo_id} not found for user {user_id}"}
    
    # Pydanticモデルに変換して返す
    return TodoItem.from_orm(todo).dict()

# TODOの完了状態を更新するエンドポイント
@mcp.tool()
def update_todo_status(user_id: str, todo_id: int, completed: bool) -> Dict:
    """TODOの完了状態を更新する
    
    Args:
        user_id: ユーザーID
        todo_id: 更新するTODOのID
        completed: 完了状態
        
    Returns:
        更新されたTODOアイテム
    """
    # データベースセッションを取得
    db = next(get_db())
    
    # 指定されたIDのTODOを取得
    todo = db.query(DBTodoItem).filter(DBTodoItem.id == todo_id).first()
    
    # TODOが存在しない場合
    if todo is None:
        return {"error": f"Todo with ID {todo_id} not found"}
    
    # ユーザーのTODOかどうかを確認
    if todo.user_id != user_id:
        return {"error": f"Todo with ID {todo_id} not found for user {user_id}"}
    
    # TODOの完了状態を更新
    todo.completed = completed
    db.commit()
    db.refresh(todo)
    
    # Pydanticモデルに変換して返す
    return TodoItem.from_orm(todo).dict()

# イベントを追加するエンドポイント
@mcp.tool()
def add_event(user_id: str, title: str, start_time: datetime, end_time: datetime, description: str = None, location: str = None, sync_to_google: bool = True) -> Dict:
    """カレンダーイベントを追加する
    
    Args:
        user_id: ユーザーID
        title: イベントのタイトル
        start_time: 開始日時
        end_time: 終了日時
        description: イベントの詳細説明（オプション）
        location: 場所（オプション）
        sync_to_google: Google CalendarAPIとの同期を行うかどうか
        
    Returns:
        追加されたイベントアイテム
    """
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

# 特定のイベントを取得するエンドポイント
@mcp.tool()
def get_event(user_id: str, event_id: int) -> Dict:
    """指定されたIDのイベントアイテムを取得する
    
    Args:
        user_id: ユーザーID
        event_id: 取得するイベントのID
        
    Returns:
        イベントアイテム
    """
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

# 全てのイベントを取得するエンドポイント
@mcp.tool()
def get_all_events(user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, include_google_calendar: bool = True) -> List[Dict]:
    """ユーザーの全てのイベントアイテムを取得する
    
    Args:
        user_id: ユーザーID
        start_date: この日時以降のイベントをフィルター（オプション）
        end_date: この日時以前のイベントをフィルター（オプション）
        include_google_calendar: Google Calendarからのイベントも含めるかどうか
    
    Returns:
        イベントアイテムのリスト
    """
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
                events_request = calendar_service.events().list(calendarId='primary')
                
                # 日付範囲でフィルタリング
                if start_date:
                    events_request = calendar_service.events().list(
                        calendarId='primary',
                        timeMin=start_date.isoformat() + 'Z'
                    )
                if end_date:
                    if start_date:
                        events_request = calendar_service.events().list(
                            calendarId='primary',
                            timeMin=start_date.isoformat() + 'Z',
                            timeMax=end_date.isoformat() + 'Z'
                        )
                    else:
                        events_request = calendar_service.events().list(
                            calendarId='primary',
                            timeMax=end_date.isoformat() + 'Z'
                        )
                
                google_events = events_request.execute()
                
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
                        result.append({
                            'id': f"google_{google_event.get('id')}",
                            'user_id': user_id,
                            'title': google_event.get('summary', ''),
                            'description': google_event.get('description', ''),
                            'start_time': start_time.isoformat(),
                            'end_time': end_time.isoformat(),
                            'location': google_event.get('location', ''),
                            'created_at': google_event.get('created'),
                            'source': 'google_calendar',
                            'google_event_id': google_event.get('id')
                        })
        except Exception as e:
            # Google API呼び出しでエラーが発生した場合、ログに記録するが処理は継続
            print(f"Google Calendar API error: {e}")
    
    # 開始時刻でソート
    result.sort(key=lambda x: x.get('start_time', ''))
    
    return result

# Google OAuth認証フローの開始
@mcp.tool()
def start_google_oauth(user_id: str, client_id: str, client_secret: str, redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob") -> Dict:
    """Google OAuth認証フローを開始する
    
    Args:
        user_id: ユーザーID
        client_id: Google OAuth クライアントID
        client_secret: Google OAuth クライアントシークレット
        redirect_uri: リダイレクトURI
        
    Returns:
        認証URL
    """
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

# Google OAuth認証フローの完了
@mcp.tool()
def complete_google_oauth(user_id: str, client_id: str, client_secret: str, auth_code: str, redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob") -> Dict:
    """Google OAuth認証フローを完了し、クレデンシャルを保存する
    
    Args:
        user_id: ユーザーID
        client_id: Google OAuth クライアントID
        client_secret: Google OAuth クライアントシークレット
        auth_code: 認証コード
        redirect_uri: リダイレクトURI
        
    Returns:
        認証結果
    """
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

# Googleクレデンシャルの状態を確認
@mcp.tool()
def check_google_credentials(user_id: str) -> Dict:
    """ユーザーのGoogleクレデンシャルの状態を確認する
    
    Args:
        user_id: ユーザーID
        
    Returns:
        クレデンシャルの状態
    """
    try:
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

if __name__ == "__main__":
    # Initialize and run the server
    import sys
    import os
    print(f"Using Python: {sys.executable}", file=sys.stderr)
    
    port = int(os.environ.get("PORT", 8000))
    
    # FastMCPのrun()メソッドは引数なしで呼び出します
    # 環境変数PORTはHerokuが自動的に設定し、サーバーが使用します
    mcp.run(transport='sse', port=port, host="0.0.0.0")