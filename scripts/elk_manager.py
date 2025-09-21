#!/usr/bin/env python3
"""
ELK Stack 統合管理スクリプト
モジュール化された機能を使用
"""

import sys
import argparse
from pathlib import Path
from typing import List, Optional

# モジュールのインポート
from modules.elk_backup_manager import ELKBackupManager
from modules.docker_manager import DockerManager
from modules.env_manager import EnvironmentManager
from modules.cleanup_manager import CleanupManager


class ELKManager:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent

        # 各種マネージャーのインスタンス化
        self.docker_manager = DockerManager(self.project_root)
        self.env_manager = EnvironmentManager(self.project_root)
        self.cleanup_manager = CleanupManager(self.project_root)

    def log(self, message: str, level: str = "INFO") -> None:
        """ログメッセージを出力"""
        print(f"[{level}] {message}")

    def check_prerequisites(self) -> bool:
        """事前条件をチェック"""
        self.log("事前条件をチェック中...")

        # 環境ファイルとDocker Composeファイルの確認
        if not self.env_manager.check_env_file():
            self.log("その後 python scripts/elk_manager.py setup を実行してください", "ERROR")
            return False

        if not self.env_manager.check_docker_compose_file():
            return False

        # Docker要件の確認
        if not self.docker_manager.check_docker_requirements():
            return False

        self.log("事前条件チェック完了")
        return True

    # === SETUP コマンド ===
    def cmd_setup(self) -> bool:
        """セットアップコマンドを実行"""
        self.log("=== ELK Stack セットアップを開始します ===")

        steps = [
            ("必要な要件のチェック", self.docker_manager.check_docker_requirements),
            ("環境変数ファイルの確認", self.env_manager.check_env_file),
            ("Docker Composeファイルの確認", self.env_manager.check_docker_compose_file),
            ("証明書ファイルの確認", self.env_manager.check_certificates),
            ("ディレクトリの作成", self.env_manager.create_directories),
            ("権限の設定", self.env_manager.set_permissions),
            ("vm.max_map_countの設定", self.env_manager.configure_vm_max_map_count),
            ("Dockerイメージの取得", self.docker_manager.pull_images),
        ]

        for step_name, step_func in steps:
            self.log(f"実行中: {step_name}")
            if not step_func():
                self.log(f"セットアップが失敗しました: {step_name}", "ERROR")
                return False

        self.log("=== セットアップが完了しました ===")
        self.log("ELKスタックの準備が整いました。以下のコマンドで操作できます:")
        self.log("- 開始: python scripts/elk_manager.py start")
        self.log("- 停止: python scripts/elk_manager.py stop")
        self.log("- 再起動: python scripts/elk_manager.py restart")

        return True

    # === START コマンド ===
    def cmd_start(self) -> bool:
        """ELKスタックを開始"""
        self.log("=== ELK Stack を開始します ===")

        steps = [
            ("事前条件のチェック", self.check_prerequisites),
            ("サービスの起動", self.docker_manager.start_services),
        ]

        for step_name, step_func in steps:
            self.log(f"実行中: {step_name}")
            if not step_func():
                self.log(f"開始が失敗しました: {step_name}", "ERROR")
                return False

        services_healthy = self.docker_manager.check_all_services()

        self.log("=== ELK Stack の開始完了 ===")

        env_vars = self.env_manager.load_env_variables()

        required_vars = ["ELASTICSEARCH_PORT", "KIBANA_PORT", "LOGSTASH_PORT"]
        missing_vars = []
        for var in required_vars:
            if var not in env_vars or not env_vars[var]:
                missing_vars.append(var)

        if missing_vars:
            self.log(f"必要な環境変数が設定されていません: {', '.join(missing_vars)}", "ERROR")
            self.log(".envファイルを確認してください", "ERROR")
            return False

        es_port = env_vars["ELASTICSEARCH_PORT"]
        kibana_port = env_vars["KIBANA_PORT"]
        logstash_port = env_vars["LOGSTASH_PORT"]

        self.log(f"Elasticsearch: http://localhost:{es_port}")
        self.log(f"Kibana: http://localhost:{kibana_port}")
        self.log(f"Logstash: localhost:{logstash_port} (Beats), localhost:5000 (TCP/UDP)")
        self.log("")
        self.log("ログの確認: python scripts/elk_manager.py logs")

        if not services_healthy:
            self.log("一部のサービスが正常に起動していない可能性があります", "WARNING")
            self.log("ログを確認してください:", "WARNING")

        return True

    # === STOP コマンド ===
    def cmd_stop(self) -> bool:
        """ELKスタックを停止"""
        self.log("=== ELK Stack を停止します ===")

        if not self.docker_manager.stop_containers():
            self.log("停止が失敗しました", "ERROR")
            return False

        self.log("=== ELK Stack の停止完了 ===")
        return True

    # === RESTART コマンド ===
    def cmd_restart(self) -> bool:
        """再起動コマンドを実行"""
        self.log("=== ELK Stack 再起動を開始します ===")

        steps = [
            ("事前条件のチェック", self.check_prerequisites),
            ("既存コンテナの停止", self.docker_manager.stop_containers),
            ("Dockerイメージの更新", self.docker_manager.pull_images),
            ("サービスの起動", self.docker_manager.start_services),
        ]

        for step_name, step_func in steps:
            self.log(f"実行中: {step_name}")
            if not step_func():
                self.log(f"再起動が失敗しました: {step_name}", "ERROR")
                return False

        services_healthy = self.docker_manager.check_all_services()

        self.log("=== 再起動完了 ===")

        env_vars = self.env_manager.load_env_variables()

        required_vars = ["ELASTICSEARCH_PORT", "KIBANA_PORT", "LOGSTASH_PORT"]
        missing_vars = []
        for var in required_vars:
            if var not in env_vars or not env_vars[var]:
                missing_vars.append(var)

        if missing_vars:
            self.log(f"必要な環境変数が設定されていません: {', '.join(missing_vars)}", "ERROR")
            self.log(".envファイルを確認してください", "ERROR")
            return False

        es_port = env_vars["ELASTICSEARCH_PORT"]
        kibana_port = env_vars["KIBANA_PORT"]
        logstash_port = env_vars["LOGSTASH_PORT"]

        self.log(f"Elasticsearch: http://localhost:{es_port}")
        self.log(f"Kibana: http://localhost:{kibana_port}")
        self.log(f"Logstash: localhost:{logstash_port} (Beats), localhost:5000 (TCP/UDP)")
        self.log("")
        self.log("ログの確認: python scripts/elk_manager.py logs")

        if not services_healthy:
            self.log("一部のサービスが正常に起動していない可能性があります", "WARNING")
            self.log("ログを確認してください:", "WARNING")

        return True

    # === LOGS コマンド ===
    def cmd_logs(self, service: Optional[str] = None, follow: bool = False, tail: int = 50, status: bool = False) -> bool:
        """ログコマンドを実行"""
        if status:
            return self.docker_manager.show_service_status()
        else:
            return self.docker_manager.show_logs(service, follow, tail)

    # === CLEANUP コマンド ===
    def cmd_cleanup(self) -> bool:
        """クリーンアップコマンドを実行"""
        self.log("=== ELK Stack クリーンアップを開始します ===")

        self.cleanup_manager.show_cleanup_summary()

        if not self.cleanup_manager.confirm_action("クリーンアップを実行しますか？"):
            self.log("クリーンアップをキャンセルしました")
            return True

        remove_volumes = self.cleanup_manager.confirm_action("Docker Volumeも削除しますか？")
        if not self.docker_manager.stop_containers(remove_volumes):
            return False

        if self.cleanup_manager.confirm_action("ELK関連のDockerイメージも削除しますか？"):
            self.cleanup_manager.remove_elk_images()

        if self.cleanup_manager.confirm_action("データディレクトリも削除しますか？"):
            self.env_manager.clean_data_directories()

        if self.cleanup_manager.confirm_action("未使用のDockerリソースもクリーンアップしますか？"):
            self.cleanup_manager.clean_docker_system()

        self.log("=== クリーンアップが完了しました ===")
        return True

    # === BACKUP コマンド ===
    def get_backup_manager(self) -> Optional[ELKBackupManager]:
        """ELKBackupManagerインスタンスを取得"""
        env_vars = self.env_manager.load_env_variables()

        # デフォルト値の設定
        es_port = env_vars.get("ELASTICSEARCH_PORT", "9200")
        kibana_port = env_vars.get("KIBANA_PORT", "5601")

        es_url = f"http://localhost:{es_port}"
        kibana_url = f"http://localhost:{kibana_port}"
        backup_dir = str(self.project_root / "backups")

        return ELKBackupManager(es_url, kibana_url, backup_dir)

    def cmd_backup(self, indices: Optional[List[str]] = None) -> bool:
        """バックアップコマンドを実行"""
        self.log("=== ELK Stack バックアップを開始します ===")

        backup_manager = self.get_backup_manager()
        if not backup_manager:
            self.log("バックアップマネージャーの初期化に失敗しました", "ERROR")
            return False

        result = backup_manager.backup_full(indices)
        if result:
            self.log(f"バックアップが完了しました: {result}")
            return True
        else:
            self.log("バックアップが失敗しました", "ERROR")
            return False

    def cmd_restore(self, snapshot_name: str, indices: Optional[List[str]] = None) -> bool:
        """リストアコマンドを実行"""
        self.log("=== ELK Stack スナップショットリストアを開始します ===")

        backup_manager = self.get_backup_manager()
        if not backup_manager:
            self.log("バックアップマネージャーの初期化に失敗しました", "ERROR")
            return False

        success = backup_manager.restore_elasticsearch_snapshot("backup_repo", snapshot_name, indices)
        if success:
            self.log(f"スナップショットリストアが完了しました: {snapshot_name}")
            return True
        else:
            self.log("スナップショットリストアが失敗しました", "ERROR")
            return False

    def cmd_kibana_import_savedobject(self, backup_file: str, overwrite: bool = False) -> bool:
        """Kibana SavedObjectsインポートコマンドを実行"""
        self.log("=== Kibana SavedObjects インポートを開始します ===")

        backup_manager = self.get_backup_manager()
        if not backup_manager:
            self.log("バックアップマネージャーの初期化に失敗しました", "ERROR")
            return False

        success = backup_manager.import_kibana_saved_objects(backup_file, overwrite)
        if success:
            self.log(f"Kibana SavedObjectsインポートが完了しました: {backup_file}")
            return True
        else:
            self.log("Kibana SavedObjectsインポートが失敗しました", "ERROR")
            return False

    def cmd_kibana_export_savedobject(self, output_file: Optional[str] = None) -> bool:
        """Kibana SavedObjectsエクスポートコマンドを実行"""
        self.log("=== Kibana SavedObjects エクスポートを開始します ===")

        backup_manager = self.get_backup_manager()
        if not backup_manager:
            self.log("バックアップマネージャーの初期化に失敗しました", "ERROR")
            return False

        if output_file:
            # カスタムファイル名でエクスポート
            result = backup_manager.export_kibana_saved_objects_custom(output_file)
        else:
            # デフォルトファイル名でエクスポート
            result = backup_manager.export_kibana_saved_objects()

        if result:
            self.log(f"Kibana SavedObjectsエクスポートが完了しました: {result}")
            return True
        else:
            self.log("Kibana SavedObjectsエクスポートが失敗しました", "ERROR")
            return False

    def cmd_list_snapshots(self) -> bool:
        """スナップショット一覧コマンドを実行"""
        self.log("=== スナップショット一覧を表示します ===")

        backup_manager = self.get_backup_manager()
        if not backup_manager:
            self.log("バックアップマネージャーの初期化に失敗しました", "ERROR")
            return False

        snapshots = backup_manager.list_snapshots()
        if snapshots:
            return True
        else:
            self.log("スナップショットが見つかりませんでした", "WARNING")
            return True


