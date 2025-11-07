# Google ADK セッションストレージのカスタマイズ調査レポート

**調査日**: 2025年11月7日
**質問**: Google ADKのSession機能は、ローカルファイル保存以外に読み書き先を変更できるか？

---

## 結論

**はい、変更可能です。** Google ADKは複数のSessionService実装を提供しており、カスタムストレージバックエンドの実装もサポートしています。

---

## 1. 標準で提供されているSessionService

ADKには以下の3つのSessionService実装が標準で含まれています：

### 1.1 InMemorySessionService

**特徴**:
- アプリケーションのメモリ内にセッションデータを保存
- 永続化なし（アプリ再起動でデータ消失）
- **用途**: 開発、テスト、短期的なデモ

**メリット**:
- ✅ 最も高速
- ✅ セットアップ不要

**デメリット**:
- ❌ 永続化されない
- ❌ スケールアウト不可（単一インスタンスのみ）

### 1.2 VertexAiSessionService

**特徴**:
- Google Cloud Vertex AIインフラをAPI経由で使用
- クラウドベースの永続ストレージ
- **用途**: 本番環境、スケーラブルなアプリケーション

**メリット**:
- ✅ 完全マネージド
- ✅ 自動スケーリング
- ✅ 高可用性

**デメリット**:
- ❌ Google Cloudへの依存
- ❌ API呼び出しコスト
- ❌ レイテンシー（外部API呼び出し）

### 1.3 DatabaseSessionService

**特徴**:
- リレーショナルデータベース（PostgreSQL、MySQL、SQLite）に接続
- 自管理型の永続ストレージ
- **用途**: 既存DBインフラを活用したい場合

**メリット**:
- ✅ 自管理による柔軟性
- ✅ 既存インフラの活用
- ✅ SQLベースのクエリ可能

**デメリット**:
- ❌ DB管理が必要
- ❌ スケーリングに工夫が必要

---

## 2. カスタムストレージバックエンド（Redis / Firestore）

### 2.1 RedisSessionService

**パッケージ**: `adk-extra-services`

**インストール**:
```bash
pip install adk-extra-services
```

**実装例**:
```python
from adk_extra_services.sessions import RedisSessionService

# Redisセッションサービスの初期化
redis_service = RedisSessionService(
    redis_url="redis://localhost:6379"
)

# エージェントに登録
from google.adk import Agent

agent = Agent(
    name="my_agent",
    model="gemini-2.5-pro",
    session_service=redis_service,  # カスタムセッションサービスを指定
)
```

**メリット**:
- ✅ 高速なキャッシュ性能
- ✅ 水平スケーリング対応
- ✅ TTL（有効期限）設定可能

**デメリット**:
- ❌ Redisサーバーの管理が必要
- ❌ 永続化設定を適切に行う必要あり

### 2.2 FirestoreSessionService（カスタム実装が必要）

**現状**: ADK公式にはFirestore専用のSessionServiceはありません

**推奨アプローチ**:

Google Cloudドキュメントでは、Firestoreをセッションストレージとして使用することは**推奨されていません**：

> "While Firestore can be used for session storage, it's often more appropriate to choose a different storage solution for sessions such as **Memcache or Redis**, whose designs might result in **faster operation** in this use case."

理由:
- Firestoreはドキュメントデータベースで、セッションストレージ用に最適化されていない
- レイテンシーがRedis/Memcacheより高い
- セッションデータは頻繁に読み書きされるため、Firestoreのコスト効率が悪い

**それでもFirestoreを使いたい場合**:

カスタムSessionServiceを実装する必要があります（後述）。

---

## 3. カスタムSessionServiceの実装方法

ADKでは、SessionServiceインターフェースを実装することで、任意のストレージバックエンドを使用できます。

### 3.1 基本的な実装パターン

```python
from google.adk.sessions import SessionService
from typing import Optional, Dict, Any

class CustomSessionService(SessionService):
    """カスタムセッションサービスの実装例"""

    def __init__(self, storage_client):
        self.storage = storage_client

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッションデータを取得"""
        # ストレージからデータを読み込む
        return await self.storage.get(session_id)

    async def save_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """セッションデータを保存"""
        # ストレージにデータを書き込む
        await self.storage.set(session_id, session_data)

    async def delete_session(self, session_id: str) -> None:
        """セッションを削除"""
        await self.storage.delete(session_id)

    async def list_sessions(self) -> list[str]:
        """セッション一覧を取得"""
        return await self.storage.list_all_keys()
```

### 3.2 サービスレジストリへの登録

ADK v1.0以降では、サービスレジストリを使ってカスタムセッションサービスを登録できます：

```python
from google.adk.services import registry

# カスタムセッションサービスのファクトリー関数を登録
def create_custom_session_service(uri: str):
    # URIから設定を解析
    # 例: "custom://localhost:6379"
    return CustomSessionService(uri)

# レジストリに登録
registry.register_session_service(
    "custom",  # スキーマ名
    create_custom_session_service
)

# CLI実行時に指定
# adk run --session_service_uri=custom://localhost:6379
```

---

## 4. 実装例：FirestoreSessionService（カスタム）

もしFirestoreをセッションストレージとして使用したい場合の実装例：

