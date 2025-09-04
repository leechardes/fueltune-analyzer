#!/bin/bash
# =============================================
# FuelTune Streamlit - Rollback Script
# =============================================
# Quick rollback to previous working version

set -euo pipefail

# =============================================
# Configuration
# =============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
NAMESPACE="${NAMESPACE:-fueltune}"
ENVIRONMENT="${ENVIRONMENT:-production}"
TIMEOUT="${TIMEOUT:-600}" # 10 minutes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $*${NC}"
}

# =============================================
# Helper Functions
# =============================================
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Rollback FuelTune Streamlit application to a previous version.

OPTIONS:
    -h, --help              Show this help message
    -n, --namespace NAME    Kubernetes namespace (default: fueltune)
    -e, --environment ENV   Environment (development|staging|production)
    -r, --revision NUM      Specific revision to rollback to (default: previous)
    -l, --list              List available revisions
    --timeout SECONDS       Rollback timeout in seconds (default: 600)
    --force                 Force rollback even if current deployment is healthy
    --dry-run              Show what would be rolled back

Examples:
    $0                                      # Rollback to previous version
    $0 -r 3                                # Rollback to specific revision
    $0 --list                              # List available revisions
    $0 --dry-run                           # Show rollback plan

EOF
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check required tools
    local required_tools=("kubectl" "helm")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            error "$tool is not installed or not in PATH"
        fi
    done
    
    # Check kubectl connectivity
    if ! kubectl cluster-info >/dev/null 2>&1; then
        error "Cannot connect to Kubernetes cluster"
    fi
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        error "Namespace $NAMESPACE does not exist"
    fi
    
    # Check if Helm release exists
    if ! helm status fueltune -n "$NAMESPACE" >/dev/null 2>&1; then
        error "Helm release 'fueltune' not found in namespace $NAMESPACE"
    fi
    
    log "Prerequisites check passed"
}

