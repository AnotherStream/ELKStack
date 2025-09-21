@echo off
setlocal

REM ELK Stack Management Tool - Windows Wrapper

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed.
    echo Please install Python 3.7 or higher.
    pause
    exit /b 1
)

REM Check if command is provided
if "%1"=="" (
    echo Usage: elk_manager.bat ^<command^> [options]
    echo.
    echo Available commands:
    echo   setup      - Run initial setup
    echo   start      - Start ELK stack
    echo   stop       - Stop ELK stack
    echo   restart    - Restart ELK stack ^(with updates^)
    echo   logs       - Show logs
    echo   cleanup    - Run cleanup
    echo   backup     - Create ELK stack backup
    echo   restore    - Restore Elasticsearch snapshot
    echo   kibana-export-savedobject - Export Kibana SavedObjects
    echo   kibana-import-savedobject - Import Kibana SavedObjects
    echo   list-snapshots - List available snapshots
    echo.
    echo Log command options:
    echo   -f, --follow    Follow log output
    echo   -t, --tail N    Show last N lines ^(default: 50^)
    echo   -s, --status    Show service status
    echo   ^<service^>       Show logs for specific service ^(elasticsearch, logstash, kibana^)
    echo.
    echo Backup command options:
    echo   --indices INDEX1 INDEX2    Backup specific indices only
    echo   --snapshot-name NAME       Snapshot name for restore
    echo   --backup-file FILE         Backup file for Kibana import
    echo   --output-file FILE         Output file for Kibana export
    echo   --overwrite               Overwrite existing objects during Kibana import
    echo.
    echo Examples:
    echo   elk_manager.bat setup
    echo   elk_manager.bat start
    echo   elk_manager.bat stop
    echo   elk_manager.bat restart
    echo   elk_manager.bat logs
    echo   elk_manager.bat logs -f elasticsearch
    echo   elk_manager.bat logs -s
    echo   elk_manager.bat cleanup
    echo   elk_manager.bat backup
    echo   elk_manager.bat backup --indices myindex1 myindex2
    echo   elk_manager.bat restore --snapshot-name snapshot_20240101_120000
    echo   elk_manager.bat kibana-export-savedobject
    echo   elk_manager.bat kibana-export-savedobject --output-file my_export.ndjson
    echo   elk_manager.bat kibana-import-savedobject --backup-file backups\kibana_saved_objects.ndjson
    echo   elk_manager.bat list-snapshots
    pause
    exit /b 1
)

REM Install Python dependencies for setup command
if "%1"=="setup" (
    echo Installing Python dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install Python dependencies.
        echo Please check your Python installation and network connection.
        pause
        exit /b 1
    )
    echo Python dependencies installed successfully.
    echo.
)

REM Execute elk_manager.py with all arguments
python scripts\elk_manager.py %*
set SCRIPT_RESULT=%ERRORLEVEL%

REM Show completion message for long-running commands
if "%1"=="setup" (
    if %SCRIPT_RESULT% equ 0 (
        echo.
        echo Setup completed successfully.
        pause
    ) else (
        echo.
        echo Setup failed.
        pause
    )
) else if "%1"=="start" (
    if %SCRIPT_RESULT% equ 0 (
        echo.
        echo Start completed successfully.
        pause
    ) else (
        echo.
        echo Start failed.
        pause
    )
) else if "%1"=="stop" (
    if %SCRIPT_RESULT% equ 0 (
        echo.
        echo Stop completed successfully.
        pause
    ) else (
        echo.
        echo Stop failed.
        pause
    )
) else if "%1"=="restart" (
    if %SCRIPT_RESULT% equ 0 (
        echo.
        echo Restart completed successfully.
        pause
    ) else (
        echo.
        echo Restart failed.
        pause
    )
) else if "%1"=="cleanup" (
    if %SCRIPT_RESULT% equ 0 (
        echo.
        echo Cleanup completed successfully.
        pause
    ) else (
        echo.
        echo Cleanup failed.
        pause
    )
) else if "%1"=="backup" (
    if %SCRIPT_RESULT% equ 0 (
        echo.
        echo Backup completed successfully.
        pause
    ) else (
        echo.
        echo Backup failed.
        pause
    )
) else if "%1"=="restore" (
    if %SCRIPT_RESULT% equ 0 (
        echo.
        echo Restore completed successfully.
        pause
    ) else (
        echo.
        echo Restore failed.
        pause
    )
) else if "%1"=="kibana-export-savedobject" (
    if %SCRIPT_RESULT% equ 0 (
        echo.
        echo Kibana export completed successfully.
        pause
    ) else (
        echo.
        echo Kibana export failed.
        pause
    )
) else if "%1"=="kibana-import-savedobject" (
    if %SCRIPT_RESULT% equ 0 (
        echo.
        echo Kibana import completed successfully.
        pause
    ) else (
        echo.
        echo Kibana import failed.
        pause
    )
) else if "%1"=="list-snapshots" (
    if %SCRIPT_RESULT% equ 0 (
        echo.
        echo Snapshot list displayed successfully.
        pause
    ) else (
        echo.
        echo Failed to list snapshots.
        pause
    )
)

exit /b %SCRIPT_RESULT%