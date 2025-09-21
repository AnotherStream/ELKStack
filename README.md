# ELK Stack Docker Compose

このプロジェクトは、Docker Composeを使用してELKスタック（Elasticsearch、Logstash、Kibana）を簡単にセットアップ・管理するためのツールとスクリプトを提供します。

## 構成

- **Elasticsearch 8.11.0**: 検索・分析エンジン
- **Logstash 8.11.0**: データ処理パイプライン
- **Kibana 8.11.0**: データ可視化ダッシュボード

## 前提条件

- Python 3.7以上
- Docker & Docker Compose
- （Linuxの場合）sudo権限

## クイックスタート

### 1. リポジトリのクローン

```bash
# リポジトリをクローン
git clone <repository-url>
cd ELKStack
```

### 2. 設定ファイルの作成

#### LDAP認証なしの場合
```bash
# 環境変数ファイルの作成
cp .env.template .env

# Docker Composeファイルの作成
cp docker-compose.yml.template docker-compose.yml

# .envファイルを編集（必要に応じてポート番号やメモリ設定等を変更）
```

#### LDAP認証ありの場合
```bash
# 環境変数ファイルの作成
cp .env.template-ldap .env

# Docker Composeファイルの作成
cp docker-compose.yml.template-ldap docker-compose.yml

# .envファイルを編集（LDAP設定やパスワード等を設定）
```

### 3. セットアップ（依存関係のインストール含む）

#### Windows
```batch
# セットアップの実行
elk_manager.bat setup
```

#### Linux/macOS
```bash
# セットアップの実行
./elk_manager.sh setup
```

### 4. ELKスタックの起動

#### Windows
```batch
# 開始
elk_manager.bat start

# 再起動（更新含む）
elk_manager.bat restart

# または、直接Docker Composeを使用
docker-compose up -d
```

#### Linux/macOS
```bash
# 開始
./elk_manager.sh start

# 再起動（更新含む）
./elk_manager.sh restart

# または、直接Docker Composeを使用
docker-compose up -d
```

**注意**: LDAP認証を使用する場合は、事前にcerts/ディレクトリに必要な証明書ファイルを配置してください。

### 5. アクセス

- **Elasticsearch**: http://localhost:9200
- **Kibana**: http://localhost:5601
- **Logstash**: 
  - Beats入力: localhost:5044
  - TCP/UDP入力: localhost:5000
  - HTTP API: localhost:9600

## 設定ファイル

### ディレクトリ構造（テンプレートファイル含む）

```
ELKStack/
├── docker-compose.yml.template        # Docker Composeテンプレート（LDAPなし）
├── docker-compose.yml.template-ldap   # Docker Composeテンプレート（LDAPあり）
├── docker-compose.yml                 # Docker Compose設定（手動作成）
├── .env.template                      # 環境変数テンプレート（LDAPなし）
├── .env.template-ldap                 # 環境変数テンプレート（LDAPあり）
├── .env                               # 環境変数（手動作成）
├── requirements.txt           # Python依存関係
├── elk_manager.bat / elk_manager.sh  # 統合管理スクリプト実行ファイル
├── Elasticsearch/             # Elasticsearch設定ファイル
│   └── elasticsearch.yml
├── Kibana/                    # Kibana設定ファイル
│   └── kibana.yml
├── Logstash/                  # Logstash設定ファイル
│   ├── logstash.yml
│   ├── pipelines.yml
│   └── pipeline/
│       └── logstash.conf
├── Volumes/                   # データ永続化ディレクトリ
│   ├── Elasticsearch/
│   │   └── data/
│   ├── Kibana/
│   │   └── data/
│   └── Logstash/
│       └── data/
└── scripts/                   # 管理スクリプト（Python実装）
    └── elk_manager.py        # 統合管理スクリプト
```

## よく使用するコマンド

### 管理スクリプト

#### Windows（バッチファイル）
```batch
# セットアップ
elk_manager.bat setup

# 開始
elk_manager.bat start

# 停止
elk_manager.bat stop

# 再起動（更新含む）
elk_manager.bat restart

# ログ表示
elk_manager.bat logs                      # 全サービスのログ
elk_manager.bat logs elasticsearch        # Elasticsearchのログのみ
elk_manager.bat logs -f                   # リアルタイムログ表示
elk_manager.bat logs -s                   # サービス状態表示

# クリーンアップ
elk_manager.bat cleanup
```

