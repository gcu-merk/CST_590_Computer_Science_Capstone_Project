#!/bin/bash
# User Storage Optimization Script
# Moves large user data directories from SD card to SSD for better performance
# Run this script on Raspberry Pi: bash scripts/optimize-user-storage.sh

set -e  # Exit on error

echo "🚀 User Storage Optimization Script - $(date)"
echo "Moving large user data from SD card to SSD"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SSD_BASE="/mnt/storage"
USER_DATA_DIR="$SSD_BASE/user_data"
BACKUP_DIR="$SSD_BASE/user_optimization_backup_$(date +%Y%m%d_%H%M%S)"

# Function to print colored output
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

info() {
    echo -e "${BLUE}📋 $1${NC}"
}

# Function to check if running as the correct user
check_user() {
    if [ "$USER" != "merk" ]; then
        error "This script should be run as user 'merk', not root"
        echo "Run: bash scripts/optimize-user-storage.sh"
        exit 1
    fi
    success "Running as correct user: $USER"
}

# Function to check SSD availability
check_ssd() {
    if [ ! -d "$SSD_BASE" ]; then
        error "SSD not mounted at $SSD_BASE"
        exit 1
    fi
    
    # Check write access
    if [ ! -w "$SSD_BASE" ]; then
        error "No write access to SSD at $SSD_BASE"
        exit 1
    fi
    
    success "SSD available and writable at $SSD_BASE"
}

# Function to create backup directory
create_backup_dir() {
    info "Creating backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    success "Backup directory created"
}

# Function to create user data structure on SSD
create_user_data_structure() {
    info "Creating user data structure on SSD..."
    
    mkdir -p "$USER_DATA_DIR"
    mkdir -p "$USER_DATA_DIR/vscode-server"
    mkdir -p "$USER_DATA_DIR/actions-runner"
    mkdir -p "$USER_DATA_DIR/github-cache"
    
    # Set proper permissions
    chmod 755 "$USER_DATA_DIR"
    chmod 755 "$USER_DATA_DIR/vscode-server"
    chmod 755 "$USER_DATA_DIR/actions-runner"
    chmod 755 "$USER_DATA_DIR/github-cache"
    
    success "User data structure created on SSD"
}

# Function to move VS Code server data
move_vscode_server() {
    local source_dir="/home/merk/.vscode-server"
    local target_dir="$USER_DATA_DIR/vscode-server"
    
    info "Moving VS Code server data..."
    
    if [ -d "$source_dir" ] && [ ! -L "$source_dir" ]; then
        # Get size for reporting
        local size=$(du -sh "$source_dir" | cut -f1)
        info "VS Code server data size: $size"
        
        # Create backup
        info "Creating backup of VS Code server data..."
        cp -r "$source_dir" "$BACKUP_DIR/"
        
        # Stop any VS Code server processes (optional)
        pkill -f "vscode-server" 2>/dev/null || true
        sleep 2
        
        # Move data to SSD
        info "Moving VS Code server data to SSD..."
        mv "$source_dir"/* "$target_dir/" 2>/dev/null || true
        
        # Remove original directory
        rm -rf "$source_dir"
        
        # Create symlink
        ln -sf "$target_dir" "$source_dir"
        
        success "VS Code server data moved to SSD ($size freed from SD card)"
        
    elif [ -L "$source_dir" ]; then
        warning "VS Code server data already appears to be symlinked"
        ls -la "$source_dir"
        
    else
        warning "VS Code server directory not found at $source_dir"
    fi
}

# Function to move GitHub Actions runner data
move_actions_runner() {
    local source_dir="/home/merk/actions-runner"
    local target_dir="$USER_DATA_DIR/actions-runner"
    
    info "Moving GitHub Actions runner data..."
    
    if [ -d "$source_dir" ] && [ ! -L "$source_dir" ]; then
        # Get size for reporting
        local size=$(du -sh "$source_dir" | cut -f1)
        info "Actions runner data size: $size"
        
        # Create backup
        info "Creating backup of Actions runner data..."
        cp -r "$source_dir" "$BACKUP_DIR/"
        
        # Stop any runner processes (be careful here)
        warning "Note: This will not stop running GitHub Actions jobs"
        
        # Move data to SSD
        info "Moving Actions runner data to SSD..."
        mv "$source_dir"/* "$target_dir/" 2>/dev/null || true
        
        # Remove original directory
        rm -rf "$source_dir"
        
        # Create symlink
        ln -sf "$target_dir" "$source_dir"
        
        success "GitHub Actions runner data moved to SSD ($size freed from SD card)"
        
    elif [ -L "$source_dir" ]; then
        warning "Actions runner data already appears to be symlinked"
        ls -la "$source_dir"
        
    else
        warning "Actions runner directory not found at $source_dir"
    fi
}

# Function to verify moves
verify_moves() {
    info "Verifying symlinks and data integrity..."
    
    echo ""
    echo "Symlink verification:"
    ls -la /home/merk/.vscode-server 2>/dev/null || echo "  VS Code server: Not found"
    ls -la /home/merk/actions-runner 2>/dev/null || echo "  Actions runner: Not found"
    
    echo ""
    echo "SSD data verification:"
    if [ -d "$USER_DATA_DIR/vscode-server" ]; then
        local vscode_size=$(du -sh "$USER_DATA_DIR/vscode-server" | cut -f1)
        echo "  VS Code server on SSD: $vscode_size"
    fi
    
    if [ -d "$USER_DATA_DIR/actions-runner" ]; then
        local runner_size=$(du -sh "$USER_DATA_DIR/actions-runner" | cut -f1)
        echo "  Actions runner on SSD: $runner_size"
    fi
    
    success "Verification complete"
}

# Function to show storage impact
show_storage_impact() {
    info "Storage impact analysis..."
    
    echo ""
    echo "Before/After SD card usage:"
    df -h / | tail -1
    
    echo ""
    echo "SSD usage:"
    df -h /mnt/storage | tail -1
    
    echo ""
    echo "User data on SSD:"
    du -sh "$USER_DATA_DIR"/* 2>/dev/null || echo "  No user data found"
    
    success "Storage analysis complete"
}

# Main execution
main() {
    echo -e "\n${BLUE}Starting user storage optimization...${NC}"
    
    check_user
    check_ssd
    create_backup_dir
    create_user_data_structure
    
    echo -e "\n${BLUE}Moving user data to SSD...${NC}"
    move_vscode_server
    move_actions_runner
    
    echo -e "\n${BLUE}Verification and analysis...${NC}"
    verify_moves
    show_storage_impact
    
    echo -e "\n${GREEN}🎉 User storage optimization complete!${NC}"
    echo ""
    echo "Summary:"
    echo "- VS Code server data moved to SSD"
    echo "- GitHub Actions runner data moved to SSD" 
    echo "- Symlinks created for compatibility"
    echo "- Backup created at: $BACKUP_DIR"
    echo ""
    echo "Benefits:"
    echo "- Reduced SD card wear"
    echo "- Improved VS Code performance"
    echo "- Faster GitHub Actions operations"
    echo ""
    warning "If you experience any issues, you can restore from backup:"
    echo "  sudo rm /home/merk/.vscode-server /home/merk/actions-runner"
    echo "  sudo mv $BACKUP_DIR/.vscode-server /home/merk/"
    echo "  sudo mv $BACKUP_DIR/actions-runner /home/merk/"
    echo "  sudo chown -R merk:merk /home/merk/.vscode-server /home/merk/actions-runner"
}

# Run main function
main "$@"