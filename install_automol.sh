#!/bin/bash
# AutoMol Independent Installation Script for Unix/Linux/macOS
# This script installs AutoMol as a standalone package using uv

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Default values
ENV_NAME="${1:-automol_env}"
PYTHON_VER="${2:-3.12}"

log "Starting AutoMol independent installation..."
echo "================================================"

# Check if Python is installed
if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
    error "Python is required but not installed. Please install Python 3.8+ first."
    error "Visit: https://www.python.org/downloads/"
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python3 --version 2>/dev/null || python --version 2>/dev/null || echo "Unknown")
info "Found Python version: $PYTHON_VERSION"

# Check if uv is installed
if ! command -v uv >/dev/null 2>&1; then
    warn "uv package manager not found. Installing uv..."
    
    # Install uv
    if command -v pip3 >/dev/null 2>&1; then
        pip3 install uv
    elif command -v pip >/dev/null 2>&1; then
        pip install uv
    else
        error "pip not found. Please install pip first."
        exit 1
    fi
    
    # Verify installation
    if ! command -v uv >/dev/null 2>&1; then
        error "Failed to install uv. Please install manually:"
        error "Visit: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
else
    log "Found uv package manager"
fi

# Create virtual environment
log "Creating virtual environment '$ENV_NAME' with Python $PYTHON_VER..."
uv venv "$ENV_NAME" --python "$PYTHON_VER"

# Activate virtual environment
log "Activating virtual environment..."
source "$ENV_NAME/bin/activate"

# Check for wkhtmltopdf (recommended for PDF generation)
if ! command -v wkhtmltopdf >/dev/null 2>&1; then
    warn "wkhtmltopdf not found. PDF generation may not work."
    warn "Install with:"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        warn "  sudo apt-get install wkhtmltopdf"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        warn "  brew install wkhtmltopdf"
    else
        warn "  Visit: https://wkhtmltopdf.org/downloads.html"
    fi
fi


# Install additional recommended packages
log "Installing additional dependencies..."
uv pip install -r requirements.txt
uv pip install PyTDC
uv pip install rdkit==2024.3.5

# Verify installation
log "Verifying AutoMol installation..."
python3 -c "
import sys
try:
    from automol.feature_generators import BottleneckTransformer
    print('✓ AutoMol core package imported successfully')
    
    # Test encoder creation
    encoder = BottleneckTransformer(model='CHEMBL', use_gpu=False, batch_size=5)
    print('✓ BottleneckTransformer created successfully')
    print('✓ AutoMol installation verified!')
    
except ImportError as e:
    print('✗ AutoMol import failed:', e)
    sys.exit(1)
except Exception as e:
    print('✗ AutoMol verification failed:', e)
    sys.exit(1)
"

# Create activation script
log "Creating activation script..."
cat > activate_automol.sh << EOF
#!/bin/bash
# AutoMol Environment Activation Script
echo "Activating AutoMol environment..."
source $ENV_NAME/bin/activate
echo "AutoMol environment activated!"
echo "Python: \$(python --version)"
echo "Location: \$(which python)"
EOF
chmod +x activate_automol.sh

# Success message
echo
log "AutoMol installation completed successfully!"
echo
info "Environment name: $ENV_NAME"
info "Python version: $PYTHON_VER"
echo
info "To use AutoMol:"
info "1. Activate environment: source $ENV_NAME/bin/activate"
info "2. Or use: ./activate_automol.sh"
info "3. Start Jupyter: jupyter lab"
info "4. Try tutorials in the Tutorials/ folder"
echo
info "For Streamlit app: streamlit run streamlit_app/main.py"
echo
log "AutoMol is ready to use!"
