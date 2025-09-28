#!/bin/bash

# Waterbook Public startup script
# For quickly starting the Waterbook Public application

set -e  # Exit on error

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APP_NAME="Waterbook Public"
PYTHON_CMD="python3"
APP_FILE="app.py"
REQUIREMENTS_FILE="requirements.txt"
CONFIG_FILE="config.yaml"

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Show help information
show_help() {
    echo "$APP_NAME Startup Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help information"
    echo "  -i, --install       Install dependencies"
    echo "  -c, --check         Check system environment"
    echo "  -d, --dev           Run in development mode"
    echo "  -s, --service       Run in service mode"
    echo "  -k, --kill          Stop running instances"
    echo "  -l, --log           Show logs"
    echo "  --no-gpio          Disable GPIO, use keyboard simulation"
    echo "  --virtual-audio    Use virtual audio recording"
    echo ""
    echo "Examples:"
    echo "  $0                  # Start application normally"
    echo "  $0 -i               # Install dependencies then start"
    echo "  $0 -c               # Check environment"
    echo "  $0 --no-gpio        # Run in non-Raspberry Pi environment"
}

# Check Python environment
check_python() {
    log_info "Checking Python environment..."
    
    if ! command -v $PYTHON_CMD &> /dev/null; then
        log_error "Python3 is not installed or not in PATH"
        return 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    log_success "Python version: $PYTHON_VERSION"
    
    # Check if Python version >= 3.8
    if $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_success "Python version meets requirements (>=3.8)"
    else
        log_error "Python version too low, requires 3.8 or higher"
        return 1
    fi
}

# Check system environment
check_environment() {
    log_info "Checking system environment..."
    
    # Check operating system
    OS=$(uname -s)
    log_info "Operating system: $OS"
    
    # Check if it's Raspberry Pi
    if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
        log_success "Raspberry Pi environment detected"
        export WATERBOOK_RASPBERRY_PI=1
    else
        log_warning "Non-Raspberry Pi environment, will use keyboard simulation for GPIO"
        export WATERBOOK_RASPBERRY_PI=0
    fi
    
    # Check audio devices
    if command -v aplay &> /dev/null; then
        AUDIO_DEVICES=$(aplay -l 2>/dev/null | grep "card" | wc -l)
        if [ "$AUDIO_DEVICES" -gt 0 ]; then
            log_success "Detected $AUDIO_DEVICES audio devices"
        else
            log_warning "No audio devices detected"
        fi
    else
        log_warning "Cannot check audio devices"
    fi
    
    # Check display environment
    if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
        log_success "Graphics display environment detected"
    else
        log_warning "No graphics display environment detected, may need configuration"
    fi
}

# Install dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    if [ ! -f "$PROJECT_DIR/$REQUIREMENTS_FILE" ]; then
        log_error "requirements.txt file not found"
        return 1
    fi
    
    # Check if pip is available
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is not installed"
        return 1
    fi
    
    # Install dependencies
    log_info "Installing dependency packages..."
    if pip3 install -r "$PROJECT_DIR/$REQUIREMENTS_FILE"; then
        log_success "Dependencies installed successfully"
    else
        log_error "Failed to install dependencies"
        return 1
    fi
    
    # Try to install Raspberry Pi GPIO (if on Raspberry Pi)
    if [ "${WATERBOOK_RASPBERRY_PI:-0}" = "1" ]; then
        log_info "Installing Raspberry Pi GPIO library..."
        pip3 install RPi.GPIO || log_warning "RPi.GPIO installation failed, will use keyboard simulation"
    fi
}

# Check configuration file
check_config() {
    log_info "Checking configuration file..."
    
    if [ ! -f "$PROJECT_DIR/$CONFIG_FILE" ]; then
        log_error "Configuration file not found: $CONFIG_FILE"
        return 1
    fi
    
    log_success "Configuration file exists: $CONFIG_FILE"
    
    # Check required directories
    REQUIRED_DIRS=("assets" "www" "scripts")
    for dir in "${REQUIRED_DIRS[@]}"; do
        if [ ! -d "$PROJECT_DIR/$dir" ]; then
            log_warning "Creating directory: $dir"
            mkdir -p "$PROJECT_DIR/$dir"
        fi
    done
}

