#!/bin/bash

################################################################################
# Copilot CLI Web UI - Automated Setup Script
# 
# This script automates the setup process for local development:
# - Checks for required software (Python 3.13+, Node.js 18+)
# - Creates Python virtual environment
# - Installs Python and Node.js dependencies
# - Generates .env files with guidance
# - Provides setup completion summary
#
# Usage: ./setup.sh [--help]
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_MIN_VERSION=3.13
NODE_MIN_VERSION=18
VENV_DIR="backend/venv"
VENV_NAME="venv"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

show_help() {
    cat << EOF
Copilot CLI Web UI - Setup Script

Usage: ./setup.sh [OPTIONS]

Options:
  --help, -h          Show this help message
  --skip-deps         Skip dependency checks
  --dev               Setup for development (with hot-reload)
  --prod              Setup for production

Examples:
  ./setup.sh                    # Full setup with all checks
  ./setup.sh --skip-deps       # Skip version checks
  ./setup.sh --dev             # Setup for development

EOF
    exit 0
}

################################################################################
# Dependency Checks
################################################################################

check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

check_python_version() {
    if ! check_command python3.13 && ! check_command python3; then
        print_error "Python 3.13+ not found"
        print_info "Please install Python 3.13 from https://www.python.org/downloads/"
        exit 1
    fi

    local python_cmd="python3.13"
    if ! check_command python3.13; then
        python_cmd="python3"
    fi

    local version=$($python_cmd --version 2>&1 | awk '{print $2}')
    local major=$(echo $version | cut -d. -f1)
    local minor=$(echo $version | cut -d. -f2)

    if [[ $major -lt 3 ]] || ([[ $major -eq 3 ]] && [[ $minor -lt 13 ]]); then
        print_error "Python $version found, but 3.13+ required"
        print_info "Please upgrade Python: https://www.python.org/downloads/"
        exit 1
    fi

    echo "$python_cmd"
}

check_node_version() {
    if ! check_command node; then
        print_error "Node.js not found"
        print_info "Please install Node.js 18+ from https://nodejs.org/"
        exit 1
    fi

    local version=$(node --version | cut -d'v' -f2)
    local major=$(echo $version | cut -d. -f1)

    if [[ $major -lt 18 ]]; then
        print_error "Node.js $version found, but 18+ required"
        print_info "Please upgrade Node.js: https://nodejs.org/"
        exit 1
    fi

    print_success "Node.js $version found"
}

check_git() {
    if ! check_command git; then
        print_error "Git not found"
        print_info "Please install Git from https://git-scm.com/"
        exit 1
    fi
    print_success "Git installed"
}

################################################################################
# Python Setup
################################################################################

setup_python_backend() {
    print_header "Setting up Python Backend"

    local python_cmd=$(check_python_version)
    print_success "Python $($python_cmd --version 2>&1 | awk '{print $2}') found"

    # Create virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        print_info "Creating virtual environment in $VENV_DIR..."
        $python_cmd -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi

    # Activate virtual environment
    print_info "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"

    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel > /dev/null 2>&1

    # Install dependencies
    if [ -f "backend/requirements.txt" ]; then
        print_info "Installing Python dependencies from requirements.txt..."
        pip install -r backend/requirements.txt
        print_success "Python dependencies installed"
    else
        print_error "requirements.txt not found in backend/"
        exit 1
    fi
}

################################################################################
# Node.js Setup
################################################################################

setup_node_frontend() {
    print_header "Setting up Node.js Frontend"

    check_node_version

    if [ ! -d "frontend/node_modules" ]; then
        print_info "Installing Node.js dependencies..."
        cd frontend
        npm install
        cd ..
        print_success "Node.js dependencies installed"
    else
        print_warning "node_modules already exists, skipping npm install"
        print_info "Run 'npm install' in frontend/ to update dependencies"
    fi
}

################################################################################
# Environment Configuration
################################################################################

setup_environment() {
    print_header "Environment Configuration"

    # Backend environment
    if [ ! -f "backend/.env.local" ]; then
        print_info "Creating backend/.env.local..."
        cp -v backend/.env.example backend/.env.local
        print_success "backend/.env.local created from template"
    else
        print_warning "backend/.env.local already exists"
    fi

    # Frontend environment
    if [ ! -f "frontend/.env.local" ]; then
        print_info "Creating frontend/.env.local..."
        cp -v frontend/.env.example frontend/.env.local
        print_success "frontend/.env.local created from template"
    else
        print_warning "frontend/.env.local already exists"
    fi

    print_warning "⚠️  Important: Edit .env.local files and add your GitHub token:"
    echo ""
    echo "1. Get your GitHub Personal Access Token (PAT):"
    echo "   → https://github.com/settings/tokens"
    echo "   → Generate new token (classic)"
    echo "   → Grant scopes: 'repo', 'user'"
    echo ""
    echo "2. Add to backend/.env.local:"
    echo "   → GITHUB_TOKEN=your_token_here"
    echo ""
    read -p "Press Enter once you've added your GitHub token..."
}

################################################################################
# Verification
################################################################################

verify_setup() {
    print_header "Verifying Setup"

    # Check Python setup
    source "$VENV_DIR/bin/activate"
    python_packages=$(pip list | wc -l)
    print_success "Python environment: $python_packages packages installed"

    # Check Node setup
    if [ -d "frontend/node_modules" ]; then
        node_modules=$(find frontend/node_modules -maxdepth 1 -type d | wc -l)
        print_success "Node.js environment: ~$node_modules packages installed"
    fi

    # Check .env files
    if [ -f "backend/.env.local" ]; then
        print_success "backend/.env.local configured"
    fi

    if [ -f "frontend/.env.local" ]; then
        print_success "frontend/.env.local configured"
    fi
}

################################################################################
# Cleanup on Error
################################################################################

cleanup() {
    if [ $? -ne 0 ]; then
        print_error "Setup failed! Check the errors above."
        exit 1
    fi
}

trap cleanup EXIT

################################################################################
# Main Setup Flow
################################################################################

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                ;;
            --skip-deps)
                SKIP_DEPS=true
                shift
                ;;
            --dev)
                MODE="development"
                shift
                ;;
            --prod)
                MODE="production"
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                ;;
        esac
    done

    # Show welcome
    print_header "Copilot CLI Web UI - Setup"
    print_info "Setting up your development environment..."
    echo ""

    # Check dependencies
    if [ "$SKIP_DEPS" != true ]; then
        print_header "Checking Dependencies"
        check_git
        check_python_version > /dev/null
        check_node_version
    fi

    # Run setup steps
    setup_python_backend
    setup_node_frontend
    setup_environment
    verify_setup

    # Show completion message
    print_header "✓ Setup Complete!"
    echo ""
    print_success "Your environment is ready!"
    echo ""
    echo "Next steps:"
    echo ""
    echo "  1. Activate Python virtual environment:"
    echo "     source backend/venv/bin/activate"
    echo ""
    echo "  2. Start the backend server:"
    echo "     cd backend && python -m uvicorn src.main:app --reload --port 8001"
    echo ""
    echo "  3. In a new terminal, start the frontend:"
    echo "     cd frontend && npm run dev"
    echo ""
    echo "  4. Open your browser:"
    echo "     http://localhost:3000"
    echo ""
    echo "Or use Make commands:"
    echo "  make run           # Run both services"
    echo "  make backend       # Run backend only"
    echo "  make frontend      # Run frontend only"
    echo ""
    echo "For more help, see: SETUP.md"
    echo ""
}

# Run main
main "$@"