#### Linux/macOS（シェルスクリプト）
```bash
# セットアップ
./elk_manager.sh setup

# 開始
./elk_manager.sh start

# 停止
./elk_manager.sh stop

# 再起動（更新含む）
./elk_manager.sh restart

# ログ表示
./elk_manager.sh logs                     # 全サービスのログ
./elk_manager.sh logs elasticsearch       # Elasticsearchのログのみ
./elk_manager.sh logs -f                  # リアルタイムログ表示
./elk_manager.sh logs -s                  # サービス状態表示

# クリーンアップ
./elk_manager.sh cleanup
```

#### Python直接実行（開発用）
```bash
# セットアップ
python scripts/elk_manager.py setup

# 開始
python scripts/elk_manager.py start

# 停止
python scripts/elk_manager.py stop

# 再起動（更新含む）
python scripts/elk_manager.py restart

# ログ表示
python scripts/elk_manager.py logs                    # 全サービスのログ
python scripts/elk_manager.py logs elasticsearch     # Elasticsearchのログのみ
python scripts/elk_manager.py logs -f                # リアルタイムログ表示
python scripts/elk_manager.py logs -s                # サービス状態表示

# クリーンアップ
python scripts/elk_manager.py cleanup
```

### 基本操作（Docker Compose直接）

```bash
# 起動
docker-compose up -d

# 停止
docker-compose down

# 再起動
docker-compose restart

# ログ確認
docker-compose logs -f
```

### ヘルスチェック

```bash
# Elasticsearch
curl -X GET "localhost:9200/_cluster/health?pretty"

# Kibana
curl -X GET "localhost:5601/api/status"

# Logstash
curl -X GET "localhost:9600/_node/stats?pretty"
```

### データ投入テスト

```bash
# JSON形式でLogstashにデータを送信
curl -X POST "localhost:5000" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello ELK Stack!", "level": "INFO", "timestamp": "'$(date -Iseconds)'"}'
```

## カスタマイズ

### 環境変数の変更

`.env`ファイルを編集して、ポート番号やメモリ設定などを変更できます。

### LDAP認証の設定

LDAP認証を使用する場合は、`.env.template.ldap`と`docker-compose.yml.template.ldap`を使用し、以下の設定を行ってください：

- `ELASTIC_PASSWORD`: Elasticsearchのelasticユーザーのパスワード
- `LDAP_URL`: LDAPサーバーのURL
- `LDAP_BIND_DN`: LDAPバインドDN
- `LDAP_BIND_PASSWORD`: LDAPバインドパスワード
- `LDAP_USER_SEARCH_BASE_DN`: ユーザー検索ベーsDN
- `LDAP_GROUP_SEARCH_BASE_DN`: グループ検索ベーsDN

### 設定ファイルの変更

各サービスの設定ファイルは各アプリケーション専用ディレクトリ内にあります：

- `Elasticsearch/elasticsearch.yml`
- `Logstash/logstash.yml`
- `Logstash/pipeline/logstash.conf`
- `Kibana/kibana.yml`

### Logstashパイプラインのカスタマイズ

`Logstash/pipeline/logstash.conf`を編集して、データ処理ロジックをカスタマイズできます。

## トラブルシューティング

### よくある問題

1. **Elasticsearchが起動しない**
   - メモリ不足: `.env`ファイルでJavaヒープサイズを調整
   - vm.max_map_count: Linux環境で`sudo sysctl -w vm.max_map_count=262144`

2. **権限エラー**
   - データディレクトリの権限: `sudo chown -R 1000:1000 Volumes/`

3. **ポート競合**
   - `.env`ファイルでポート番号を変更

### ログの確認

```bash
# 全サービスのログ
docker-compose logs

# 特定のサービスのログ
docker-compose logs elasticsearch
docker-compose logs logstash
docker-compose logs kibana
```

## クリーンアップ

### Windows
```batch
# 完全なクリーンアップ（対話式）
elk_manager.bat cleanup

# または再起動のみ
elk_manager.bat restart

# コンテナのみ停止・削除
docker-compose down
```

### Linux/macOS
```bash
# 完全なクリーンアップ（対話式）
./elk_manager.sh cleanup

# または再起動のみ
./elk_manager.sh restart

# コンテナのみ停止・削除
docker-compose down
```

## 注意事項

- このセットアップは開発・テスト環境向けです
- 本番環境では適切なセキュリティ設定を行ってください
- データの永続化が必要な場合は、適切なバックアップ戦略を実装してください