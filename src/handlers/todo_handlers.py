from typing import Dict, List
from src.services import TodoService
from src.core import logger

class TodoHandlers:
    """FastMCP handlers for TODO operations"""
    
    def __init__(self):
        self.todo_service = TodoService()
    
    def add_todo(self, user_id: str, title: str, description: str = None) -> Dict:
        """TODOアイテムを追加する
        
        Args:
            user_id: ユーザーID
            title: TODOのタイトル
            description: TODOの詳細説明（オプション）
            
        Returns:
            追加されたTODOアイテム
        """
        logger.info(f"Adding TODO for user {user_id}: {title}")
        result = self.todo_service.create_todo(user_id, title, description)
        
        # Return the data directly for MCP compatibility
        if result.get("success"):
            return result["data"]
        else:
            return {"error": result.get("error", "Unknown error")}
    
    def get_todo(self, user_id: str, todo_id: int) -> Dict:
        """指定されたIDのTODOアイテムを取得する
        
        Args:
            user_id: ユーザーID
            todo_id: 取得するTODOのID
            
        Returns:
            TODOアイテム
        """
        logger.info(f"Getting TODO {todo_id} for user {user_id}")
        result = self.todo_service.get_todo(user_id, todo_id)
        
        if result.get("success"):
            return result["data"]
        else:
            return {"error": result.get("error", "Unknown error")}
    
    def get_all_todos(self, user_id: str, filter_status: str = "all") -> List[Dict]:
        """ユーザーの全てのTODOアイテムを取得する
        
        Args:
            user_id: ユーザーID
            filter_status: フィルターオプション。'completed'または'active'を指定可能
        
        Returns:
            TODOアイテムのリスト
        """
        logger.info(f"Getting all TODOs for user {user_id} with filter {filter_status}")
        result = self.todo_service.get_all_todos(user_id, filter_status)
        
        if result.get("success"):
            return result["data"]
        else:
            return {"error": result.get("error", "Unknown error")}
    
    def update_todo_status(self, user_id: str, todo_id: int, completed: bool) -> Dict:
        """TODOの完了状態を更新する
        
        Args:
            user_id: ユーザーID
            todo_id: 更新するTODOのID
            completed: 完了状態
            
        Returns:
            更新されたTODOアイテム
        """
        logger.info(f"Updating TODO {todo_id} status to {completed} for user {user_id}")
        result = self.todo_service.update_todo_status(user_id, todo_id, completed)
        
        if result.get("success"):
            return result["data"]
        else:
            return {"error": result.get("error", "Unknown error")}