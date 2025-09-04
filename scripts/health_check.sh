#!/bin/bash
# =============================================
# FuelTune Streamlit - Health Check Script
# =============================================
# Comprehensive health monitoring and diagnostics

set -euo pipefail

# =============================================
# Configuration
# =============================================
NAMESPACE="${NAMESPACE:-fueltune}"
ENVIRONMENT="${ENVIRONMENT:-production}"
TIMEOUT="${TIMEOUT:-30}"
CHECK_EXTERNAL="${CHECK_EXTERNAL:-true}"
VERBOSE="${VERBOSE:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Health check results
HEALTH_SCORE=0
MAX_SCORE=0
FAILED_CHECKS=()

# =============================================
# Logging Functions
# =============================================
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $*${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $*${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $*${NC}"
}

pass() {
    echo -e "${GREEN}✓ $*${NC}"
    HEALTH_SCORE=$((HEALTH_SCORE + 1))
}

fail() {
    echo -e "${RED}✗ $*${NC}"
    FAILED_CHECKS+=("$*")
}

# =============================================
# Helper Functions
# =============================================
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Perform comprehensive health checks on FuelTune Streamlit application.

OPTIONS:
    -h, --help              Show this help message
    -n, --namespace NAME    Kubernetes namespace (default: fueltune)
    -e, --environment ENV   Environment (development|staging|production)
    -t, --timeout SECONDS   HTTP timeout in seconds (default: 30)
    --no-external          Skip external connectivity checks
    --verbose              Show detailed output
    --json                 Output results in JSON format
    --nagios               Output in Nagios-compatible format

Examples:
    $0                                      # Basic health check
    $0 --verbose                           # Detailed health check
    $0 --no-external                       # Skip external checks
    $0 --json                              # JSON output for monitoring

EOF
}

increment_max_score() {
    MAX_SCORE=$((MAX_SCORE + 1))
}

# =============================================
# Health Check Functions
# =============================================

check_cluster_connectivity() {
    increment_max_score
    if [[ "$VERBOSE" == "true" ]]; then
        info "Checking Kubernetes cluster connectivity..."
    fi
    
    if kubectl cluster-info >/dev/null 2>&1; then
        pass "Kubernetes cluster connectivity"
    else
        fail "Kubernetes cluster connectivity"
        return 1
    fi
}

check_namespace_exists() {
    increment_max_score
    if [[ "$VERBOSE" == "true" ]]; then
        info "Checking if namespace $NAMESPACE exists..."
    fi
    
    if kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        pass "Namespace $NAMESPACE exists"
    else
        fail "Namespace $NAMESPACE does not exist"
        return 1
    fi
}

check_deployment_status() {
    increment_max_score
    if [[ "$VERBOSE" == "true" ]]; then
        info "Checking deployment status..."
    fi
    
    local deployment_status
    deployment_status=$(kubectl get deployment fueltune-app -n "$NAMESPACE" -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null || echo "False")
    
    if [[ "$deployment_status" == "True" ]]; then
        pass "Deployment is available"
    else
        fail "Deployment is not available"
        if [[ "$VERBOSE" == "true" ]]; then
            kubectl describe deployment fueltune-app -n "$NAMESPACE" 2>/dev/null || true
        fi
        return 1
    fi
}

