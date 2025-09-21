# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要
このプロジェクトは、Docker Composeを使用してELKスタック（Elasticsearch、Logstash、Kibana）をセットアップ・管理するためのツールとスクリプトを提供します。再利用可能な設定テンプレートとELKデプロイメント用の自動化スクリプトの作成に焦点を当てています。

## よく使用するコマンド

### 管理スクリプト（入り口）

#### Windows（バッチファイル）
```batch
# セットアップの実行（依存関係のインストール含む）
elk_manager.bat setup

# ELKスタックの開始
elk_manager.bat start

# ELKスタックの停止
elk_manager.bat stop

# ELKスタックの再起動（更新含む）
elk_manager.bat restart

# ログ表示
elk_manager.bat logs
elk_manager.bat logs elasticsearch
elk_manager.bat logs -f
elk_manager.bat logs -s

# 停止とクリーンアップ
elk_manager.bat cleanup
```

#### Linux/macOS（シェルスクリプト）
```bash
# セットアップの実行（依存関係のインストール含む）
./elk_manager.sh setup

# ELKスタックの開始
./elk_manager.sh start

# ELKスタックの停止
./elk_manager.sh stop

# ELKスタックの再起動（更新含む）
./elk_manager.sh restart

# ログ表示
./elk_manager.sh logs
./elk_manager.sh logs elasticsearch
./elk_manager.sh logs -f
./elk_manager.sh logs -s

# 停止とクリーンアップ
./elk_manager.sh cleanup
```

#### Python直接実行（開発用）
```bash
# セットアップの実行
python scripts/elk_manager.py setup

# ELKスタックの開始
python scripts/elk_manager.py start

# ELKスタックの停止
python scripts/elk_manager.py stop

# ELKスタックの再起動（更新含む）
python scripts/elk_manager.py restart

# ログ表示
python scripts/elk_manager.py logs

# 停止とクリーンアップ
python scripts/elk_manager.py cleanup
```

### Docker Composeコマンド
```bash
# ELKスタックの起動
docker-compose up -d

# ELKスタックの停止
docker-compose down

# 特定のサービスのログ表示
docker-compose logs -f elasticsearch
docker-compose logs -f logstash
docker-compose logs -f kibana

# リビルドと再起動
docker-compose build && docker-compose up -d
```

### ヘルスチェックコマンド
```bash
# Elasticsearchの状態確認
curl -X GET "localhost:9200/_cluster/health"

# Kibanaの状態確認
curl -X GET "localhost:5601/api/status"

# Logstash設定の検証
docker-compose exec logstash bin/logstash --config.test_and_exit -f /usr/share/logstash/pipeline/
```

## アーキテクチャ概要
- ELKスタック構成ツール・スクリプト開発プロジェクト
- Elasticsearch: 検索・分析エンジン（通常ポート9200）
- Logstash: データ処理パイプライン（通常入力ポート5044）
- Kibana: データ可視化ダッシュボード（通常ポート5601）
- 想定される設定ファイル: docker-compose.yml, logstash.conf, elasticsearch.yml, kibana.yml

## プロジェクト構造ガイドライン
- `docker-compose.yml.template` - Docker Composeテンプレート（LDAP認証なし）
- `docker-compose.yml.template-ldap` - Docker Composeテンプレート（LDAP認証あり）
- `docker-compose.yml` - ELKスタック用のDocker Compose設定（手動作成）
- `.env.template` - 環境変数テンプレート（LDAP認証なし）
- `.env.template-ldap` - 環境変数テンプレート（LDAP認証あり）
- `.env` - 環境変数ファイル（手動作成）
- `requirements.txt` - Python依存関係
- `certs/` - SSL/TLS証明書ディレクトリ（LDAP認証時に必要）
- `/Elasticsearch/` - Elasticsearch用の設定ファイル
- `/Kibana/` - Kibana用の設定ファイル
- `/Logstash/` - Logstash用の設定ファイル
- `/Volumes/` - データ永続化用ディレクトリ
  - `/Volumes/Elasticsearch/data/` - Elasticsearchデータ
  - `/Volumes/Kibana/data/` - Kibanaデータ
  - `/Volumes/Logstash/data/` - Logstashデータ
- `/scripts/` - Python製の統合管理スクリプト（elk_manager.py）

### アプリケーション追加時のルール
- 新しいアプリケーション追加時は、ルート直下に`/[アプリケーション名]/`フォルダを作成
- データ永続化は`/Volumes/[アプリケーション名]/`以下にマップする

## 開発ルール・方針

### 設定ファイル管理
- テンプレートファイルを用意：LDAP認証あり/なしの2種類
  - `.env.template` / `docker-compose.yml.template` (ベーシック版)
  - `.env.template-ldap` / `docker-compose.yml.template-ldap` (LDAP認証版)
- 人間が手動でテンプレートを参考に設定ファイルを作成する
- スクリプトなどで設定ファイルが存在しない場合はエラーとして処理する
- セットアップスクリプトは設定ファイルの自動作成は行わない
- LDAP認証使用時は証明書ファイルの配置が必要（certs/ディレクトリ）
- 証明書ファイルは機密情報のためリポジトリにコミットしない

### 環境変数・設定値の扱い
- 環境変数の参照で値が見つからない場合は、デフォルト値やリカバリー処理は行わない
- 必要な設定値が不足している場合は明確にエラーとして処理する
- 設定不備による予期しない動作を防ぐため、厳格にチェックする

### スクリプト実装方針
- 実装の詳細やロジックの実装はPythonで行う
- 実行用の入り口となる部分は、バッチファイル（Windows用）とシェルスクリプト（Linux/macOS用）を用意して実行できるようにする
- 管理スクリプトは原則Pythonで実装する
- シェルスクリプトやバッチファイルでは複雑なロジックは実装しない
- 複雑なロジックはPythonで実装する
- Pythonでライブラリが使用できる機能については、外部コマンド実行ではなくライブラリを優先して使用する

### Pythonライブラリ優先例
- ファイル操作: シェルコマンドではなく`pathlib`や標準ライブラリ
- JSON処理: 外部コマンドではなく`json`ライブラリ
- YAML処理: 外部コマンドではなく`PyYAML`ライブラリ

### REST API / HTTPアクセス
- REST APIなどのHTTPアクセスは、`requests`ライブラリではなく`curl`をサブプロセスで実行する
- これは、コマンドラインやシェルでの検証時に同じコマンドを使用できるようにするため
- `subprocess`を使用して`curl`コマンドを実行し、結果を解析する

### Gitコミット管理
- コミットメッセージは日本語で記載する
- コミットは基本的に自動実行しない
- コミットを実行する場合は、必ずユーザーに確認を取る
- コミットメッセージにはClaude Codeでメッセージを作成した旨は記載しない

## セキュリティ考慮事項
- パスワードやAPIキーなどの機密データをコミットしない
- 機密設定には環境変数を使用する
- サービス間通信の適切なネットワークセキュリティを確保する