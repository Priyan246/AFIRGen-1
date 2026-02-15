#!/bin/bash
# Certificate Generation Script for AFIRGen
# Supports both self-signed certificates (development) and Let's Encrypt (production)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SSL_DIR="$PROJECT_ROOT/nginx/ssl"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "AFIRGen TLS Certificate Generator"
echo "=========================================="
echo ""

# Create SSL directory if it doesn't exist
mkdir -p "$SSL_DIR"

# Function to generate self-signed certificate
generate_self_signed() {
    echo -e "${YELLOW}Generating self-signed certificate...${NC}"
    
    # Prompt for certificate details
    read -p "Enter domain name (default: localhost): " DOMAIN
    DOMAIN=${DOMAIN:-localhost}
    
    read -p "Enter country code (default: US): " COUNTRY
    COUNTRY=${COUNTRY:-US}
    
    read -p "Enter state (default: State): " STATE
    STATE=${STATE:-State}
    
    read -p "Enter city (default: City): " CITY
    CITY=${CITY:-City}
    
    read -p "Enter organization (default: AFIRGen): " ORG
    ORG=${ORG:-AFIRGen}
    
    read -p "Enter validity days (default: 365): " DAYS
    DAYS=${DAYS:-365}
    
    # Generate certificate
    openssl req -x509 -nodes -days "$DAYS" -newkey rsa:2048 \
        -keyout "$SSL_DIR/key.pem" \
        -out "$SSL_DIR/cert.pem" \
        -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/CN=$DOMAIN"
    
    # Set proper permissions
    chmod 600 "$SSL_DIR/key.pem"
    chmod 644 "$SSL_DIR/cert.pem"
    
    echo -e "${GREEN}✓ Self-signed certificate generated successfully!${NC}"
    echo ""
    echo "Certificate location: $SSL_DIR/cert.pem"
    echo "Private key location: $SSL_DIR/key.pem"
    echo ""
    echo -e "${YELLOW}WARNING: Self-signed certificates are for development only!${NC}"
    echo "Browsers will show security warnings. For production, use Let's Encrypt."
}

# Function to setup Let's Encrypt
setup_letsencrypt() {
    echo -e "${YELLOW}Setting up Let's Encrypt certificate...${NC}"
    echo ""
    
    # Check if certbot is installed
    if ! command -v certbot &> /dev/null; then
        echo -e "${RED}Error: certbot is not installed${NC}"
        echo "Install certbot first:"
        echo "  Ubuntu/Debian: sudo apt-get install certbot"
        echo "  CentOS/RHEL: sudo yum install certbot"
        echo "  macOS: brew install certbot"
        exit 1
    fi
    
    read -p "Enter your domain name: " DOMAIN
    if [ -z "$DOMAIN" ]; then
        echo -e "${RED}Error: Domain name is required${NC}"
        exit 1
    fi
    
    read -p "Enter your email address: " EMAIL
    if [ -z "$EMAIL" ]; then
        echo -e "${RED}Error: Email address is required${NC}"
        exit 1
    fi
    
    echo ""
    echo "This will:"
    echo "1. Request a certificate from Let's Encrypt"
    echo "2. Verify domain ownership (requires port 80 to be accessible)"
    echo "3. Install the certificate"
    echo ""
    read -p "Continue? (y/n): " CONFIRM
    
    if [ "$CONFIRM" != "y" ]; then
        echo "Aborted."
        exit 0
    fi
    
    # Request certificate using standalone mode
    # Note: This requires port 80 to be available
    sudo certbot certonly --standalone \
        -d "$DOMAIN" \
        --email "$EMAIL" \
        --agree-tos \
        --non-interactive
    
    # Copy certificates to SSL directory
    sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SSL_DIR/cert.pem"
    sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SSL_DIR/key.pem"
    
    # Set proper permissions
    sudo chown $(whoami):$(whoami) "$SSL_DIR/cert.pem" "$SSL_DIR/key.pem"
    chmod 600 "$SSL_DIR/key.pem"
    chmod 644 "$SSL_DIR/cert.pem"
    
    echo -e "${GREEN}✓ Let's Encrypt certificate installed successfully!${NC}"
    echo ""
    echo "Certificate location: $SSL_DIR/cert.pem"
    echo "Private key location: $SSL_DIR/key.pem"
    echo ""
    echo -e "${YELLOW}Note: Let's Encrypt certificates expire in 90 days.${NC}"
    echo "Set up automatic renewal with: sudo certbot renew --dry-run"
}

# Function to use existing certificates
use_existing() {
    echo -e "${YELLOW}Using existing certificates...${NC}"
    echo ""
    
    read -p "Enter path to certificate file: " CERT_PATH
    if [ ! -f "$CERT_PATH" ]; then
        echo -e "${RED}Error: Certificate file not found${NC}"
        exit 1
    fi
    
    read -p "Enter path to private key file: " KEY_PATH
    if [ ! -f "$KEY_PATH" ]; then
        echo -e "${RED}Error: Private key file not found${NC}"
        exit 1
    fi
    
    # Copy certificates
    cp "$CERT_PATH" "$SSL_DIR/cert.pem"
    cp "$KEY_PATH" "$SSL_DIR/key.pem"
    
    # Set proper permissions
    chmod 600 "$SSL_DIR/key.pem"
    chmod 644 "$SSL_DIR/cert.pem"
    
    echo -e "${GREEN}✓ Certificates copied successfully!${NC}"
    echo ""
    echo "Certificate location: $SSL_DIR/cert.pem"
    echo "Private key location: $SSL_DIR/key.pem"
}

# Main menu
echo "Select certificate type:"
echo "1) Self-signed certificate (development)"
echo "2) Let's Encrypt certificate (production)"
echo "3) Use existing certificates"
echo ""
read -p "Enter choice (1-3): " CHOICE

case $CHOICE in
    1)
        generate_self_signed
        ;;
    2)
        setup_letsencrypt
        ;;
    3)
        use_existing
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Certificate setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Update docker-compose.yaml to use the nginx reverse proxy"
echo "2. Update frontend config.js to use HTTPS URLs"
echo "3. Start the services: docker-compose up -d"
echo ""