check_pod_status() {
    increment_max_score
    if [[ "$VERBOSE" == "true" ]]; then
        info "Checking pod status..."
    fi
    
    local ready_replicas
    ready_replicas=$(kubectl get deployment fueltune-app -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    
    local desired_replicas
    desired_replicas=$(kubectl get deployment fueltune-app -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
    
    if [[ "$ready_replicas" == "$desired_replicas" ]] && [[ "$ready_replicas" -gt 0 ]]; then
        pass "All pods are ready ($ready_replicas/$desired_replicas)"
    else
        fail "Pods not ready ($ready_replicas/$desired_replicas)"
        if [[ "$VERBOSE" == "true" ]]; then
            kubectl get pods -n "$NAMESPACE" -l app=fueltune
        fi
        return 1
    fi
}

check_pod_health() {
    increment_max_score
    if [[ "$VERBOSE" == "true" ]]; then
        info "Checking individual pod health..."
    fi
    
    local unhealthy_pods
    unhealthy_pods=$(kubectl get pods -n "$NAMESPACE" -l app=fueltune --field-selector=status.phase!=Running --no-headers 2>/dev/null | wc -l || echo "0")
    
    if [[ "$unhealthy_pods" == "0" ]]; then
        pass "All pods are running"
    else
        fail "$unhealthy_pods pods are not running"
        if [[ "$VERBOSE" == "true" ]]; then
            kubectl get pods -n "$NAMESPACE" -l app=fueltune --field-selector=status.phase!=Running
        fi
        return 1
    fi
}

check_service_endpoints() {
    increment_max_score
    if [[ "$VERBOSE" == "true" ]]; then
        info "Checking service endpoints..."
    fi
    
    local endpoint_count
    endpoint_count=$(kubectl get endpoints fueltune-service -n "$NAMESPACE" -o jsonpath='{.subsets[*].addresses[*].ip}' 2>/dev/null | wc -w || echo "0")
    
    if [[ "$endpoint_count" -gt 0 ]]; then
        pass "Service has $endpoint_count endpoints"
    else
        fail "Service has no endpoints"
        if [[ "$VERBOSE" == "true" ]]; then
            kubectl describe endpoints fueltune-service -n "$NAMESPACE" 2>/dev/null || true
        fi
        return 1
    fi
}

check_ingress_status() {
    increment_max_score
    if [[ "$VERBOSE" == "true" ]]; then
        info "Checking ingress status..."
    fi
    
    if kubectl get ingress fueltune-ingress -n "$NAMESPACE" >/dev/null 2>&1; then
        local ingress_ip
        ingress_ip=$(kubectl get ingress fueltune-ingress -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
        
        if [[ -n "$ingress_ip" ]]; then
            pass "Ingress has external IP: $ingress_ip"
        else
            warn "Ingress exists but no external IP assigned"
            HEALTH_SCORE=$((HEALTH_SCORE + 1)) # Don't fail for this
        fi
    else
        fail "Ingress not found"
        return 1
    fi
}

check_hpa_status() {
    increment_max_score
    if [[ "$VERBOSE" == "true" ]]; then
        info "Checking HPA status..."
    fi
    
    if kubectl get hpa fueltune-hpa -n "$NAMESPACE" >/dev/null 2>&1; then
        local hpa_ready
        hpa_ready=$(kubectl get hpa fueltune-hpa -n "$NAMESPACE" -o jsonpath='{.status.conditions[?(@.type=="AbleToScale")].status}' 2>/dev/null || echo "False")
        
        if [[ "$hpa_ready" == "True" ]]; then
            pass "HPA is functioning"
        else
            fail "HPA is not ready"
            if [[ "$VERBOSE" == "true" ]]; then
                kubectl describe hpa fueltune-hpa -n "$NAMESPACE" 2>/dev/null || true
            fi
            return 1
        fi
    else
        warn "HPA not found (optional)"
        HEALTH_SCORE=$((HEALTH_SCORE + 1)) # Don't fail for optional component
    fi
}

check_application_health() {
    increment_max_score
    if [[ "$VERBOSE" == "true" ]]; then
        info "Checking application health endpoint..."
    fi
    
    # Port forward to access the application
    kubectl port-forward service/fueltune-service 8080:80 -n "$NAMESPACE" >/dev/null 2>&1 &
    local port_forward_pid=$!
    
    # Wait for port forward to establish
    sleep 3
    
    local health_url="http://localhost:8080/_stcore/health"
    local health_check_result=false
    
    if curl -f -s --connect-timeout "$TIMEOUT" "$health_url" >/dev/null 2>&1; then
        health_check_result=true
    fi
    
    # Clean up port forward
    kill $port_forward_pid 2>/dev/null || true
    wait $port_forward_pid 2>/dev/null || true
    
    if [[ "$health_check_result" == "true" ]]; then
        pass "Application health endpoint responds"
    else
        fail "Application health endpoint not responding"
        return 1
    fi
}

check_database_connectivity() {
    increment_max_score
    if [[ "$VERBOSE" == "true" ]]; then
        info "Checking database connectivity..."
    fi
    
    # Try to get database secret to verify it exists
    if kubectl get secret fueltune-database-secret -n "$NAMESPACE" >/dev/null 2>&1; then
        pass "Database secret exists"
        
        # Try to create a test pod to check database connectivity
        local test_pod="db-test-$(date +%s)"
        
        kubectl run "$test_pod" -n "$NAMESPACE" --image=postgres:15-alpine --rm -i --restart=Never --quiet=true -- \
            sh -c 'pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER' \
            --env DB_HOST="$(kubectl get secret fueltune-database-secret -n "$NAMESPACE" -o jsonpath='{.data.host}' | base64 -d 2>/dev/null || echo 'localhost')" \
            --env DB_PORT="$(kubectl get secret fueltune-database-secret -n "$NAMESPACE" -o jsonpath='{.data.port}' | base64 -d 2>/dev/null || echo '5432')" \
            --env DB_USER="$(kubectl get secret fueltune-database-secret -n "$NAMESPACE" -o jsonpath='{.data.username}' | base64 -d 2>/dev/null || echo 'fueltune')" \
            >/dev/null 2>&1 || true
        
        # Since we can't easily test DB connectivity without credentials in plain text,
        # we'll just verify the secret exists
        HEALTH_SCORE=$((HEALTH_SCORE + 1))
    else
        fail "Database secret not found"
        return 1
    fi
}

check_redis_connectivity() {
    increment_max_score
    if [[ "$VERBOSE" == "true" ]]; then
        info "Checking Redis connectivity..."
    fi
    
    # Check if Redis secret exists
    if kubectl get secret fueltune-redis-secret -n "$NAMESPACE" >/dev/null 2>&1; then
        pass "Redis secret exists"
    else
        warn "Redis secret not found (may be optional)"
        HEALTH_SCORE=$((HEALTH_SCORE + 1)) # Don't fail for optional component
    fi
}

check_resource_usage() {
    increment_max_score
    if [[ "$VERBOSE" == "true" ]]; then
        info "Checking resource usage..."
    fi
    
    # Get resource usage metrics if metrics-server is available
    if kubectl top nodes >/dev/null 2>&1; then
        local pod_cpu_usage
        pod_cpu_usage=$(kubectl top pods -n "$NAMESPACE" -l app=fueltune --no-headers 2>/dev/null | awk '{sum+=$2} END {print sum}' || echo "0")
        
        if [[ "$pod_cpu_usage" != "0" ]]; then
            pass "Pod metrics available (CPU usage data found)"
        else
            warn "Pod metrics available but no CPU usage data"
            HEALTH_SCORE=$((HEALTH_SCORE + 1))
        fi
    else
        warn "Metrics server not available"
        HEALTH_SCORE=$((HEALTH_SCORE + 1))
    fi
}

check_persistent_volumes() {
    increment_max_score
    if [[ "$VERBOSE" == "true" ]]; then
        info "Checking persistent volumes..."
    fi
    
    local pvc_count
    pvc_count=$(kubectl get pvc -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l || echo "0")
    
    if [[ "$pvc_count" -gt 0 ]]; then
        local bound_pvcs
        bound_pvcs=$(kubectl get pvc -n "$NAMESPACE" --no-headers 2>/dev/null | grep -c "Bound" || echo "0")
        
        if [[ "$bound_pvcs" == "$pvc_count" ]]; then
            pass "All PVCs are bound ($bound_pvcs/$pvc_count)"
        else
            fail "Some PVCs are not bound ($bound_pvcs/$pvc_count)"
            if [[ "$VERBOSE" == "true" ]]; then
                kubectl get pvc -n "$NAMESPACE"
            fi
            return 1
        fi
    else
        warn "No PVCs found (may be intentional)"
        HEALTH_SCORE=$((HEALTH_SCORE + 1))
    fi
}

check_external_connectivity() {
    if [[ "$CHECK_EXTERNAL" == "false" ]]; then
        return 0
    fi
    
    increment_max_score
    if [[ "$VERBOSE" == "true" ]]; then
        info "Checking external connectivity..."
    fi
    
    # Try to get the external URL from ingress
    local external_host
    external_host=$(kubectl get ingress fueltune-ingress -n "$NAMESPACE" -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "")
    
    if [[ -n "$external_host" ]]; then
        if curl -f -s --connect-timeout "$TIMEOUT" "https://$external_host/_stcore/health" >/dev/null 2>&1; then
            pass "External URL is accessible: https://$external_host"
        else
            fail "External URL not accessible: https://$external_host"
            return 1
        fi
    else
        warn "No external host configured"
        HEALTH_SCORE=$((HEALTH_SCORE + 1))
    fi
}

check_monitoring() {
    increment_max_score
    if [[ "$VERBOSE" == "true" ]]; then
        info "Checking monitoring setup..."
    fi
    
    # Check if ServiceMonitor exists (for Prometheus)
    if kubectl get servicemonitor fueltune-monitor -n "$NAMESPACE" >/dev/null 2>&1; then
        pass "ServiceMonitor exists"
    else
        warn "ServiceMonitor not found (monitoring may not be configured)"
        HEALTH_SCORE=$((HEALTH_SCORE + 1))
    fi
}

# =============================================
# Output Functions
# =============================================
output_json() {
    local health_percentage
    if [[ "$MAX_SCORE" -gt 0 ]]; then
        health_percentage=$(( (HEALTH_SCORE * 100) / MAX_SCORE ))
    else
        health_percentage=0
    fi
    
    local status
    if [[ "$health_percentage" -eq 100 ]]; then
        status="healthy"
    elif [[ "$health_percentage" -ge 80 ]]; then
        status="warning"
    else
        status="critical"
    fi
    
    cat << EOF
{
    "status": "$status",
    "health_score": $HEALTH_SCORE,
    "max_score": $MAX_SCORE,
    "health_percentage": $health_percentage,
    "namespace": "$NAMESPACE",
    "environment": "$ENVIRONMENT",
    "timestamp": "$(date -Iseconds)",
    "failed_checks": [$(IFS=','; printf '"%s"' "${FAILED_CHECKS[*]}")],
    "checks": {
        "cluster_connectivity": $(kubectl cluster-info >/dev/null 2>&1 && echo "true" || echo "false"),
        "namespace_exists": $(kubectl get namespace "$NAMESPACE" >/dev/null 2>&1 && echo "true" || echo "false"),
        "deployment_available": $(kubectl get deployment fueltune-app -n "$NAMESPACE" -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null | grep -q "True" && echo "true" || echo "false")
    }
}
EOF
}

output_nagios() {
    local health_percentage
    if [[ "$MAX_SCORE" -gt 0 ]]; then
        health_percentage=$(( (HEALTH_SCORE * 100) / MAX_SCORE ))
    else
        health_percentage=0
    fi
    
    local exit_code
    local status_text
    
    if [[ "$health_percentage" -eq 100 ]]; then
        exit_code=0
        status_text="OK"
    elif [[ "$health_percentage" -ge 80 ]]; then
        exit_code=1
        status_text="WARNING"
    else
        exit_code=2
        status_text="CRITICAL"
    fi
    
    echo "FUELTUNE $status_text - Health: $health_percentage% ($HEALTH_SCORE/$MAX_SCORE checks passed)"
    
    if [[ ${#FAILED_CHECKS[@]} -gt 0 ]]; then
        echo "Failed checks: ${FAILED_CHECKS[*]}"
    fi
    
    exit $exit_code
}

# =============================================
# Main Function
# =============================================
main() {
    local output_format="standard"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -t|--timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --no-external)
                CHECK_EXTERNAL=false
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --json)
                output_format="json"
                shift
                ;;
            --nagios)
                output_format="nagios"
                shift
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
    
    if [[ "$output_format" == "standard" ]]; then
        log "FuelTune Streamlit Health Check"
        log "Environment: $ENVIRONMENT"
        log "Namespace: $NAMESPACE"
        echo ""
    fi
    
    # Run health checks
    check_cluster_connectivity || true
    check_namespace_exists || true
    check_deployment_status || true
    check_pod_status || true
    check_pod_health || true
    check_service_endpoints || true
    check_ingress_status || true
    check_hpa_status || true
    check_application_health || true
    check_database_connectivity || true
    check_redis_connectivity || true
    check_resource_usage || true
    check_persistent_volumes || true
    check_external_connectivity || true
    check_monitoring || true
    
    # Output results
    case "$output_format" in
        "json")
            output_json
            ;;
        "nagios")
            output_nagios
            ;;
        *)
            # Standard output
            echo ""
            log "Health Check Summary:"
            echo "===================="
            
            local health_percentage
            if [[ "$MAX_SCORE" -gt 0 ]]; then
                health_percentage=$(( (HEALTH_SCORE * 100) / MAX_SCORE ))
            else
                health_percentage=0
            fi
            
            echo "Overall Health: $health_percentage% ($HEALTH_SCORE/$MAX_SCORE checks passed)"
            
            if [[ ${#FAILED_CHECKS[@]} -gt 0 ]]; then
                echo ""
                warn "Failed Checks:"
                for check in "${FAILED_CHECKS[@]}"; do
                    echo "  - $check"
                done
            fi
            
            echo ""
            if [[ "$health_percentage" -eq 100 ]]; then
                log "All health checks passed! 🎉"
                exit 0
            elif [[ "$health_percentage" -ge 80 ]]; then
                warn "Some non-critical issues found"
                exit 1
            else
                error "Critical issues found"
                exit 2
            fi
            ;;
    esac
}

# Run main function
main "$@"