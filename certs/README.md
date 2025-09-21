# 証明書ディレクトリ

このディレクトリには、LDAP認証やSSL/TLS通信に必要な証明書ファイルを配置します。

## 必要なファイル（LDAP認証使用時）

### Elasticsearchで必要な証明書
- `ca.crt` - CA証明書（認証局の証明書）
- `elasticsearch.crt` - Elasticsearch用SSL証明書
- `elasticsearch.key` - Elasticsearch用秘密鍵

### Kibanaで必要な証明書
- `kibana.crt` - Kibana用SSL証明書  
- `kibana.key` - Kibana用秘密鍵

### Logstashで必要な証明書
- `logstash.crt` - Logstash用SSL証明書
- `logstash.key` - Logstash用秘密鍵

## セットアップ手順

1. 証明書ファイルをこのディレクトリに配置
2. 適切な権限を設定（読み取り専用推奨）
3. .envファイルで証明書パスを設定

## 注意事項

- 証明書ファイルは機密情報のためリポジトリにコミットしないこと
- 本番環境では信頼できるCA発行の証明書を使用すること
- 開発環境では自己署名証明書でも可能