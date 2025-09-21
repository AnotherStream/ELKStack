#!/usr/bin/env python3
"""
環境変数・ファイル管理モジュール
環境変数の読み込みと設定ファイルの検証機能を提供
"""

import os
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List

class EnvironmentManager:
    """環境変数とファイル管理を行うクラス"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.env_file = self.project_root / ".env"
        self.env_template = self.project_root / ".env.template"
        self.docker_compose_file = self.project_root / "docker-compose.yml"

    def log(self, message: str, level: str = "INFO") -> None:
        """ログメッセージを出力"""
        print(f"[{level}] {message}")

    def load_env_variables(self) -> Dict[str, str]:
        """環境変数を読み込み"""
        env_vars = {}
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
            return env_vars
        except Exception as e:
            self.log(f"環境変数の読み込みに失敗しました: {e}", "ERROR")
            return {}

    def check_env_file(self) -> bool:
        """環境変数ファイルの存在確認"""
        self.log("環境変数ファイルの確認中...")

        if not self.env_file.exists():
            self.log(f".envファイルが見つかりません: {self.env_file}", "ERROR")
            self.log("テンプレートファイルを参考に.envファイルを作成してください:", "ERROR")
            self.log("- .env.template (LDAP認証なし)", "ERROR")
            self.log("- .env.template-ldap (LDAP認証あり)", "ERROR")
            return False

        self.log(f".envファイルを確認しました: {self.env_file}")
        return True

    def check_docker_compose_file(self) -> bool:
        """Docker Composeファイルの存在確認"""
        self.log("Docker Composeファイルの確認中...")

        if not self.docker_compose_file.exists():
            self.log(f"docker-compose.ymlファイルが見つかりません: {self.docker_compose_file}", "ERROR")
            self.log("テンプレートファイルを参考にdocker-compose.ymlファイルを作成してください:", "ERROR")
            self.log("- docker-compose.yml.template (LDAP認証なし)", "ERROR")
            self.log("- docker-compose.yml.template-ldap (LDAP認証あり)", "ERROR")
            return False

        self.log(f"docker-compose.ymlファイルを確認しました: {self.docker_compose_file}")
        return True

    def check_certificates(self) -> bool:
        """証明書ファイルの確認（LDAP認証時のみ）"""
        self.log("証明書ファイルの確認中...")

        env_vars = self.load_env_variables()

        # LDAP認証が有効かどうかを確認
        if 'ELASTIC_PASSWORD' not in env_vars or not env_vars['ELASTIC_PASSWORD']:
            self.log("LDAP認証が無効のため、証明書チェックをスキップします")
            return True

        cert_vars = [
            'CA_CERT_PATH',
            'ELASTICSEARCH_CERT_PATH', 'ELASTICSEARCH_KEY_PATH',
            'KIBANA_CERT_PATH', 'KIBANA_KEY_PATH',
            'LOGSTASH_CERT_PATH', 'LOGSTASH_KEY_PATH'
        ]

        missing_files = []
        for cert_var in cert_vars:
            if cert_var not in env_vars or not env_vars[cert_var]:
                self.log(f"証明書パスが設定されていません: {cert_var}", "ERROR")
                return False

            cert_path = Path(env_vars[cert_var])
            if not cert_path.exists():
                missing_files.append(f"{cert_var}: {cert_path}")

        if missing_files:
            self.log("以下の証明書ファイルが見つかりません:", "ERROR")
            for missing in missing_files:
                self.log(f"  - {missing}", "ERROR")
            self.log("certs/ディレクトリに必要な証明書ファイルを配置してください", "ERROR")
            self.log("詳細はcerts/README.mdを参照してください", "ERROR")
            return False

        self.log("証明書ファイルの確認完了")
        return True

    def create_directories(self) -> bool:
        """必要なディレクトリを作成"""
        self.log("必要なディレクトリを作成中...")

        directories = [
            "Volumes/Elasticsearch/data",
            "Volumes/Kibana/data",
            "Volumes/Logstash/data",
            "backups"
        ]

        try:
            for dir_path in directories:
                full_path = self.project_root / dir_path
                full_path.mkdir(parents=True, exist_ok=True)
                self.log(f"ディレクトリを作成: {full_path}")
            return True
        except Exception as e:
            self.log(f"ディレクトリの作成に失敗しました: {e}", "ERROR")
            return False

    def set_permissions(self) -> bool:
        """権限の設定（Linux/macOS用）"""
        if platform.system() == "Windows":
            self.log("Windowsでは権限設定をスキップします")
            return True

        self.log("ディレクトリの権限を設定中...")

        try:
            data_dirs = [
                self.project_root / "Volumes" / "Elasticsearch" / "data",
                self.project_root / "Volumes" / "Kibana" / "data",
                self.project_root / "Volumes" / "Logstash" / "data"
            ]

            for dir_path in data_dirs:
                if dir_path.exists():
                    subprocess.run(['sudo', 'chown', '-R', '1000:1000', str(dir_path)],
                                 check=True)
                    subprocess.run(['sudo', 'chmod', '-R', '755', str(dir_path)],
                                 check=True)
                    self.log(f"権限を設定: {dir_path}")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"権限設定に失敗しました: {e}", "ERROR")
            self.log("手動で以下のコマンドを実行してください:", "WARNING")
            self.log("sudo chown -R 1000:1000 Volumes/", "WARNING")
            self.log("sudo chmod -R 755 Volumes/", "WARNING")
            return False

    def configure_vm_max_map_count(self) -> bool:
        """vm.max_map_countの設定（Linux用）"""
        if platform.system() != "Linux":
            self.log("Linux以外のOSでは vm.max_map_count の設定をスキップします")
            return True

        self.log("vm.max_map_countの設定を確認中...")

        try:
            result = subprocess.run(['sysctl', 'vm.max_map_count'],
                                  capture_output=True, text=True, check=True)
            current_value = int(result.stdout.split('=')[1].strip())
            required_value = 262144

            if current_value >= required_value:
                self.log(f"vm.max_map_countは既に適切に設定されています: {current_value}")
                return True

            self.log(f"vm.max_map_countを{required_value}に設定中...")

            subprocess.run(['sudo', 'sysctl', '-w', f'vm.max_map_count={required_value}'],
                         check=True)

            sysctl_conf = Path('/etc/sysctl.conf')
            if sysctl_conf.exists():
                with open(sysctl_conf, 'a') as f:
                    f.write(f'\nvm.max_map_count={required_value}\n')

            self.log(f"vm.max_map_countを{required_value}に設定しました")
            return True

        except (subprocess.CalledProcessError, FileNotFoundError, PermissionError) as e:
            self.log(f"vm.max_map_countの設定に失敗しました: {e}", "ERROR")
            self.log("手動で以下のコマンドを実行してください:", "WARNING")
            self.log(f"sudo sysctl -w vm.max_map_count={required_value}", "WARNING")
            return False

    def clean_data_directories(self) -> bool:
        """データディレクトリのクリーンアップ"""
        self.log("データディレクトリをクリーンアップ中...")

        data_dirs = [
            self.project_root / "Volumes" / "Elasticsearch" / "data",
            self.project_root / "Volumes" / "Kibana" / "data",
            self.project_root / "Volumes" / "Logstash" / "data"
        ]

        try:
            for dir_path in data_dirs:
                if dir_path.exists():
                    for item in dir_path.iterdir():
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                    self.log(f"クリーンアップ完了: {dir_path}")
                else:
                    self.log(f"ディレクトリが存在しません: {dir_path}")

            return True
        except Exception as e:
            self.log(f"データディレクトリのクリーンアップに失敗しました: {e}", "ERROR")
            self.log("権限の問題の可能性があります。以下のコマンドを試してください:", "WARNING")
            self.log("sudo rm -rf Volumes/*/data/*", "WARNING")
            return False