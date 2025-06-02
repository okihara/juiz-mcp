# Todo アプリケーション

このプロジェクトはFastMCPを使用したTodoアプリケーションです。

## 機能

- TODOアイテムの追加
- TODOアイテムの一覧表示（全て、完了済み、未完了でフィルタリング可能）
- TODOアイテムの詳細表示
- TODOアイテムの完了状態の更新

## 技術スタック

- FastMCP: APIサーバーフレームワーク
- FastAPI: RESTful APIフレームワーク
- SQLAlchemy: ORMライブラリ
- PostgreSQL: リモートデータベース
- Alembic: データベースマイグレーションツール

## セットアップ

### 環境変数

`.env`ファイルを作成し、以下の環境変数を設定してください：

```env
DATABASE_URL=postgres://ua458rg90o90bh:pa2aa8916ddecf284f926e16cd0b191dd8e9af8a61cee24efae1eb9a639d5f5dc@c8m0261h0c7idk.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d36v41fd01afup
```

### 依存関係のインストール

```bash
pip install -r requirements.txt
```

### サーバーの起動

```bash
python main.py
```

デフォルトでは、サーバーは`http://0.0.0.0:8000`で起動します。

## データベース操作

### リモートデータベースの情報

- データベースタイプ: PostgreSQL
- ホスト: c8m0261h0c7idk.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com
- ポート: 5432
- データベース名: d36v41fd01afup
- ユーザー名: ua458rg90o90bh

### データベース内容の確認方法

#### テーブル一覧の表示

```bash
psql $DATABASE_URL -c "\dt"
```

#### todosテーブルの内容表示

```bash
psql $DATABASE_URL -c "SELECT * FROM todos;"
```

#### 特定のユーザーのTODOを表示

```bash
psql $DATABASE_URL -c "SELECT * FROM todos WHERE user_id = '1234';"
```

#### 完了済みのTODOを表示

```bash
psql $DATABASE_URL -c "SELECT * FROM todos WHERE completed = TRUE;"
```

#### 未完了のTODOを表示

```bash
psql $DATABASE_URL -c "SELECT * FROM todos WHERE completed = FALSE;"
```

### データベースの現在の内容

現在、todosテーブルには以下のレコードが存在しています：

1. ID: 1
   - ユーザーID: 1234
   - タイトル: 牛乳を買う
   - 説明: なし
   - 完了状態: 未完了
   - 作成日時: 2025-05-04 13:25:47

2. ID: 2
   - ユーザーID: 1234
   - タイトル: 映画パルプフィクションを見る
   - 説明: なし
   - 完了状態: 未完了
   - 作成日時: 2025-05-04 13:32:03

## APIエンドポイント

### TODOの追加

```python
@mcp.tool()
def add_todo(user_id: str, title: str, description: str = None) -> Dict
```

### TODOの一覧取得

```python
@mcp.tool()
def get_all_todos(user_id: str, filter_status: str = "all") -> List[Dict]
```

### 特定のTODOの取得

```python
@mcp.tool()
def get_todo(user_id: str, todo_id: int) -> Dict
```

### TODOの完了状態の更新

```python
@mcp.tool()
def update_todo_status(user_id: str, todo_id: int, completed: bool) -> Dict
```

## マイグレーション

このプロジェクトではAlembicを使用してデータベースマイグレーションを管理しています。現在のマイグレーションバージョンは `1dc9901c0158` です。
