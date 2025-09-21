#!/usr/bin/env python3
"""
クリーンアップ管理モジュール
Docker イメージ・コンテナ・データのクリーンアップ機能を提供
"""

import subprocess
from pathlib import Path
from typing import List

class CleanupManager:
    """クリーンアップ処理を管理するクラス"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def log(self, message: str, level: str = "INFO") -> None:
        """ログメッセージを出力"""
        print(f"[{level}] {message}")

    def confirm_action(self, message: str) -> bool:
        """ユーザーに確認を求める"""
        while True:
            response = input(f"{message} (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no', '']:
                return False
            else:
                print("'y' または 'n' で回答してください。")

    def remove_elk_images(self) -> bool:
        """ELK関連のDockerイメージを削除"""
        self.log("ELK関連のDockerイメージを削除中...")

        try:
            result = subprocess.run(
                ['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}'],
                capture_output=True,
                text=True,
                check=True
            )

            elk_images = []
            for line in result.stdout.strip().split('\n'):
                if any(keyword in line.lower() for keyword in ['elastic', 'logstash', 'kibana']):
                    elk_images.append(line.strip())

            if not elk_images:
                self.log("削除対象のELKイメージが見つかりませんでした")
                return True

            self.log(f"削除対象のイメージ: {len(elk_images)}個")
            for image in elk_images:
                self.log(f"  - {image}")

            for image in elk_images:
                try:
                    subprocess.run(
                        ['docker', 'rmi', '-f', image],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    self.log(f"削除完了: {image}")
                except subprocess.CalledProcessError as e:
                    self.log(f"削除失敗: {image} - {e.stderr}", "WARNING")

            return True
        except subprocess.CalledProcessError as e:
            self.log(f"イメージの削除に失敗しました: {e}", "ERROR")
            return False

    def clean_docker_system(self) -> bool:
        """未使用のDockerリソースをクリーンアップ"""
        self.log("未使用のDockerリソースをクリーンアップ中...")

        try:
            subprocess.run(
                ['docker', 'system', 'prune', '-f'],
                capture_output=True,
                text=True,
                check=True
            )
            self.log("Dockerシステムのクリーンアップ完了")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Dockerシステムのクリーンアップに失敗しました: {e}", "ERROR")
            return False

    def show_cleanup_summary(self) -> None:
        """クリーンアップの概要を表示"""
        self.log("=== クリーンアップ概要 ===")
        self.log("以下の項目をクリーンアップできます:")
        self.log("1. コンテナの停止・削除")
        self.log("2. ELK関連Dockerイメージの削除")
        self.log("3. データディレクトリのクリーンアップ")
        self.log("4. 未使用Dockerリソースのクリーンアップ")
        print()