# Stop running instances
kill_instances() {
    log_info "Looking for running Waterbook instances..."
    
    PIDS=$(pgrep -f "python.*app.py" || true)
    if [ -n "$PIDS" ]; then
        log_info "Found running instances, PID: $PIDS"
        echo "$PIDS" | xargs kill -TERM
        sleep 2
        
        # Check for remaining processes
        REMAINING=$(pgrep -f "python.*app.py" || true)
        if [ -n "$REMAINING" ]; then
            log_warning "Force terminating remaining processes: $REMAINING"
            echo "$REMAINING" | xargs kill -KILL
        fi
        
        log_success "Stopped running instances"
    else
        log_info "No running instances found"
    fi
}

# Show logs
show_logs() {
    LOG_FILE="$PROJECT_DIR/waterbook.log"
    if [ -f "$LOG_FILE" ]; then
        log_info "Showing recent logs (press Ctrl+C to exit):"
        tail -f "$LOG_FILE"
    else
        log_warning "Log file does not exist: $LOG_FILE"
    fi
}

# Start application
start_app() {
    local dev_mode=${1:-false}
    local no_gpio=${2:-false}
    local virtual_audio=${3:-false}
    
    log_info "Starting $APP_NAME..."
    
    # Switch to project directory
    cd "$PROJECT_DIR"
    
    # Set environment variables
    export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
    
    if [ "$no_gpio" = "true" ]; then
        export WATERBOOK_NO_GPIO=1
        log_info "GPIO disabled, using keyboard simulation"
    fi
    
    if [ "$virtual_audio" = "true" ]; then
        export WATERBOOK_VIRTUAL_AUDIO=1
        log_info "Using virtual audio recording"
    fi
    
    # Start application
    if [ "$dev_mode" = "true" ]; then
        log_info "Starting in development mode..."
        $PYTHON_CMD "$APP_FILE" --dev
    else
        log_info "Starting in normal mode..."
        $PYTHON_CMD "$APP_FILE"
    fi
}

# Main function
main() {
    local install_deps=false
    local check_env=false
    local dev_mode=false
    local service_mode=false
    local kill_mode=false
    local show_logs_mode=false
    local no_gpio=false
    local virtual_audio=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -i|--install)
                install_deps=true
                shift
                ;;
            -c|--check)
                check_env=true
                shift
                ;;
            -d|--dev)
                dev_mode=true
                shift
                ;;
            -s|--service)
                service_mode=true
                shift
                ;;
            -k|--kill)
                kill_mode=true
                shift
                ;;
            -l|--log)
                show_logs_mode=true
                shift
                ;;
            --no-gpio)
                no_gpio=true
                shift
                ;;
            --virtual-audio)
                virtual_audio=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Show startup information
    echo "="*50
    echo "  $APP_NAME Startup Script"
    echo "  Project Directory: $PROJECT_DIR"
    echo "="*50
    echo ""
    
    # Execute operations
    if [ "$kill_mode" = "true" ]; then
        kill_instances
        exit 0
    fi
    
    if [ "$show_logs_mode" = "true" ]; then
        show_logs
        exit 0
    fi
    
    # Check Python environment
    if ! check_python; then
        exit 1
    fi
    
    # Check system environment
    if [ "$check_env" = "true" ]; then
        check_environment
        exit 0
    fi
    
    # Install dependencies
    if [ "$install_deps" = "true" ]; then
        if ! install_dependencies; then
            exit 1
        fi
    fi
    
    # Check configuration
    if ! check_config; then
        exit 1
    fi
    
    # Check environment (simplified version)
    check_environment
    
    # Start application
    if [ "$service_mode" = "true" ]; then
        log_info "Starting in service mode (background)..."
        nohup $0 > "$PROJECT_DIR/waterbook.log" 2>&1 &
        log_success "Service started, PID: $!"
        log_info "Use '$0 -l' to view logs"
        log_info "Use '$0 -k' to stop service"
    else
        start_app "$dev_mode" "$no_gpio" "$virtual_audio"
    fi
}

# Signal handling
trap 'log_info "Received interrupt signal, exiting..."; exit 0' INT TERM

# Run main function
main "$@"