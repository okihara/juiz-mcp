from fastmcp.server import FastMCP
from typing import List, Dict, Optional
from datetime import datetime
import sys
import os

# Import service modules
from todo_service import add_todo, get_all_todos, get_todo, update_todo_status
from event_service import add_event, get_event, get_all_events

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


# TODO関連のエンドポイント
@mcp.tool()
def add_todo_endpoint(user_id: str, title: str, description: str = None, sync_to_google: bool = True) -> Dict:
    """TODOアイテムを追加する
    
    Args:
        user_id: ユーザーID
        title: TODOのタイトル
        description: TODOの詳細説明（オプション）
        sync_to_google: GoogleタスクAPIとの同期を行うかどうか
        
    Returns:
        追加されたTODOアイテム
    """
    return add_todo(user_id, title, description, sync_to_google)


@mcp.tool()
def get_all_todos_endpoint(user_id: str, filter_status: str = "all", include_google_tasks: bool = True) -> List[Dict]:
    """ユーザーの全てのTODOアイテムを取得する
    
    Args:
        user_id: ユーザーID
        filter_status: フィルターオプション。'completed'または'active'を指定可能
        include_google_tasks: Google Tasksからのタスクも含めるかどうか
    
    Returns:
        TODOアイテムのリスト
    """
    return get_all_todos(user_id, filter_status, include_google_tasks)


@mcp.tool()
def get_todo_endpoint(user_id: str, todo_id: int) -> Dict:
    """指定されたIDのTODOアイテムを取得する
    
    Args:
        user_id: ユーザーID
        todo_id: 取得するTODOのID
        
    Returns:
        TODOアイテム
    """
    return get_todo(user_id, todo_id)


@mcp.tool()
def update_todo_status_endpoint(user_id: str, todo_id: int, completed: bool) -> Dict:
    """TODOの完了状態を更新する
    
    Args:
        user_id: ユーザーID
        todo_id: 更新するTODOのID
        completed: 完了状態
        
    Returns:
        更新されたTODOアイテム
    """
    return update_todo_status(user_id, todo_id, completed)


# イベント関連のエンドポイント
@mcp.tool()
def add_event_endpoint(user_id: str, title: str, start_time: datetime, end_time: datetime, description: str = None, location: str = None, sync_to_google: bool = True) -> Dict:
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
    return add_event(user_id, title, start_time, end_time, description, location, sync_to_google)


@mcp.tool()
def get_event_endpoint(user_id: str, event_id: int) -> Dict:
    """指定されたIDのイベントアイテムを取得する
    
    Args:
        user_id: ユーザーID
        event_id: 取得するイベントのID
        
    Returns:
        イベントアイテム
    """
    return get_event(user_id, event_id)


@mcp.tool()
def get_all_events_endpoint(user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, include_google_calendar: bool = True) -> List[Dict]:
    """ユーザーの全てのイベントアイテムを取得する
    
    Args:
        user_id: ユーザーID
        start_date: この日時以降のイベントをフィルター（オプション）
        end_date: この日時以前のイベントをフィルター（オプション）
        include_google_calendar: Google Calendarからのイベントも含めるかどうか
    
    Returns:
        イベントアイテムのリスト
    """
    return get_all_events(user_id, start_date, end_date, include_google_calendar)


if __name__ == "__main__":
    # Initialize and run the server
    print(f"Using Python: {sys.executable}", file=sys.stderr)
    
    port = int(os.environ.get("PORT", 8000))
    
    # FastMCPのrun()メソッドは引数なしで呼び出します
    # 環境変数PORTはHerokuが自動的に設定し、サーバーが使用します
    mcp.run(transport='sse', port=port, host="0.0.0.0")