import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from todo_service import add_todo, get_all_todos, get_todo, update_todo_status
from models import TodoItem
from schemas import TodoItem as TodoItemSchema


class TestTodoService(unittest.TestCase):
    """TODOサービスのテストクラス"""

    def setUp(self):
        """テストの前準備"""
        # テスト用のユーザーID
        self.user_id = "test_user"
        
        # テスト用のTODOアイテム（SQLAlchemyモデル）
        self.test_todo = MagicMock()
        self.test_todo.id = 1
        self.test_todo.user_id = self.user_id
        self.test_todo.title = "テストタスク"
        self.test_todo.description = "テスト用のタスク説明"
        self.test_todo.completed = False
        self.test_todo.created_at = datetime.now()
        
        # モックのDBセッション
        self.mock_db = MagicMock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.test_todo
        self.mock_db.query.return_value.filter.return_value.all.return_value = [self.test_todo]
        
        # add_todoのために、db.add()を呼び出したときに、引数のオブジェクトにidとcompletedを設定する
        def mock_add(todo):
            todo.id = 1
            todo.completed = False
        self.mock_db.add.side_effect = mock_add
        
        # get_db関数のモック
        self.db_patch = patch('todo_service.get_db')
        self.mock_get_db = self.db_patch.start()
        self.mock_get_db.return_value.__next__.return_value = self.mock_db
        
        # Google Tasks APIのモック
        self.google_api_patch = patch('todo_service.get_google_tasks_service')
        self.mock_google_api = self.google_api_patch.start()
        self.mock_google_api.return_value = None  # デフォルトではGoogle APIは無効
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.db_patch.stop()
        self.google_api_patch.stop()
    
    def test_add_todo(self):
        """add_todo関数のテスト"""
        # テスト用のパラメータ
        title = "新しいタスク"
        description = "新しいタスクの説明"
        
        # Google APIを無効にしてテスト
        result = add_todo(self.user_id, title, description, sync_to_google=False)
        
        # DBに追加されたことを確認
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()
        
        # 戻り値を検証
        self.assertEqual(result["user_id"], self.user_id)
        self.assertEqual(result["title"], title)
        self.assertEqual(result["description"], description)
    
    def test_add_todo_with_google_sync(self):
        """Google同期ありのadd_todo関数のテスト"""
        # Google APIのモックを設定
        mock_tasks_service = MagicMock()
        mock_tasklists = {'items': [{'id': 'tasklist_id_1'}]}
        mock_task_result = {'id': 'google_task_id_1'}
        
        mock_tasks_service.tasklists().list().execute.return_value = mock_tasklists
        mock_tasks_service.tasks().insert().execute.return_value = mock_task_result
        self.mock_google_api.return_value = mock_tasks_service
        
        # テスト用のパラメータ
        title = "Google同期タスク"
        description = "Google同期するタスクの説明"
        
        # Google API同期ありでテスト
        result = add_todo(self.user_id, title, description, sync_to_google=True)
        
        # DBに追加されたことを確認
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()
        
        # Google APIが呼ばれたことを確認
        self.mock_google_api.assert_called_once_with(self.user_id, self.mock_db)
        
        # 戻り値を検証
        self.assertEqual(result["user_id"], self.user_id)
        self.assertEqual(result["title"], title)
        self.assertEqual(result["description"], description)
        self.assertEqual(result["google_task_id"], "google_task_id_1")
    
    def test_get_all_todos(self):
        """get_all_todos関数のテスト"""
        # Google APIを無効にしてテスト
        result = get_all_todos(self.user_id, filter_status="all", include_google_tasks=False)
        
        # クエリが実行されたことを確認
        self.mock_db.query.assert_called_once_with(TodoItem)
        
        # 戻り値を検証
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], self.test_todo.id)
        self.assertEqual(result[0]["title"], self.test_todo.title)
    
    def test_get_all_todos_with_filter(self):
        """フィルター付きのget_all_todos関数のテスト"""
        # completedフィルターでテスト
        get_all_todos(self.user_id, filter_status="completed", include_google_tasks=False)
        
        # フィルターが適用されたことを確認
        self.mock_db.query.return_value.filter.return_value.filter.assert_called_once()
        
        # activeフィルターでテスト
        self.mock_db.reset_mock()
        get_all_todos(self.user_id, filter_status="active", include_google_tasks=False)
        
        # フィルターが適用されたことを確認
        self.mock_db.query.return_value.filter.return_value.filter.assert_called_once()
    
    def test_get_all_todos_with_google_tasks(self):
        """Google Tasksを含むget_all_todos関数のテスト"""
        # Google APIのモックを設定
        mock_tasks_service = MagicMock()
        mock_tasklists = {'items': [{'id': 'tasklist_id_1'}]}
        mock_tasks = {
            'items': [
                {
                    'id': 'google_task_id_1',
                    'title': 'Googleタスク1',
                    'notes': 'Googleタスクの説明',
                    'status': 'needsAction',
                    'updated': '2025-06-05T00:00:00Z'
                }
            ]
        }
        
        mock_tasks_service.tasklists().list().execute.return_value = mock_tasklists
        mock_tasks_service.tasks().list().execute.return_value = mock_tasks
        self.mock_google_api.return_value = mock_tasks_service
        
        # Google Tasks含めてテスト
        result = get_all_todos(self.user_id, filter_status="all", include_google_tasks=True)
        
        # Google APIが呼ばれたことを確認
        self.mock_google_api.assert_called_once_with(self.user_id, self.mock_db)
        
        # 戻り値を検証
        self.assertEqual(len(result), 2)  # ローカルの1件 + Googleの1件
        self.assertEqual(result[1]["id"], "google_google_task_id_1")
        self.assertEqual(result[1]["title"], "Googleタスク1")
        self.assertEqual(result[1]["source"], "google_tasks")
    
    def test_get_todo(self):
        """get_todo関数のテスト"""
        # 存在するTODOを取得
        result = get_todo(self.user_id, 1)
        
        # クエリが実行されたことを確認
        self.mock_db.query.assert_called_once_with(TodoItem)
        
        # 戻り値を検証
        self.assertEqual(result["id"], self.test_todo.id)
        self.assertEqual(result["title"], self.test_todo.title)
    
    def test_get_todo_not_found(self):
        """存在しないTODOを取得するテスト"""
        # モックを設定して存在しないケースをシミュレート
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 存在しないTODOを取得
        result = get_todo(self.user_id, 999)
        
        # エラーメッセージを検証
        self.assertIn("error", result)
        self.assertIn("not found", result["error"])
    
    def test_get_todo_wrong_user(self):
        """別ユーザーのTODOを取得するテスト"""
        # 別のユーザーIDでテスト
        result = get_todo("wrong_user", 1)
        
        # エラーメッセージを検証
        self.assertIn("error", result)
        self.assertIn("not found for user", result["error"])
    
    def test_update_todo_status(self):
        """update_todo_status関数のテスト"""
        # TODOのステータスを更新
        result = update_todo_status(self.user_id, 1, True)
        
        # クエリが実行されたことを確認
        self.mock_db.query.assert_called_once_with(TodoItem)
        
        # TODOが更新されたことを確認
        self.assertEqual(self.test_todo.completed, True)
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()
        
        # 戻り値を検証
        self.assertEqual(result["id"], self.test_todo.id)
        self.assertEqual(result["completed"], True)
    
    def test_update_todo_status_not_found(self):
        """存在しないTODOのステータスを更新するテスト"""
        # モックを設定して存在しないケースをシミュレート
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 存在しないTODOを更新
        result = update_todo_status(self.user_id, 999, True)
        
        # エラーメッセージを検証
        self.assertIn("error", result)
        self.assertIn("not found", result["error"])
    
    def test_update_todo_status_wrong_user(self):
        """別ユーザーのTODOのステータスを更新するテスト"""
        # 別のユーザーIDでテスト
        result = update_todo_status("wrong_user", 1, True)
        
        # エラーメッセージを検証
        self.assertIn("error", result)
        self.assertIn("not found for user", result["error"])


if __name__ == "__main__":
    unittest.main()
