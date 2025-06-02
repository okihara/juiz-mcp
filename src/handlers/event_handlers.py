from typing import Dict, List, Optional
from datetime import datetime
from src.services import EventService
from src.core import logger

class EventHandlers:
    """FastMCP handlers for Event operations"""
    
    def __init__(self):
        self.event_service = EventService()
    
    def add_event(self, user_id: str, title: str, start_time: datetime, end_time: datetime, 
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
        logger.info(f"Adding Event for user {user_id}: {title}")
        result = self.event_service.create_event(user_id, title, start_time, end_time, description, location)
        
        # Return the data directly for MCP compatibility
        if result.get("success"):
            return result["data"]
        else:
            return {"error": result.get("error", "Unknown error")}
    
    def get_event(self, user_id: str, event_id: int) -> Dict:
        """指定されたIDのイベントアイテムを取得する
        
        Args:
            user_id: ユーザーID
            event_id: 取得するイベントのID
            
        Returns:
            イベントアイテム
        """
        logger.info(f"Getting Event {event_id} for user {user_id}")
        result = self.event_service.get_event(user_id, event_id)
        
        if result.get("success"):
            return result["data"]
        else:
            return {"error": result.get("error", "Unknown error")}
    
    def get_all_events(self, user_id: str, start_date: Optional[datetime] = None, 
                      end_date: Optional[datetime] = None) -> List[Dict]:
        """ユーザーの全てのイベントアイテムを取得する
        
        Args:
            user_id: ユーザーID
            start_date: この日時以降のイベントをフィルター（オプション）
            end_date: この日時以前のイベントをフィルター（オプション）
        
        Returns:
            イベントアイテムのリスト
        """
        logger.info(f"Getting all Events for user {user_id}")
        result = self.event_service.get_all_events(user_id, start_date, end_date)
        
        if result.get("success"):
            return result["data"]
        else:
            return {"error": result.get("error", "Unknown error")}