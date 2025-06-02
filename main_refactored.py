import sys
import os
from fastmcp.server import FastMCP
from typing import List, Dict, Optional
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import settings
from src.core import logger
from src.handlers import TodoHandlers, EventHandlers

# Create an MCP server
mcp = FastMCP("Todo")

# Initialize handlers
todo_handlers = TodoHandlers()
event_handlers = EventHandlers()

# Echo endpoints (keeping original functionality)
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

# TODO endpoints
@mcp.tool()
def add_todo(user_id: str, title: str, description: str = None) -> Dict:
    """TODOアイテムを追加する
    
    Args:
        user_id: ユーザーID
        title: TODOのタイトル
        description: TODOの詳細説明（オプション）
        
    Returns:
        追加されたTODOアイテム
    """
    return todo_handlers.add_todo(user_id, title, description)

@mcp.tool()
def get_all_todos(user_id: str, filter_status: str = "all") -> List[Dict]:
    """ユーザーの全てのTODOアイテムを取得する
    
    Args:
        user_id: ユーザーID
        filter_status: フィルターオプション。'completed'または'active'を指定可能
    
    Returns:
        TODOアイテムのリスト
    """
    return todo_handlers.get_all_todos(user_id, filter_status)

@mcp.tool()
def get_todo(user_id: str, todo_id: int) -> Dict:
    """指定されたIDのTODOアイテムを取得する
    
    Args:
        user_id: ユーザーID
        todo_id: 取得するTODOのID
        
    Returns:
        TODOアイテム
    """
    return todo_handlers.get_todo(user_id, todo_id)

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
    return todo_handlers.update_todo_status(user_id, todo_id, completed)

# Event endpoints
@mcp.tool()
def add_event(user_id: str, title: str, start_time: datetime, end_time: datetime, 
             description: str = None, location: str = None) -> Dict:
    """カレンダーイベントを追加する
    
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
    return event_handlers.add_event(user_id, title, start_time, end_time, description, location)

@mcp.tool()
def get_event(user_id: str, event_id: int) -> Dict:
    """指定されたIDのイベントアイテムを取得する
    
    Args:
        user_id: ユーザーID
        event_id: 取得するイベントのID
        
    Returns:
        イベントアイテム
    """
    return event_handlers.get_event(user_id, event_id)

@mcp.tool()
def get_all_events(user_id: str, start_date: Optional[datetime] = None, 
                  end_date: Optional[datetime] = None) -> List[Dict]:
    """ユーザーの全てのイベントアイテムを取得する
    
    Args:
        user_id: ユーザーID
        start_date: この日時以降のイベントをフィルター（オプション）
        end_date: この日時以前のイベントをフィルター（オプション）
    
    Returns:
        イベントアイテムのリスト
    """
    return event_handlers.get_all_events(user_id, start_date, end_date)

if __name__ == "__main__":
    # Initialize and run the server
    logger.info(f"Using Python: {sys.executable}")
    logger.info(f"Starting Juiz MCP server on {settings.host}:{settings.port}")
    
    # FastMCPのrun()メソッドは引数なしで呼び出します
    # 環境変数PORTはHerokuが自動的に設定し、サーバーが使用します
    mcp.run(transport='sse', port=settings.port, host=settings.host)