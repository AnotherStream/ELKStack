#!/usr/bin/env python3
"""
ELK Stack Backup and Restore Module
Kibana SavedObjectを介したバックアップ・リストア機能を提供
"""

import os
import json
import subprocess
import datetime
from pathlib import Path
import logging
import time
import tarfile
import shutil
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class ELKBackupManager:
    """ELK Stack バックアップ・リストア管理クラス"""

    def __init__(self, elasticsearch_url: str = "http://localhost:9200",
                 kibana_url: str = "http://localhost:5601",
                 backup_dir: str = "./backups"):
        self.es_url = elasticsearch_url
        self.kibana_url = kibana_url
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

    def log(self, message: str, level: str = "INFO") -> None:
        """ログメッセージを出力"""
        print(f"[{level}] {message}")

    def run_curl_command(self, url: str, method: str = "GET", data: Optional[Dict[str, Any]] = None,
                        headers: Optional[Dict[str, str]] = None, output_file: Optional[Path] = None) -> Optional[str]:
        """curlコマンドを実行してHTTPリクエストを送信"""
        cmd = ["curl", "-s", "-X", method]

        if headers:
            for key, value in headers.items():
                cmd.extend(["-H", f"{key}: {value}"])

        if data:
            if isinstance(data, dict):
                data = json.dumps(data)
            cmd.extend(["-d", data])

        if output_file:
            cmd.extend(["-o", str(output_file)])

        cmd.append(url)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout if not output_file else True
        except subprocess.CalledProcessError as e:
            logger.error(f"curl command failed: {e}")
            logger.error(f"stderr: {e.stderr}")
            return None

    def check_elasticsearch_health(self) -> bool:
        """Elasticsearchの健全性チェック"""
        try:
            response = self.run_curl_command(f"{self.es_url}/_cluster/health")
            if response:
                health = json.loads(response)
                self.log(f"Elasticsearch status: {health['status']}")
                return health['status'] in ['green', 'yellow']
            return False
        except Exception as e:
            self.log(f"Elasticsearch health check failed: {e}", "ERROR")
            return False

    def check_kibana_health(self) -> bool:
        """Kibanaの健全性チェック"""
        try:
            response = self.run_curl_command(f"{self.kibana_url}/api/status")
            if response:
                status = json.loads(response)
                self.log(f"Kibana status: {status.get('status', {}).get('overall', {}).get('state', 'unknown')}")
                return True
            return False
        except Exception as e:
            self.log(f"Kibana health check failed: {e}", "ERROR")
            return False

    def get_indices(self) -> List[str]:
        """インデックス一覧を取得"""
        try:
            response = self.run_curl_command(f"{self.es_url}/_cat/indices?format=json")
            if response:
                indices = json.loads(response)
                user_indices = [idx for idx in indices if not idx['index'].startswith('.')]
                return [idx['index'] for idx in user_indices]
            return []
        except Exception as e:
            self.log(f"Failed to get indices: {e}", "ERROR")
            return []

    def create_snapshot_repository(self, repo_name: str = "backup_repo") -> bool:
        """スナップショットリポジトリを作成"""
        repo_path = "/usr/share/elasticsearch/data/snapshots"
        repo_config = {
            "type": "fs",
            "settings": {
                "location": repo_path,
                "compress": True
            }
        }

        try:
            headers = {"Content-Type": "application/json"}
            response = self.run_curl_command(
                f"{self.es_url}/_snapshot/{repo_name}",
                method="PUT",
                data=repo_config,
                headers=headers
            )
            if response is not None:
                self.log(f"Snapshot repository '{repo_name}' created/updated")
                return True
            return False
        except Exception as e:
            self.log(f"Failed to create snapshot repository: {e}", "ERROR")
            return False

    def create_elasticsearch_snapshot(self, snapshot_name: Optional[str] = None,
                                    indices: Optional[List[str]] = None) -> Optional[str]:
        """Elasticsearchスナップショットを作成"""
        if not snapshot_name:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_name = f"snapshot_{timestamp}"

        repo_name = "backup_repo"

        if not self.create_snapshot_repository(repo_name):
            return None

        snapshot_config = {
            "indices": ",".join(indices) if indices else "*",
            "ignore_unavailable": True,
            "include_global_state": True,
            "metadata": {
                "taken_by": "elk_backup_script",
                "taken_because": "scheduled_backup"
            }
        }

        try:
            headers = {"Content-Type": "application/json"}
            response = self.run_curl_command(
                f"{self.es_url}/_snapshot/{repo_name}/{snapshot_name}",
                method="PUT",
                data=snapshot_config,
                headers=headers
            )
            if response is not None:
                self.wait_for_snapshot_completion(repo_name, snapshot_name)
                self.log(f"Elasticsearch snapshot '{snapshot_name}' created successfully")
                return snapshot_name
            return None
        except Exception as e:
            self.log(f"Failed to create snapshot: {e}", "ERROR")
            return None

    def wait_for_snapshot_completion(self, repo_name: str, snapshot_name: str, timeout: int = 300) -> bool:
        """スナップショット完了を待機"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.run_curl_command(
                    f"{self.es_url}/_snapshot/{repo_name}/{snapshot_name}"
                )
                if response:
                    snapshot_info = json.loads(response)

                    if snapshot_info['snapshots']:
                        state = snapshot_info['snapshots'][0]['state']
                        if state == 'SUCCESS':
                            self.log(f"Snapshot {snapshot_name} completed successfully")
                            return True
                        elif state == 'FAILED':
                            self.log(f"Snapshot {snapshot_name} failed", "ERROR")
                            return False

                    self.log(f"Snapshot {snapshot_name} in progress... ({state})")
                    time.sleep(10)
            except Exception as e:
                self.log(f"Error checking snapshot status: {e}", "ERROR")
                return False

        self.log(f"Snapshot {snapshot_name} timed out", "ERROR")
        return False

    def export_kibana_saved_objects(self) -> Optional[str]:
        """Kibana SavedObjectsをエクスポート（デフォルトファイル名）"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"kibana_saved_objects_{timestamp}.ndjson"
        return self._export_kibana_saved_objects_to_file(backup_file)

    def export_kibana_saved_objects_custom(self, output_file: str) -> Optional[str]:
        """Kibana SavedObjectsをエクスポート（カスタムファイル名）"""
        backup_file = Path(output_file)
        # 相対パスの場合はbackup_dirを基準にする
        if not backup_file.is_absolute():
            backup_file = self.backup_dir / backup_file

        # ディレクトリが存在しない場合は作成
        backup_file.parent.mkdir(parents=True, exist_ok=True)

        return self._export_kibana_saved_objects_to_file(backup_file)

    def _export_kibana_saved_objects_to_file(self, backup_file: Path) -> Optional[str]:
        """Kibana SavedObjectsを指定ファイルにエクスポート（内部メソッド）"""
        try:
            export_url = f"{self.kibana_url}/api/saved_objects/_export"
            export_config = {
                "type": ["dashboard", "visualization", "search", "index-pattern",
                        "config", "timelion-sheet", "graph-workspace", "map",
                        "lens", "canvas-workpad", "data-source"],
                "includeReferencesDeep": True
            }

            headers = {
                "Content-Type": "application/json",
                "kbn-xsrf": "true"
            }

            success = self.run_curl_command(
                export_url,
                method="POST",
                data=export_config,
                headers=headers,
                output_file=backup_file
            )

            if success and backup_file.exists():
                self.log(f"Kibana SavedObjects exported to: {backup_file}")
                return str(backup_file)
            else:
                self.log("Failed to export Kibana SavedObjects", "ERROR")
                return None
        except Exception as e:
            self.log(f"Failed to export Kibana SavedObjects: {e}", "ERROR")
            return None

    def import_kibana_saved_objects(self, backup_file: str, overwrite: bool = False) -> bool:
        """Kibana SavedObjectsをインポート"""
        try:
            import_url = f"{self.kibana_url}/api/saved_objects/_import"
            if overwrite:
                import_url += "?overwrite=true"

            cmd = [
                "curl", "-s", "-X", "POST",
                "-H", "kbn-xsrf: true",
                "-F", f"file=@{backup_file}",
                import_url
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if result.stdout:
                import_result = json.loads(result.stdout)
                self.log(f"Kibana SavedObjects import result: {import_result}")
                return True
            return False
        except subprocess.CalledProcessError as e:
            self.log(f"Failed to import Kibana SavedObjects: {e}", "ERROR")
            self.log(f"stderr: {e.stderr}", "ERROR")
            return False
        except Exception as e:
            self.log(f"Failed to import Kibana SavedObjects: {e}", "ERROR")
            return False

    def export_index_mapping(self, index_name: str) -> Optional[Dict[str, Any]]:
        """インデックスマッピングをエクスポート"""
        try:
            response = self.run_curl_command(f"{self.es_url}/{index_name}/_mapping")
            if response:
                return json.loads(response)
            return None
        except Exception as e:
            self.log(f"Failed to export mapping for {index_name}: {e}", "ERROR")
            return None

    def backup_full(self, indices: Optional[List[str]] = None) -> Optional[str]:
        """フルバックアップを実行"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = self.backup_dir / f"elk_backup_{timestamp}"
        backup_folder.mkdir(exist_ok=True)

        self.log("Starting full ELK Stack backup...")

        if not self.check_elasticsearch_health():
            self.log("Elasticsearch is not healthy, aborting backup", "ERROR")
            return None

        if not self.check_kibana_health():
            self.log("Kibana is not healthy, aborting backup", "ERROR")
            return None

        backup_info = {
            "timestamp": timestamp,
            "elasticsearch_url": self.es_url,
            "kibana_url": self.kibana_url,
            "indices": indices or self.get_indices(),
            "backup_components": []
        }

        # Elasticsearchスナップショット
        snapshot_name = self.create_elasticsearch_snapshot(
            f"backup_{timestamp}", indices
        )
        if snapshot_name:
            backup_info["backup_components"].append({
                "type": "elasticsearch_snapshot",
                "snapshot_name": snapshot_name,
                "repository": "backup_repo"
            })

        # Kibana SavedObjectsバックアップ
        kibana_backup = self.export_kibana_saved_objects()
        if kibana_backup:
            kibana_dest = backup_folder / "kibana_saved_objects.ndjson"
            shutil.copy2(kibana_backup, kibana_dest)
            backup_info["backup_components"].append({
                "type": "kibana_saved_objects",
                "file": "kibana_saved_objects.ndjson"
            })

        # インデックスマッピングのバックアップ
        if indices:
            mappings = {}
            for index in indices:
                mapping = self.export_index_mapping(index)
                if mapping:
                    mappings[index] = mapping

            if mappings:
                mappings_file = backup_folder / "index_mappings.json"
                with open(mappings_file, 'w') as f:
                    json.dump(mappings, f, indent=2)
                backup_info["backup_components"].append({
                    "type": "index_mappings",
                    "file": "index_mappings.json"
                })

        # バックアップ情報を保存
        info_file = backup_folder / "backup_info.json"
        with open(info_file, 'w') as f:
            json.dump(backup_info, f, indent=2)

        # アーカイブ作成
        archive_name = f"elk_backup_{timestamp}.tar.gz"
        archive_path = self.backup_dir / archive_name

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(backup_folder, arcname=f"elk_backup_{timestamp}")

        # 一時フォルダを削除
        shutil.rmtree(backup_folder)

        self.log(f"Full backup completed: {archive_path}")
        return str(archive_path)

    def restore_elasticsearch_snapshot(self, repo_name: str, snapshot_name: str,
                                     indices: Optional[List[str]] = None) -> bool:
        """Elasticsearchスナップショットをリストア"""
        restore_config = {
            "indices": ",".join(indices) if indices else "*",
            "ignore_unavailable": True,
            "include_global_state": True
        }

        try:
            headers = {"Content-Type": "application/json"}
            response = self.run_curl_command(
                f"{self.es_url}/_snapshot/{repo_name}/{snapshot_name}/_restore",
                method="POST",
                data=restore_config,
                headers=headers
            )
            if response is not None:
                self.log(f"Snapshot {snapshot_name} restore initiated")
                return True
            return False
        except Exception as e:
            self.log(f"Failed to restore snapshot: {e}", "ERROR")
            return False

    def list_snapshots(self, repo_name: str = "backup_repo") -> List[Dict[str, Any]]:
        """利用可能なスナップショット一覧を取得"""
        try:
            response = self.run_curl_command(f"{self.es_url}/_snapshot/{repo_name}/_all")
            if response:
                snapshots_data = json.loads(response)
                snapshots = snapshots_data['snapshots']

                self.log("\nAvailable snapshots:")
                self.log("-" * 80)
                for snapshot in snapshots:
                    self.log(f"Name: {snapshot['snapshot']}")
                    self.log(f"State: {snapshot['state']}")
                    self.log(f"Start time: {snapshot['start_time']}")
                    self.log(f"Indices: {len(snapshot['indices'])} indices")
                    self.log("-" * 80)

                return snapshots
            return []
        except Exception as e:
            self.log(f"Failed to list snapshots: {e}", "ERROR")
            return []

    def extract_backup_archive(self, archive_path: str) -> Optional[Path]:
        """バックアップアーカイブを展開"""
        try:
            extract_dir = self.backup_dir / "temp_restore"
            extract_dir.mkdir(exist_ok=True)

            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(extract_dir)

            extracted_folders = list(extract_dir.iterdir())
            if extracted_folders:
                return extracted_folders[0]
            return None
        except Exception as e:
            self.log(f"Failed to extract backup archive: {e}", "ERROR")
            return None