def show_usage():
    """使用方法を表示"""
    print("使用方法: python scripts/elk_manager.py <command> [options]")
    print("")
    print("利用可能なコマンド:")
    print("  setup      - 初期セットアップを実行")
    print("  start      - ELKスタックを開始")
    print("  stop       - ELKスタックを停止")
    print("  restart    - ELKスタックを再起動（更新含む）")
    print("  logs       - ログを表示")
    print("  cleanup    - クリーンアップを実行")
    print("  backup     - ELKスタックのバックアップを作成")
    print("  restore    - Elasticsearchスナップショットをリストア")
    print("  kibana-export-savedobject - Kibana SavedObjectsをエクスポート")
    print("  kibana-import-savedobject - Kibana SavedObjectsをインポート")
    print("  list-snapshots - 利用可能なスナップショット一覧を表示")
    print("")
    print("ログコマンドのオプション:")
    print("  -f, --follow    ログをリアルタイムで表示")
    print("  -t, --tail N    最新のN行を表示（デフォルト: 50）")
    print("  -s, --status    サービスの状態を表示")
    print("  <service>       特定サービスのログ（elasticsearch, logstash, kibana）")
    print("")
    print("バックアップコマンドのオプション:")
    print("  --indices INDEX1 INDEX2  特定のインデックスのみバックアップ")
    print("  --snapshot-name NAME     リストア時のスナップショット名")
    print("  --backup-file FILE       Kibanaインポート時のバックアップファイル")
    print("  --output-file FILE       Kibanaエクスポート時の出力ファイル")
    print("  --overwrite             Kibanaインポート時に既存オブジェクトを上書き")
    print("")
    print("例:")
    print("  python scripts/elk_manager.py setup")
    print("  python scripts/elk_manager.py start")
    print("  python scripts/elk_manager.py stop")
    print("  python scripts/elk_manager.py restart")
    print("  python scripts/elk_manager.py logs")
    print("  python scripts/elk_manager.py logs -f elasticsearch")
    print("  python scripts/elk_manager.py logs -s")
    print("  python scripts/elk_manager.py cleanup")
    print("  python scripts/elk_manager.py backup")
    print("  python scripts/elk_manager.py backup --indices myindex1 myindex2")
    print("  python scripts/elk_manager.py restore --snapshot-name snapshot_20240101_120000")
    print("  python scripts/elk_manager.py kibana-export-savedobject")
    print("  python scripts/elk_manager.py kibana-export-savedobject --output-file my_export.ndjson")
    print("  python scripts/elk_manager.py kibana-import-savedobject --backup-file backups/kibana_saved_objects.ndjson")
    print("  python scripts/elk_manager.py list-snapshots")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='ELK Stack Management Tool', add_help=False)
    parser.add_argument('command', nargs='?',
                       choices=['setup', 'start', 'stop', 'restart', 'logs', 'cleanup',
                               'backup', 'restore', 'kibana-export-savedobject',
                               'kibana-import-savedobject', 'list-snapshots'],
                       help='Command to execute')
    parser.add_argument('service', nargs='?', help='Service name for logs command')
    parser.add_argument('-f', '--follow', action='store_true', help='Follow log output')
    parser.add_argument('-t', '--tail', type=int, default=50, help='Number of lines to show')
    parser.add_argument('-s', '--status', action='store_true', help='Show service status')
    parser.add_argument('-h', '--help', action='store_true', help='Show help message')

    # バックアップ関連のオプション
    parser.add_argument('--indices', nargs='+', help='Specific indices to backup/restore')
    parser.add_argument('--snapshot-name', help='Snapshot name for restore operation')
    parser.add_argument('--backup-file', help='Backup file path for Kibana import operations')
    parser.add_argument('--output-file', help='Output file path for Kibana export operations')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing objects during Kibana import')

    args = parser.parse_args()

    if args.help or not args.command:
        show_usage()
        return

    manager = ELKManager()

    try:
        if args.command == 'setup':
            success = manager.cmd_setup()
        elif args.command == 'start':
            success = manager.cmd_start()
        elif args.command == 'stop':
            success = manager.cmd_stop()
        elif args.command == 'restart':
            success = manager.cmd_restart()
        elif args.command == 'logs':
            success = manager.cmd_logs(args.service, args.follow, args.tail, args.status)
        elif args.command == 'cleanup':
            success = manager.cmd_cleanup()
        elif args.command == 'backup':
            success = manager.cmd_backup(args.indices)
        elif args.command == 'restore':
            if not args.snapshot_name:
                print("エラー: restore コマンドには --snapshot-name が必要です")
                show_usage()
                sys.exit(1)
            success = manager.cmd_restore(args.snapshot_name, args.indices)
        elif args.command == 'kibana-export-savedobject':
            success = manager.cmd_kibana_export_savedobject(args.output_file)
        elif args.command == 'kibana-import-savedobject':
            if not args.backup_file:
                print("エラー: kibana-import-savedobject コマンドには --backup-file が必要です")
                show_usage()
                sys.exit(1)
            success = manager.cmd_kibana_import_savedobject(args.backup_file, args.overwrite)
        elif args.command == 'list-snapshots':
            success = manager.cmd_list_snapshots()
        else:
            show_usage()
            return

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n操作がキャンセルされました")
        sys.exit(1)
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()