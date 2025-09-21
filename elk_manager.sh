#!/bin/bash

# ELK Stack Management Tool - Linux/macOS Wrapper

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[ERROR] Python is not installed."
    echo "Please install Python 3.7 or higher."
    exit 1
fi

# Determine Python executable
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# Check if command is provided
if [ $# -eq 0 ]; then
    echo "Usage: ./elk_manager.sh <command> [options]"
    echo
    echo "Available commands:"
    echo "  setup      - Run initial setup"
    echo "  start      - Start ELK stack"
    echo "  stop       - Stop ELK stack"
    echo "  restart    - Restart ELK stack (with updates)"
    echo "  logs       - Show logs"
    echo "  cleanup    - Run cleanup"
    echo "  backup     - Create ELK stack backup"
    echo "  restore    - Restore Elasticsearch snapshot"
    echo "  kibana-export-savedobject - Export Kibana SavedObjects"
    echo "  kibana-import-savedobject - Import Kibana SavedObjects"
    echo "  list-snapshots - List available snapshots"
    echo
    echo "Log command options:"
    echo "  -f, --follow    Follow log output"
    echo "  -t, --tail N    Show last N lines (default: 50)"
    echo "  -s, --status    Show service status"
    echo "  <service>       Show logs for specific service (elasticsearch, logstash, kibana)"
    echo
    echo "Backup command options:"
    echo "  --indices INDEX1 INDEX2    Backup specific indices only"
    echo "  --snapshot-name NAME       Snapshot name for restore"
    echo "  --backup-file FILE         Backup file for Kibana import"
    echo "  --output-file FILE         Output file for Kibana export"
    echo "  --overwrite               Overwrite existing objects during Kibana import"
    echo
    echo "Examples:"
    echo "  ./elk_manager.sh setup"
    echo "  ./elk_manager.sh start"
    echo "  ./elk_manager.sh stop"
    echo "  ./elk_manager.sh restart"
    echo "  ./elk_manager.sh logs"
    echo "  ./elk_manager.sh logs -f elasticsearch"
    echo "  ./elk_manager.sh logs -s"
    echo "  ./elk_manager.sh cleanup"
    echo "  ./elk_manager.sh backup"
    echo "  ./elk_manager.sh backup --indices myindex1 myindex2"
    echo "  ./elk_manager.sh restore --snapshot-name snapshot_20240101_120000"
    echo "  ./elk_manager.sh kibana-export-savedobject"
    echo "  ./elk_manager.sh kibana-export-savedobject --output-file my_export.ndjson"
    echo "  ./elk_manager.sh kibana-import-savedobject --backup-file backups/kibana_saved_objects.ndjson"
    echo "  ./elk_manager.sh list-snapshots"
    exit 1
fi

# Install Python dependencies for setup command
if [ "$1" = "setup" ]; then
    echo "Installing Python dependencies..."
    $PYTHON_CMD -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install Python dependencies."
        echo "Please check your Python installation and network connection."
        exit 1
    fi
    echo "Python dependencies installed successfully."
    echo
fi

# Execute elk_manager.py with all arguments
$PYTHON_CMD scripts/elk_manager.py "$@"
SCRIPT_RESULT=$?

# Show completion message for long-running commands
case "$1" in
    setup)
        if [ $SCRIPT_RESULT -eq 0 ]; then
            echo
            echo "Setup completed successfully."
        else
            echo
            echo "Setup failed."
        fi
        ;;
    start)
        if [ $SCRIPT_RESULT -eq 0 ]; then
            echo
            echo "Start completed successfully."
        else
            echo
            echo "Start failed."
        fi
        ;;
    stop)
        if [ $SCRIPT_RESULT -eq 0 ]; then
            echo
            echo "Stop completed successfully."
        else
            echo
            echo "Stop failed."
        fi
        ;;
    restart)
        if [ $SCRIPT_RESULT -eq 0 ]; then
            echo
            echo "Restart completed successfully."
        else
            echo
            echo "Restart failed."
        fi
        ;;
    cleanup)
        if [ $SCRIPT_RESULT -eq 0 ]; then
            echo
            echo "Cleanup completed successfully."
        else
            echo
            echo "Cleanup failed."
        fi
        ;;
    backup)
        if [ $SCRIPT_RESULT -eq 0 ]; then
            echo
            echo "Backup completed successfully."
        else
            echo
            echo "Backup failed."
        fi
        ;;
    restore)
        if [ $SCRIPT_RESULT -eq 0 ]; then
            echo
            echo "Restore completed successfully."
        else
            echo
            echo "Restore failed."
        fi
        ;;
    kibana-export-savedobject)
        if [ $SCRIPT_RESULT -eq 0 ]; then
            echo
            echo "Kibana export completed successfully."
        else
            echo
            echo "Kibana export failed."
        fi
        ;;
    kibana-import-savedobject)
        if [ $SCRIPT_RESULT -eq 0 ]; then
            echo
            echo "Kibana import completed successfully."
        else
            echo
            echo "Kibana import failed."
        fi
        ;;
    list-snapshots)
        if [ $SCRIPT_RESULT -eq 0 ]; then
            echo
            echo "Snapshot list displayed successfully."
        else
            echo
            echo "Failed to list snapshots."
        fi
        ;;
esac

exit $SCRIPT_RESULT