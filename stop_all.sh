#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC}  $1"; }
info() { echo -e "  ${CYAN}→${NC}  $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC}  $1"; }

# Helper: get PID on a port (Mac and Linux compatible)
get_port_pid() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        lsof -ti tcp:$1 2>/dev/null
    else
        fuser $1/tcp 2>/dev/null
    fi
}

echo ""
echo -e "${BOLD}╔══════════════════════════════════════╗${NC}"
echo -e "${BOLD}║      Stopping Debug Assistant        ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════╝${NC}"
echo ""

# Stop API servers on ports 8001 and 8002
for port in 8001 8002; do
    pid=$(get_port_pid $port)
    if [[ -n "$pid" ]]; then
        info "Stopping process on port $port (PID $pid)..."
        kill -9 $pid 2>/dev/null
        ok "Port $port stopped."
    else
        warn "Nothing running on port $port."
    fi
done

# Stop React UI on port 3000
pid=$(get_port_pid 3000)
if [[ -n "$pid" ]]; then
    info "Stopping React UI on port 3000 (PID $pid)..."
    kill -9 $pid 2>/dev/null
    ok "React UI stopped."
else
    warn "Nothing running on port 3000."
fi

# Stop Postgres Docker container
if docker ps | grep -q rag-demo-postgres; then
    info "Stopping Postgres container..."
    docker stop rag-demo-postgres > /dev/null 2>&1
    ok "Postgres stopped."
else
    warn "Postgres container not running."
fi

echo ""
echo -e "${BOLD}╔══════════════════════════════════════╗${NC}"
echo -e "${BOLD}║        All services stopped.         ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════╝${NC}"
echo ""
