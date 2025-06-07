#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# テストモジュールをインポート
from tests.test_todo_service import TestTodoService
from tests.test_mcp_endpoints import TestMCPEndpoints

if __name__ == "__main__":
    # テストスイートを作成
    test_suite = unittest.TestSuite()
    
    # テストクラスをスイートに追加
    test_suite.addTest(unittest.makeSuite(TestTodoService))
    test_suite.addTest(unittest.makeSuite(TestMCPEndpoints))
    
    # テストランナーを作成して実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 終了コードを設定（テスト失敗があれば1、なければ0）
    sys.exit(not result.wasSuccessful())
