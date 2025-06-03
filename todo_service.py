from typing import List, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from models import TodoItem as DBTodoItem, get_db
from schemas import TodoItem
from google_api import get_google_tasks_service


def add_todo(user_id: str, title: str, description: str = None, sync_to_google: bool = True) -> Dict:
    """TODOアイテムを追加する"""
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


def get_all_todos(user_id: str, filter_status: str = "all", include_google_tasks: bool = True) -> List[Dict]:
    """ユーザーの全てのTODOアイテムを取得する"""
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


def get_todo(user_id: str, todo_id: int) -> Dict:
    """指定されたIDのTODOアイテムを取得する"""
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


def update_todo_status(user_id: str, todo_id: int, completed: bool) -> Dict:
    """TODOの完了状態を更新する"""
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