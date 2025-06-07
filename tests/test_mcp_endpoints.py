import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from datetime import datetime
import json

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    add_todo_endpoint, get_all_todos_endpoint, get_todo_endpoint, update_todo_status_endpoint,
    add_event_endpoint, get_event_endpoint, get_all_events_endpoint,
    start_google_oauth_endpoint, complete_google_oauth_endpoint, check_google_credentials_endpoint
)


class TestMCPEndpoints(unittest.TestCase):
    """MCPエンドポイントのテストクラス"""

    def setUp(self):
        """テストの前準備"""
        # テスト用のユーザーID
        self.user_id = "test_user"
        
        # テスト用のTODOアイテム
        self.test_todo = {
            "id": 1,
            "user_id": self.user_id,
            "title": "テストタスク",
            "description": "テスト用のタスク説明",
            "completed": False,
            "created_at": datetime.now().isoformat()
        }
        
        # テスト用のイベントアイテム
        self.test_event = {
            "id": 1,
            "user_id": self.user_id,
            "title": "テストイベント",
            "description": "テスト用のイベント説明",
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "location": "テスト会場",
            "created_at": datetime.now().isoformat()
        }
        
        # テスト用のGoogleクレデンシャル
        self.test_credentials = {
            "user_id": self.user_id,
            "has_credentials": True,
            "scopes": ["https://www.googleapis.com/auth/tasks", "https://www.googleapis.com/auth/calendar"]
        }
    
    @patch('main.add_todo')
    def test_add_todo_endpoint(self, mock_add_todo):
        """add_todo_endpointのテスト"""
        # モックの戻り値を設定
        mock_add_todo.return_value = self.test_todo
        
        # エンドポイントを呼び出し
        result = add_todo_endpoint(
            user_id=self.user_id,
            title="テストタスク",
            description="テスト用のタスク説明",
            sync_to_google=False
        )
        
        # モック関数が正しく呼ばれたことを確認
        mock_add_todo.assert_called_once_with(
            self.user_id, "テストタスク", "テスト用のタスク説明", False
        )
        
        # 戻り値を検証
        self.assertEqual(result, self.test_todo)
    
    @patch('main.get_all_todos')
    def test_get_all_todos_endpoint(self, mock_get_all_todos):
        """get_all_todos_endpointのテスト"""
        # モックの戻り値を設定
        mock_get_all_todos.return_value = [self.test_todo]
        
        # エンドポイントを呼び出し
        result = get_all_todos_endpoint(
            user_id=self.user_id,
            filter_status="all",
            include_google_tasks=True
        )
        
        # モック関数が正しく呼ばれたことを確認
        mock_get_all_todos.assert_called_once_with(
            self.user_id, "all", True
        )
        
        # 戻り値を検証
        self.assertEqual(result, [self.test_todo])
    
    @patch('main.get_todo')
    def test_get_todo_endpoint(self, mock_get_todo):
        """get_todo_endpointのテスト"""
        # モックの戻り値を設定
        mock_get_todo.return_value = self.test_todo
        
        # エンドポイントを呼び出し
        result = get_todo_endpoint(
            user_id=self.user_id,
            todo_id=1
        )
        
        # モック関数が正しく呼ばれたことを確認
        mock_get_todo.assert_called_once_with(self.user_id, 1)
        
        # 戻り値を検証
        self.assertEqual(result, self.test_todo)
    
    @patch('main.update_todo_status')
    def test_update_todo_status_endpoint(self, mock_update_todo_status):
        """update_todo_status_endpointのテスト"""
        # 更新後のTODOを作成
        updated_todo = self.test_todo.copy()
        updated_todo["completed"] = True
        
        # モックの戻り値を設定
        mock_update_todo_status.return_value = updated_todo
        
        # エンドポイントを呼び出し
        result = update_todo_status_endpoint(
            user_id=self.user_id,
            todo_id=1,
            completed=True
        )
        
        # モック関数が正しく呼ばれたことを確認
        mock_update_todo_status.assert_called_once_with(self.user_id, 1, True)
        
        # 戻り値を検証
        self.assertEqual(result, updated_todo)
        self.assertTrue(result["completed"])
    
    @patch('main.add_event')
    def test_add_event_endpoint(self, mock_add_event):
        """add_event_endpointのテスト"""
        # モックの戻り値を設定
        mock_add_event.return_value = self.test_event
        
        # テスト用の日時
        start_time = datetime.now()
        end_time = datetime.now()
        
        # エンドポイントを呼び出し
        result = add_event_endpoint(
            user_id=self.user_id,
            title="テストイベント",
            start_time=start_time,
            end_time=end_time,
            description="テスト用のイベント説明",
            location="テスト会場",
            sync_to_google=False
        )
        
        # モック関数が正しく呼ばれたことを確認
        mock_add_event.assert_called_once_with(
            self.user_id, "テストイベント", start_time, end_time,
            "テスト用のイベント説明", "テスト会場", False
        )
        
        # 戻り値を検証
        self.assertEqual(result, self.test_event)
    
    @patch('main.get_event')
    def test_get_event_endpoint(self, mock_get_event):
        """get_event_endpointのテスト"""
        # モックの戻り値を設定
        mock_get_event.return_value = self.test_event
        
        # エンドポイントを呼び出し
        result = get_event_endpoint(
            user_id=self.user_id,
            event_id=1
        )
        
        # モック関数が正しく呼ばれたことを確認
        mock_get_event.assert_called_once_with(self.user_id, 1)
        
        # 戻り値を検証
        self.assertEqual(result, self.test_event)
    
    @patch('main.get_all_events')
    def test_get_all_events_endpoint(self, mock_get_all_events):
        """get_all_events_endpointのテスト"""
        # モックの戻り値を設定
        mock_get_all_events.return_value = [self.test_event]
        
        # テスト用の日時
        start_date = datetime.now()
        end_date = datetime.now()
        
        # エンドポイントを呼び出し
        result = get_all_events_endpoint(
            user_id=self.user_id,
            start_date=start_date,
            end_date=end_date,
            include_google_calendar=True
        )
        
        # モック関数が正しく呼ばれたことを確認
        mock_get_all_events.assert_called_once_with(
            self.user_id, start_date, end_date, True
        )
        
        # 戻り値を検証
        self.assertEqual(result, [self.test_event])
    
    @patch('main.start_google_oauth')
    def test_start_google_oauth_endpoint(self, mock_start_google_oauth):
        """start_google_oauth_endpointのテスト"""
        # モックの戻り値を設定
        auth_url = {"auth_url": "https://accounts.google.com/o/oauth2/auth?..."}
        mock_start_google_oauth.return_value = auth_url
        
        # エンドポイントを呼び出し
        result = start_google_oauth_endpoint(
            user_id=self.user_id,
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="urn:ietf:wg:oauth:2.0:oob"
        )
        
        # モック関数が正しく呼ばれたことを確認
        mock_start_google_oauth.assert_called_once_with(
            self.user_id, "test_client_id", "test_client_secret", "urn:ietf:wg:oauth:2.0:oob"
        )
        
        # 戻り値を検証
        self.assertEqual(result, auth_url)
    
    @patch('main.complete_google_oauth')
    def test_complete_google_oauth_endpoint(self, mock_complete_google_oauth):
        """complete_google_oauth_endpointのテスト"""
        # モックの戻り値を設定
        auth_result = {"success": True, "message": "認証が完了しました"}
        mock_complete_google_oauth.return_value = auth_result
        
        # エンドポイントを呼び出し
        result = complete_google_oauth_endpoint(
            user_id=self.user_id,
            client_id="test_client_id",
            client_secret="test_client_secret",
            auth_code="test_auth_code",
            redirect_uri="urn:ietf:wg:oauth:2.0:oob"
        )
        
        # モック関数が正しく呼ばれたことを確認
        mock_complete_google_oauth.assert_called_once_with(
            self.user_id, "test_client_id", "test_client_secret", "test_auth_code", "urn:ietf:wg:oauth:2.0:oob"
        )
        
        # 戻り値を検証
        self.assertEqual(result, auth_result)
    
    @patch('main.check_google_credentials')
    def test_check_google_credentials_endpoint(self, mock_check_google_credentials):
        """check_google_credentials_endpointのテスト"""
        # モックの戻り値を設定
        mock_check_google_credentials.return_value = self.test_credentials
        
        # エンドポイントを呼び出し
        result = check_google_credentials_endpoint(
            user_id=self.user_id
        )
        
        # モック関数が正しく呼ばれたことを確認
        mock_check_google_credentials.assert_called_once_with(self.user_id)
        
        # 戻り値を検証
        self.assertEqual(result, self.test_credentials)


if __name__ == "__main__":
    unittest.main()
