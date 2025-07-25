#!/bin/bash

# SiamTech Multi-Tenant RAG System Setup Script
# Enhanced version with model routing and separate authentication

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_step() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

print_info() {
    echo -e "${YELLOW}[INFO] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

print_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# Main setup function
main() {
    print_header "🚀 SiamTech Multi-Tenant RAG System Setup"
    
    echo -e "${CYAN}Configuration:${NC}"
    echo "• Company A: Bangkok HQ (llama3.1:8b model)"
    echo "• Company B: Chiang Mai Regional (gemma2:9b model)" 
    echo "• Company C: International (phi3:14b model)"
    echo "• Ollama Server: 192.168.11.97:12434"
    echo "• Separate databases and authentication per company"
    echo ""
    
    # Check prerequisites
    print_step "Checking prerequisites..."
    check_prerequisites
    
    # Create necessary files
    print_step "Creating configuration files..."
    create_config_files
    
    # Setup database initialization scripts
    print_step "Preparing database initialization..."
    check_database_scripts
    
    # Start the system
    print_step "Starting multi-tenant system..."
    start_system
    
    # Wait for services to be ready
    print_step "Waiting for services to start..."
    wait_for_services
    
    # Test the system
    print_step "Testing system endpoints..."
    test_system
    
    # Show final status
    show_system_status
}

check_prerequisites() {
    local missing_deps=()
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing_deps+=("docker-compose")
    fi
    
    # Check curl
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi
    
    # Check jq
    if ! command -v jq &> /dev/null; then
        missing_deps+=("jq (optional, for better JSON formatting)")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_info "Please install missing dependencies and run again"
        exit 1
    fi
    
    print_success "All prerequisites met"
}

create_config_files() {
    # Create tenant_config.yaml (already exists, just verify)
    if [ ! -f "tenant_config.yaml" ]; then
        print_info "Creating tenant_config.yaml..."
        # The file should already exist from artifacts
        print_error "tenant_config.yaml not found! Please ensure all artifacts are saved."
        exit 1
    fi
    
    # Create enhanced Dockerfile.rag
    print_info "Creating enhanced Dockerfile.rag..."
    cat > Dockerfile.rag << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy configuration files
COPY tenant_config.yaml .

# Copy application files
COPY ollama_postgres_agent.py .
COPY enhanced_multi_agent_service.py .

# Create logs directory
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check script
COPY <<'HEALTH_EOF' /app/healthcheck.py
#!/usr/bin/env python3
import requests
import sys
import os

try:
    response = requests.get(
        f"http://localhost:{os.getenv('PORT', '5000')}/health",
        timeout=10
    )
    if response.status_code == 200:
        print("Health check passed")
        sys.exit(0)
    else:
        print(f"Health check failed: HTTP {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"Health check failed: {e}")
    sys.exit(1)
HEALTH_EOF

RUN chmod +x /app/healthcheck.py

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python /app/healthcheck.py

# Create non-root user
RUN useradd --create-home --shell /bin/bash siamtech && \
    chown -R siamtech:siamtech /app

USER siamtech

# Run the enhanced multi-agent service
CMD ["python", "enhanced_multi_agent_service.py"]
EOF

    # Create enhanced requirements.txt
    print_info "Creating enhanced requirements.txt..."
    cat > requirements.txt << 'EOF'
# Core FastAPI and web framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0

# Database dependencies
psycopg2-binary==2.9.9
sqlalchemy==2.0.23

# HTTP client for Ollama
aiohttp==3.9.0
httpx==0.25.2
requests==2.31.0

# Configuration support
pyyaml==6.0.1
python-dotenv==1.0.0

# Utilities
python-dateutil==2.8.2
typing-extensions==4.8.0

# Development tools
pytest==7.4.3
pytest-asyncio==0.21.1
EOF

    print_success "Configuration files created"
}

check_database_scripts() {
    local db_scripts=("init-company-a.sql" "init-company-b.sql" "init-company-c.sql")
    
    for script in "${db_scripts[@]}"; do
        if [ ! -f "$script" ]; then
            print_error "Database script $script not found!"
            print_info "Please ensure all database initialization scripts are present"
            exit 1
        fi
    done
    
    print_success "Database scripts verified"
}

start_system() {
    print_info "Stopping any existing containers..."
    docker-compose down --remove-orphans 2>/dev/null || true
    
    print_info "Building and starting services..."
    docker-compose up -d --build
    
    if [ $? -eq 0 ]; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        exit 1
    fi
}

wait_for_services() {
    local services=(
        "localhost:5000|RAG Service"
        "localhost:5678|n8n Workflow"
        "localhost:3000|Company A WebUI"
        "localhost:3100|Company B WebUI"
        "localhost:3200|Company C WebUI"
        "localhost:9000|Admin Dashboard"
    )
    
    print_info "Waiting for services to be ready (this may take 2-3 minutes)..."
    
    for i in {1..60}; do
        local all_ready=true
        
        for service in "${services[@]}"; do
            local url=$(echo $service | cut -d'|' -f1)
            local name=$(echo $service | cut -d'|' -f2)
            
            if ! curl -s "http://$url" > /dev/null 2>&1; then
                all_ready=false
                break
            fi
        done
        
        if $all_ready; then
            print_success "All services are ready!"
            return 0
        fi
        
        echo -n "."
        sleep 3
    done
    
    print_error "Some services may not be ready yet. Continuing anyway..."
}

test_system() {
    print_info "Testing system endpoints..."
    
    # Test RAG Service health
    if curl -s http://localhost:5000/health | grep -q "healthy"; then
        print_success "✅ RAG Service is healthy"
    else
        print_error "❌ RAG Service health check failed"
    fi
    
    # Test tenant endpoints
    local tenants=("company-a" "company-b" "company-c")
    
    for tenant in "${tenants[@]}"; do
        print_info "Testing $tenant endpoints..."
        
        # Test tenant status
        if curl -s "http://localhost:5000/tenants/$tenant/status" | grep -q "$tenant"; then
            print_success "✅ $tenant status endpoint working"
        else
            print_error "❌ $tenant status endpoint failed"
        fi
        
        # Test simple query
        local test_query='{"query": "Hello", "tenant_id": "'$tenant'"}'
        if curl -s -X POST \
            -H "Content-Type: application/json" \
            -H "X-Tenant-ID: $tenant" \
            -d "$test_query" \
            http://localhost:5000/rag-query | grep -q "answer"; then
            print_success "✅ $tenant RAG query working"
        else
            print_error "❌ $tenant RAG query failed"
        fi
    done
    
    # Test Ollama connectivity
    print_info "Testing Ollama server connectivity..."
    if curl -s http://192.168.11.97:12434/api/tags > /dev/null; then
        print_success "✅ Ollama server (192.168.11.97:12434) is accessible"
    else
        print_error "❌ Ollama server connection failed"
        print_info "Please ensure Ollama server is running on 192.168.11.97:12434"
    fi
}

show_system_status() {
    print_header "🎉 SiamTech Multi-Tenant RAG System Ready!"
    
    echo ""
    echo -e "${CYAN}🌐 Access Points:${NC}"
    echo "  Admin Dashboard:    http://localhost:9000"
    echo "  RAG Service API:    http://localhost:5000"
    echo "  n8n Workflows:      http://localhost:5678 (admin/password)"
    echo ""
    echo -e "${CYAN}💼 Company Access:${NC}"
    echo "  🏢 Company A (Bangkok HQ):       http://localhost:3000"
    echo "     • Model: llama3.1:8b"
    echo "     • Database: siamtech_company_a"
    echo "     • Language: Thai"
    echo ""
    echo "  🏔️  Company B (Chiang Mai):      http://localhost:3100"
    echo "     • Model: gemma2:9b"
    echo "     • Database: siamtech_company_b" 
    echo "     • Language: Thai"
    echo ""
    echo "  🌍 Company C (International):    http://localhost:3200"
    echo "     • Model: phi3:14b"
    echo "     • Database: siamtech_company_c"
    echo "     • Language: English"
    echo ""
    echo -e "${CYAN}🔧 Technical Details:${NC}"
    echo "  Ollama Server:      192.168.11.97:12434"
    echo "  PostgreSQL Ports:   5432 (A), 5433 (B), 5434 (C)"
    echo "  Redis Cache:        localhost:6379"
    echo ""
    echo -e "${CYAN}📖 API Documentation:${NC}"
    echo "  Swagger UI:         http://localhost:5000/docs"
    echo "  ReDoc:              http://localhost:5000/redoc"
    echo ""
    echo -e "${CYAN}🧪 Quick Test Commands:${NC}"
    echo '  curl -X POST http://localhost:5000/rag-query \'
    echo '    -H "Content-Type: application/json" \'
    echo '    -H "X-Tenant-ID: company-a" \'
    echo '    -d '"'"'{"query": "มีพนักงานกี่คน"}'"'"
    echo ""
    echo '  curl -X POST http://localhost:5000/rag-query \'
    echo '    -H "Content-Type: application/json" \'
    echo '    -H "X-Tenant-ID: company-c" \'
    echo '    -d '"'"'{"query": "How many employees?"}'"'"
    echo ""
    
    # Show running containers
    echo -e "${CYAN}🐳 Running Containers:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep siamtech || echo "No SiamTech containers found"
    
    print_success "Setup completed successfully! 🎉"
    print_info "Check the admin dashboard at http://localhost:9000 for a complete overview"
}

# Handle script arguments
case "${1:-}" in
    "clean")
        print_header "🧹 Cleaning up system..."
        docker-compose down --remove-orphans --volumes
        docker system prune -f
        print_success "System cleaned up"
        ;;
    "restart")
        print_header "🔄 Restarting system..."
        docker-compose restart
        wait_for_services
        print_success "System restarted"
        ;;
    "logs")
        print_header "📋 Showing system logs..."
        docker-compose logs -f
        ;;
    "status")
        print_header "📊 System Status"
        show_system_status
        ;;
    *)
        main
        ;;
esac