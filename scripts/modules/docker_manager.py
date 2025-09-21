#!/usr/bin/env python3
"""
Docker管理モジュール
Docker関連の操作とヘルスチェック機能を提供
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

class DockerManager:
    """Docker関連の操作を管理するクラス"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.docker_compose_file = self.project_root / "docker-compose.yml"

        # サービスのヘルスチェック設定
        self.health_checks = {
            "elasticsearch": {
                "url": "http://localhost:9200/_cluster/health",
                "timeout": 300,
                "interval": 10
            },
            "kibana": {
                "url": "http://localhost:5601/api/status",
                "timeout": 300,
                "interval": 10
            },
            "logstash": {
                "url": "http://localhost:9600/_node/stats",
                "timeout": 300,
                "interval": 10
            }
        }

    def log(self, message: str, level: str = "INFO") -> None:
        """ログメッセージを出力"""
        print(f"[{level}] {message}")

    def get_docker_compose_command(self) -> Optional[List[str]]:
        """利用可能なDocker Composeコマンドを取得"""
        commands = [
            ['docker-compose'],
            ['docker', 'compose']
        ]

        for cmd in commands:
            try:
                subprocess.run(cmd + ['--version'],
                              capture_output=True, text=True, check=True)
                return cmd
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

        return None

    def check_docker_requirements(self) -> bool:
        """Docker関連の要件をチェック"""
        self.log("Docker関連の要件をチェック中...")

        # Docker の確認
        try:
            result = subprocess.run(['docker', '--version'],
                                  capture_output=True, text=True, check=True)
            self.log(f"Docker: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("Dockerがインストールされていません", "ERROR")
            return False

        # Docker Compose の確認
        compose_cmd = self.get_docker_compose_command()
        if not compose_cmd:
            self.log("Docker Composeがインストールされていません", "ERROR")
            return False

        return True

    def check_service_health(self, url: str) -> bool:
        """curlを使用してサービスのヘルスチェックを実行"""
        try:
            result = subprocess.run(
                ['curl', '-f', '-s', url],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def wait_for_service(self, service_name: str) -> bool:
        """サービスの起動を待機"""
        if service_name not in self.health_checks:
            self.log(f"未知のサービス: {service_name}", "WARNING")
            return True

        config = self.health_checks[service_name]
        url = config["url"]
        timeout = config["timeout"]
        interval = config["interval"]

        self.log(f"{service_name}の起動を確認中...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.check_service_health(url):
                self.log(f"✓ {service_name} が起動しました")
                return True

            elapsed = int(time.time() - start_time)
            self.log(f"{service_name} の起動を待機中... ({elapsed}/{timeout}秒)")
            time.sleep(interval)

        self.log(f"⚠ {service_name} の起動確認がタイムアウトしました", "WARNING")
        return False

    def start_services(self) -> bool:
        """サービスを起動"""
        self.log("ELK Stack を起動中...")

        compose_cmd = self.get_docker_compose_command()
        try:
            subprocess.run(
                compose_cmd + ['up', '-d'],
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True
            )
            self.log("ELK Stack の起動完了")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"サービスの起動に失敗しました: {e.stderr}", "ERROR")
            return False

    def stop_containers(self, remove_volumes: bool = False) -> bool:
        """既存のコンテナを停止"""
        self.log("既存のコンテナを停止中...")

        compose_cmd = self.get_docker_compose_command()
        try:
            cmd = compose_cmd + ['down']
            if remove_volumes:
                cmd.append('-v')

            subprocess.run(
                cmd,
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True
            )
            self.log("既存のコンテナを停止しました")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"コンテナの停止に失敗しました: {e.stderr}", "WARNING")
            return True

    def pull_images(self) -> bool:
        """Dockerイメージを更新"""
        self.log("Dockerイメージを更新中...")

        compose_cmd = self.get_docker_compose_command()
        try:
            subprocess.run(
                compose_cmd + ['pull'],
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True
            )
            self.log("Dockerイメージの更新完了")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"イメージの更新に失敗しました: {e.stderr}", "WARNING")
            return True

    def show_logs(self, service: Optional[str] = None, follow: bool = False, tail: int = 50) -> bool:
        """ログを表示"""
        compose_cmd = self.get_docker_compose_command()
        if not compose_cmd:
            self.log("Docker Composeが利用できません", "ERROR")
            return False

        services = ["elasticsearch", "logstash", "kibana"]

        try:
            cmd = compose_cmd + ['logs']

            if tail > 0:
                cmd.extend(['--tail', str(tail)])

            if follow:
                cmd.append('-f')

            if service:
                if service not in services:
                    self.log(f"未知のサービス: {service}", "ERROR")
                    self.log(f"利用可能なサービス: {', '.join(services)}")
                    return False
                cmd.append(service)

            subprocess.run(
                cmd,
                cwd=self.project_root,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"ログの表示に失敗しました: {e}", "ERROR")
            return False
        except KeyboardInterrupt:
            print("\nログ表示を終了しました")
            return True

    def show_service_status(self) -> bool:
        """サービスの状態を表示"""
        compose_cmd = self.get_docker_compose_command()
        if not compose_cmd:
            self.log("Docker Composeが利用できません", "ERROR")
            return False

        try:
            subprocess.run(
                compose_cmd + ['ps'],
                cwd=self.project_root,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"サービス状態の表示に失敗しました: {e}", "ERROR")
            return False

    def check_all_services(self) -> bool:
        """全サービスの状態確認"""
        self.log("サービスの状態を確認中...")

        time.sleep(10)

        services = ["elasticsearch", "kibana", "logstash"]
        all_healthy = True

        for service in services:
            if not self.wait_for_service(service):
                all_healthy = False

        return all_healthy