```python
from google.adk.sessions import SessionService
from google.cloud import firestore
from typing import Optional, Dict, Any
import json

class FirestoreSessionService(SessionService):
    """Firestoreをバックエンドとするセッションサービス"""

    def __init__(self, project_id: str, collection_name: str = "adk_sessions"):
        self.db = firestore.Client(project=project_id)
        self.collection = self.db.collection(collection_name)

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッションデータを取得"""
        doc_ref = self.collection.document(session_id)
        doc = doc_ref.get()

        if doc.exists:
            return doc.to_dict()
        return None

    async def save_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """セッションデータを保存"""
        doc_ref = self.collection.document(session_id)
        doc_ref.set(session_data, merge=True)

    async def delete_session(self, session_id: str) -> None:
        """セッションを削除"""
        doc_ref = self.collection.document(session_id)
        doc_ref.delete()

    async def list_sessions(self) -> list[str]:
        """セッション一覧を取得"""
        docs = self.collection.stream()
        return [doc.id for doc in docs]

# 使用例
firestore_service = FirestoreSessionService(
    project_id="your-gcp-project-id",
    collection_name="adk_sessions"
)

agent = Agent(
    name="my_agent",
    model="gemini-2.5-pro",
    session_service=firestore_service,
)
```

---

## 5. 現在のHeraプロジェクトでの利用可能性

### 5.1 現状分析

**現在の実装**:
- ADKのAgentオブジェクトは初期化されているが、**実行エンジンは使用されていない**
- セッション管理は**自前実装**（FileSessionManager / FirebaseSessionManager）
- ADKのセッション機能は**未使用**

### 5.2 ADKセッション機能を使う場合のメリット

もしADKのセッション機能を使うように変更する場合：

**メリット**:
- ✅ ADKの標準機能を活用（保守性向上）
- ✅ RedisSessionServiceで高速化可能
- ✅ ADKのツール・メモリ管理と統合
- ✅ スケーラビリティ向上

**デメリット**:
- ❌ 大幅なリファクタリングが必要
- ❌ 現在の自前実装を破棄
- ❌ ADKの実行エンジン全体を使う必要がある

### 5.3 推奨アプローチ

**現状維持を推奨**:

理由:
1. すでに動作している自前実装がある
2. ADKの実行エンジンを使っていないため、セッション機能だけ使うのは不自然
3. FirebaseSessionManagerで十分な機能を実現済み

**将来的な選択肢**:
- ADKを完全に活用する方向にリファクタリングする場合のみ、ADKセッション機能の採用を検討

---

## 6. ベストプラクティス

### 6.1 ストレージバックエンドの選び方

| ユースケース | 推奨 | 理由 |
|------------|------|------|
| **開発・テスト** | InMemorySessionService | セットアップ不要、高速 |
| **本番環境（GCP）** | VertexAiSessionService | マネージド、スケーラブル |
| **本番環境（高速）** | RedisSessionService | 低レイテンシー、高スループット |
| **既存DBインフラあり** | DatabaseSessionService | インフラ統合が容易 |
| **カスタム要件** | 自作SessionService | 完全な制御 |

### 6.2 Redis vs Firestore

**セッションストレージとしては**:

| 特性 | Redis | Firestore |
|------|-------|-----------|
| **読み取り速度** | ⚡ 超高速（< 1ms） | 🐢 遅い（10-100ms） |
| **書き込み速度** | ⚡ 超高速（< 1ms） | 🐢 遅い（10-100ms） |
| **コスト** | 💰 インスタンス課金 | 💰💰 読み書き回数課金 |
| **用途適性** | ✅ セッション最適 | ❌ ドキュメントDB向け |
| **推奨度** | ⭐⭐⭐⭐⭐ | ⭐⭐ |

**結論**: **Redisを強く推奨**

---

## 7. 参考リンク

### 公式ドキュメント
- [ADK Session Documentation](https://google.github.io/adk-docs/sessions/session/)
- [Google Cloud: Handling sessions with Firestore](https://cloud.google.com/python/docs/getting-started/session-handling-with-firestore)

### パッケージ
- [adk-extra-services (PyPI)](https://pypi.org/project/adk-extra-services/)
- [google-adk (PyPI)](https://pypi.org/project/google-adk/)

### GitHub Issues
- [Support to configure Redis as session storage #938](https://github.com/google/adk-python/issues/938)

---

## 8. まとめ

### 質問への回答

> Google ADKのSession機能は、ローカルファイル保存以外に読み書き先を変更できるか？

**回答**: **はい、可能です。**

ADKは以下の方法でストレージバックエンドを変更できます：

1. ✅ **標準提供**: InMemory, VertexAI, Database
2. ✅ **追加パッケージ**: Redis (`adk-extra-services`)
3. ✅ **カスタム実装**: SessionServiceインターフェースを実装

### Heraプロジェクトへの適用

**現時点では適用不要**:
- 現在のプロジェクトは自前のセッション管理を使用
- ADKの実行エンジンを使っていないため、ADKセッション機能を使うメリットが少ない
- FirebaseSessionManagerで十分な機能を提供済み

**将来的な検討事項**:
- ADKを完全に活用する方向にリファクタリングする場合
- RedisSessionServiceで高速化したい場合
- ADKのツール・メモリ管理を統合したい場合

---

**調査者**: Claude Code
**最終更新**: 2025年11月7日
