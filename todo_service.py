from typing import List, Dict
from models import get_db
from google_api import get_google_tasks_service


def _get_default_tasklist_id(tasks_service) -> str:
    """デフォルトのタスクリストIDを取得するヘルパー関数"""
    tasklists = tasks_service.tasklists().list().execute()
    if tasklists.get('items'):
        return tasklists['items'][0]['id']
    raise ValueError("No tasklists found")


def _create_task_dict(google_task: Dict, user_id: str) -> Dict:
    """Google TaskからTODO辞書を作成するヘルパー関数"""
    return {
        'id': f"google_{google_task.get('id')}",
        'user_id': user_id,
        'title': google_task.get('title', ''),
        'description': google_task.get('notes', ''),
        'completed': google_task.get('status') == 'completed',
        'created_at': google_task.get('updated'),
        'source': 'google_tasks',
        'google_task_id': google_task.get('id')
    }


def add_todo(user_id: str, title: str, description: str = None) -> Dict:
    """Google TasksにTODOアイテムを追加する"""
    # データベースセッションを取得
    db = next(get_db())
    
    try:
        tasks_service = get_google_tasks_service(user_id, db)
        if tasks_service:
            tasklist_id = _get_default_tasklist_id(tasks_service)
            if tasklist_id:
                # Google Tasksにタスクを追加
                task_body = {
                    'title': title,
                    'notes': description or '',
                }
                result = tasks_service.tasks().insert(
                    tasklist=tasklist_id,
                    body=task_body
                ).execute()
                
                return _create_task_dict(result, user_id)
        return {"error": "Google Tasks service not available"}
    except Exception as e:
        return {"error": f"Google Tasks API error: {e}"}


def get_all_todos(user_id: str, filter_status: str = "all") -> List[Dict]:
    """Google TasksからTODOアイテムを取得する"""
    # データベースセッションを取得
    db = next(get_db())
    
    result = []
    
    try:
        tasks_service = get_google_tasks_service(user_id, db)
        if tasks_service:
            tasklist_id = _get_default_tasklist_id(tasks_service)
            if tasklist_id:
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
                    result.append(_create_task_dict(google_task, user_id))
    except Exception as e:
        # Google API呼び出しでエラーが発生した場合、ログに記録するが処理は継続
        print(f"Google Tasks API error: {e}")
    
    return result


def get_todo(user_id: str, todo_id: str) -> Dict:
    """指定されたIDのTODOアイテムをGoogle Tasksから取得する"""
    # データベースセッションを取得
    db = next(get_db())
    
    # Google Task IDを抽出（「google_」プレフィックスを削除）
    google_task_id = todo_id.replace('google_', '') if todo_id.startswith('google_') else todo_id
    
    try:
        tasks_service = get_google_tasks_service(user_id, db)
        if tasks_service:
            tasklist_id = _get_default_tasklist_id(tasks_service)
            if tasklist_id:
                # 指定されたIDのタスクを取得
                google_task = tasks_service.tasks().get(
                    tasklist=tasklist_id,
                    task=google_task_id
                ).execute()
                
                return _create_task_dict(google_task, user_id)
        return {"error": "Google Tasks service not available"}
    except Exception as e:
        return {"error": f"Todo with ID {todo_id} not found: {e}"}


def update_todo_status(user_id: str, todo_id: str, completed: bool) -> Dict:
    """Google TasksでTODOの完了状態を更新する"""
    # データベースセッションを取得
    db = next(get_db())
    
    # Google Task IDを抽出（「google_」プレフィックスを削除）
    google_task_id = todo_id.replace('google_', '') if todo_id.startswith('google_') else todo_id
    
    try:
        tasks_service = get_google_tasks_service(user_id, db)
        if tasks_service:
            tasklist_id = _get_default_tasklist_id(tasks_service)
            if tasklist_id:
                # タスクの完了状態を更新
                task_body = {
                    'status': 'completed' if completed else 'needsAction'
                }
                
                updated_task = tasks_service.tasks().patch(
                    tasklist=tasklist_id,
                    task=google_task_id,
                    body=task_body
                ).execute()
                
                return _create_task_dict(updated_task, user_id)
        return {"error": "Google Tasks service not available"}
    except Exception as e:
        return {"error": f"Failed to update todo with ID {todo_id}: {e}"}