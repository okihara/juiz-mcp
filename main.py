
from fastmcp.server import FastMCP
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
from models import TodoItem as DBTodoItem, EventItem as DBEventItem, GoogleCredentials, get_db
import os

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
def add_todo(user_id: str, title: str, description: str = None) -> Dict:
    """TODOアイテムを追加する（Google Tasks連携対応）
    
    Args:
        user_id: ユーザーID
        title: TODOのタイトル
        description: TODOの詳細説明（オプション）
        
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
    
    from google_services import get_google_credentials, sync_todo_to_google_tasks
    creds = get_google_credentials(db, user_id)
    if creds:
        try:
            sync_todo_to_google_tasks(creds, title, description)
        except Exception as e:
            print(f"Google Tasks sync failed: {e}")
    
    # Pydanticモデルに変換して返す
    return TodoItem.from_orm(db_todo).dict()

# 全てのTODOを取得するエンドポイント
@mcp.tool()
def get_all_todos(user_id: str, filter_status: str = "all") -> List[Dict]:
    """ユーザーの全てのTODOアイテムを取得する
    
    Args:
        user_id: ユーザーID
        filter_status: フィルターオプション。'completed'または'active'を指定可能
    
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
    
    # Pydanticモデルに変換して返す
    return [TodoItem.from_orm(todo).dict() for todo in todos]

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
def add_event(user_id: str, title: str, start_time: datetime, end_time: datetime, description: str = None, location: str = None) -> Dict:
    """カレンダーイベントを追加する（Google Calendar連携対応）
    
    Args:
        user_id: ユーザーID
        title: イベントのタイトル
        start_time: 開始日時
        end_time: 終了日時
        description: イベントの詳細説明（オプション）
        location: 場所（オプション）
        
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
    
    from google_services import get_google_credentials, sync_event_to_google_calendar
    creds = get_google_credentials(db, user_id)
    if creds:
        try:
            sync_event_to_google_calendar(creds, title, start_time, end_time, description, location)
        except Exception as e:
            print(f"Google Calendar sync failed: {e}")
    
    # Pydanticモデルに変換して返す
    return EventItem.from_orm(db_event).dict()

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
def get_all_events(user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict]:
    """ユーザーの全てのイベントアイテムを取得する
    
    Args:
        user_id: ユーザーID
        start_date: この日時以降のイベントをフィルター（オプション）
        end_date: この日時以前のイベントをフィルター（オプション）
    
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
    
    # Pydanticモデルに変換して返す
    return [EventItem.from_orm(event).dict() for event in events]

@mcp.tool()
def store_google_credentials(user_id: str, access_token: str, refresh_token: str, token_expiry: datetime = None) -> Dict:
    """Google認証情報を保存する
    
    Args:
        user_id: ユーザーID
        access_token: アクセストークン
        refresh_token: リフレッシュトークン
        token_expiry: トークン有効期限
        
    Returns:
        保存結果
    """
    db = next(get_db())
    
    existing_creds = db.query(GoogleCredentials).filter(GoogleCredentials.user_id == user_id).first()
    
    if existing_creds:
        existing_creds.access_token = access_token
        existing_creds.refresh_token = refresh_token
        existing_creds.token_expiry = token_expiry
        existing_creds.updated_at = datetime.now()
    else:
        new_creds = GoogleCredentials(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=token_expiry,
            created_at=datetime.now()
        )
        db.add(new_creds)
    
    db.commit()
    return {"status": "success", "message": "Google credentials stored successfully"}

@mcp.tool()
def check_google_integration(user_id: str) -> Dict:
    """ユーザーのGoogle連携状態を確認する
    
    Args:
        user_id: ユーザーID
        
    Returns:
        連携状態
    """
    db = next(get_db())
    creds = db.query(GoogleCredentials).filter(GoogleCredentials.user_id == user_id).first()
    
    return {
        "google_integrated": creds is not None,
        "last_updated": creds.updated_at.isoformat() if creds else None
    }

if __name__ == "__main__":
    # Initialize and run the server
    import sys
    import os
    print(f"Using Python: {sys.executable}", file=sys.stderr)
    
    port = int(os.environ.get("PORT", 8000))
    
    # FastMCPのrun()メソッドは引数なしで呼び出します
    # 環境変数PORTはHerokuが自動的に設定し、サーバーが使用します
    mcp.run(transport='sse', port=port, host="0.0.0.0")