get_current_status() {
    local deployment_status
    deployment_status=$(kubectl get deployment fueltune-app -n "$NAMESPACE" -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null || echo "Unknown")
    
    local current_version
    current_version=$(kubectl get deployment fueltune-app -n "$NAMESPACE" -o jsonpath='{.metadata.labels.version}' 2>/dev/null || echo "unknown")
    
    local ready_replicas
    ready_replicas=$(kubectl get deployment fueltune-app -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    
    local desired_replicas
    desired_replicas=$(kubectl get deployment fueltune-app -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
    
    echo "Current deployment status:"
    echo "  Version: $current_version"
    echo "  Status: $deployment_status"
    echo "  Replicas: $ready_replicas/$desired_replicas"
    echo ""
}

list_revisions() {
    log "Available Helm revisions:"
    echo ""
    
    if ! helm history fueltune -n "$NAMESPACE" 2>/dev/null; then
        error "Failed to get Helm revision history"
    fi
    
    echo ""
    info "Use -r/--revision option to rollback to a specific revision"
}

check_health() {
    log "Checking application health..."
    
    # Check if deployment is available
    local deployment_available
    deployment_available=$(kubectl get deployment fueltune-app -n "$NAMESPACE" -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null || echo "False")
    
    if [[ "$deployment_available" != "True" ]]; then
        warn "Deployment is not currently available"
        return 1
    fi
    
    # Check pod health
    local unhealthy_pods
    unhealthy_pods=$(kubectl get pods -n "$NAMESPACE" -l app=fueltune --field-selector=status.phase!=Running --no-headers 2>/dev/null | wc -l || echo "0")
    
    if [[ "$unhealthy_pods" -gt 0 ]]; then
        warn "Found $unhealthy_pods unhealthy pods"
        kubectl get pods -n "$NAMESPACE" -l app=fueltune --field-selector=status.phase!=Running
        return 1
    fi
    
    # Try health endpoint check
    local health_check_passed=false
    
    # Port forward for health check (background process)
    kubectl port-forward service/fueltune-service 8080:80 -n "$NAMESPACE" >/dev/null 2>&1 &
    local port_forward_pid=$!
    
    # Wait for port forward
    sleep 3
    
    # Quick health check
    if curl -f "http://localhost:8080/_stcore/health" >/dev/null 2>&1; then
        health_check_passed=true
    fi
    
    # Clean up port forward
    kill $port_forward_pid 2>/dev/null || true
    
    if [[ "$health_check_passed" == "true" ]]; then
        log "Application appears healthy"
        return 0
    else
        warn "Health endpoint check failed"
        return 1
    fi
}

perform_rollback() {
    local target_revision="$1"
    local dry_run="$2"
    
    log "Initiating rollback..."
    
    if [[ "$dry_run" == "true" ]]; then
        log "DRY RUN: Would rollback to revision $target_revision"
        helm get values fueltune -n "$NAMESPACE" --revision "$target_revision" || warn "Could not get values for revision $target_revision"
        return 0
    fi
    
    # Create emergency backup before rollback
    log "Creating emergency backup before rollback..."
    local backup_name="emergency-backup-$(date +%Y%m%d-%H%M%S)"
    
    if kubectl get cronjob fueltune-backup-cronjob -n "$NAMESPACE" >/dev/null 2>&1; then
        kubectl create job --from=cronjob/fueltune-backup-cronjob "$backup_name" -n "$NAMESPACE" || warn "Failed to create backup job"
    fi
    
    # Perform the rollback
    log "Rolling back to revision $target_revision..."
    
    local rollback_cmd=(
        "helm" "rollback" "fueltune" "$target_revision"
        "-n" "$NAMESPACE"
        "--wait"
        "--timeout" "${TIMEOUT}s"
    )
    
    if ! "${rollback_cmd[@]}"; then
        error "Rollback command failed"
    fi
    
    log "Rollback command completed"
}

wait_for_rollback() {
    log "Waiting for rollback to complete..."
    
    # Wait for deployment to be available
    local wait_start
    wait_start=$(date +%s)
    local max_wait=$TIMEOUT
    
    while true; do
        local current_time
        current_time=$(date +%s)
        local elapsed=$((current_time - wait_start))
        
        if [[ $elapsed -gt $max_wait ]]; then
            error "Rollback timed out after ${max_wait}s"
        fi
        
        local deployment_status
        deployment_status=$(kubectl get deployment fueltune-app -n "$NAMESPACE" -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null || echo "False")
        
        if [[ "$deployment_status" == "True" ]]; then
            # Check if all replicas are ready
            local ready_replicas
            ready_replicas=$(kubectl get deployment fueltune-app -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
            
            local desired_replicas
            desired_replicas=$(kubectl get deployment fueltune-app -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
            
            if [[ "$ready_replicas" == "$desired_replicas" ]] && [[ "$ready_replicas" -gt 0 ]]; then
                log "Rollback completed - all replicas ready ($ready_replicas/$desired_replicas)"
                break
            fi
        fi
        
        info "Waiting for rollback to complete... (${elapsed}s elapsed)"
        sleep 10
    done
}

verify_rollback() {
    log "Verifying rollback success..."
    
    # Give the application time to stabilize
    sleep 30
    
    # Check deployment health
    if ! check_health; then
        error "Rollback verification failed - application is not healthy"
    fi
    
    # Show current status
    get_current_status
    
    log "Rollback verification passed"
}

show_rollback_summary() {
    log "Rollback Summary:"
    echo "================="
    
    # Current revision
    local current_revision
    current_revision=$(helm status fueltune -n "$NAMESPACE" -o json | jq -r '.version' 2>/dev/null || echo "unknown")
    echo "Current Revision: $current_revision"
    
    # Current version
    local current_version
    current_version=$(kubectl get deployment fueltune-app -n "$NAMESPACE" -o jsonpath='{.metadata.labels.version}' 2>/dev/null || echo "unknown")
    echo "Current Version: $current_version"
    
    # Pod status
    echo ""
    echo "Pod Status:"
    kubectl get pods -n "$NAMESPACE" -l app=fueltune
    
    echo ""
    log "Rollback completed successfully! 🔄"
    warn "Remember to investigate and fix the issues that caused the rollback"
}

# =============================================
# Main Function
# =============================================
main() {
    local target_revision=""
    local list_revisions_only=false
    local force_rollback=false
    local dry_run=false
    
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
            -r|--revision)
                target_revision="$2"
                shift 2
                ;;
            -l|--list)
                list_revisions_only=true
                shift
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --force)
                force_rollback=true
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
    
    # Validate environment
    case "$ENVIRONMENT" in
        development|staging|production) ;;
        *) error "Invalid environment: $ENVIRONMENT" ;;
    esac
    
    log "FuelTune Streamlit Rollback Tool"
    log "Environment: $ENVIRONMENT"
    log "Namespace: $NAMESPACE"
    
    # Check prerequisites
    check_prerequisites
    
    # List revisions and exit if requested
    if [[ "$list_revisions_only" == "true" ]]; then
        list_revisions
        exit 0
    fi
    
    # Get current status
    get_current_status
    
    # Determine target revision if not specified
    if [[ -z "$target_revision" ]]; then
        # Get previous revision
        target_revision=$(helm history fueltune -n "$NAMESPACE" -o json | jq -r '.[].revision' | tail -2 | head -1 2>/dev/null || echo "")
        
        if [[ -z "$target_revision" ]]; then
            error "Could not determine previous revision. Use --list to see available revisions."
        fi
        
        info "No revision specified, using previous revision: $target_revision"
    fi
    
    # Validate target revision exists
    if ! helm history fueltune -n "$NAMESPACE" | grep -q "^$target_revision"; then
        error "Revision $target_revision not found. Use --list to see available revisions."
    fi
    
    # Check if rollback is needed (unless forced)
    if [[ "$force_rollback" == "false" ]] && [[ "$dry_run" == "false" ]]; then
        if check_health; then
            warn "Application appears healthy. Use --force to rollback anyway."
            echo ""
            info "Current application status:"
            get_current_status
            exit 0
        else
            warn "Application health check failed, proceeding with rollback"
        fi
    fi
    
    # Confirm rollback for production
    if [[ "$ENVIRONMENT" == "production" ]] && [[ "$dry_run" == "false" ]]; then
        echo ""
        warn "You are about to rollback the PRODUCTION environment!"
        info "Target revision: $target_revision"
        echo ""
        read -p "Are you sure you want to continue? (type 'yes' to confirm): " -r
        if [[ ! $REPLY =~ ^yes$ ]]; then
            log "Rollback cancelled by user"
            exit 0
        fi
    fi
    
    # Perform rollback
    perform_rollback "$target_revision" "$dry_run"
    
    if [[ "$dry_run" == "false" ]]; then
        wait_for_rollback
        verify_rollback
        show_rollback_summary
    else
        log "Dry run completed"
    fi
}

# Run main function
main "$@"