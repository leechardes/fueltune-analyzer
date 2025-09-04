#!/bin/bash
# =============================================
# FuelTune Streamlit - Deployment Script
# =============================================
# Zero-downtime deployment with rollback capability

set -euo pipefail

# =============================================
# Configuration
# =============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
NAMESPACE="${NAMESPACE:-fueltune}"
ENVIRONMENT="${ENVIRONMENT:-production}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
TIMEOUT="${TIMEOUT:-900}" # 15 minutes
DRY_RUN="${DRY_RUN:-false}"

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

Deploy FuelTune Streamlit application to Kubernetes.

OPTIONS:
    -h, --help              Show this help message
    -n, --namespace NAME    Kubernetes namespace (default: fueltune)
    -e, --environment ENV   Environment (development|staging|production)
    -t, --tag TAG          Docker image tag (default: latest)
    -d, --dry-run          Show what would be deployed without applying changes
    --timeout SECONDS      Deployment timeout in seconds (default: 900)
    --rollback             Rollback to previous deployment
    --force                Force deployment even if already at target version

Examples:
    $0                                      # Deploy latest to production
    $0 -e staging -t v1.2.3                # Deploy specific version to staging
    $0 --dry-run                           # Show what would be deployed
    $0 --rollback                          # Rollback to previous version

EOF
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check required tools
    local required_tools=("kubectl" "helm" "docker")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            error "$tool is not installed or not in PATH"
        fi
    done
    
    # Check kubectl connectivity
    if ! kubectl cluster-info >/dev/null 2>&1; then
        error "Cannot connect to Kubernetes cluster. Check your kubeconfig."
    fi
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        info "Creating namespace: $NAMESPACE"
        if [[ "$DRY_RUN" == "false" ]]; then
            kubectl create namespace "$NAMESPACE" || error "Failed to create namespace"
        fi
    fi
    
    log "Prerequisites check passed"
}

get_current_deployment() {
    kubectl get deployment fueltune-app -n "$NAMESPACE" -o jsonpath='{.metadata.labels.version}' 2>/dev/null || echo "none"
}

backup_current_deployment() {
    local current_version
    current_version=$(get_current_deployment)
    
    if [[ "$current_version" != "none" ]]; then
        log "Creating backup of current deployment (version: $current_version)"
        
        # Create backup job if enabled
        if kubectl get cronjob fueltune-backup-cronjob -n "$NAMESPACE" >/dev/null 2>&1; then
            local backup_job_name="fueltune-pre-deploy-backup-$(date +%Y%m%d-%H%M%S)"
            info "Starting backup job: $backup_job_name"
            
            if [[ "$DRY_RUN" == "false" ]]; then
                kubectl create job --from=cronjob/fueltune-backup-cronjob "$backup_job_name" -n "$NAMESPACE"
                
                # Wait for backup to complete (with timeout)
                local wait_time=0
                local max_wait=300  # 5 minutes
                
                while [[ $wait_time -lt $max_wait ]]; do
                    local job_status
                    job_status=$(kubectl get job "$backup_job_name" -n "$NAMESPACE" -o jsonpath='{.status.conditions[0].type}' 2>/dev/null || echo "")
                    
                    if [[ "$job_status" == "Complete" ]]; then
                        log "Backup completed successfully"
                        break
                    elif [[ "$job_status" == "Failed" ]]; then
                        warn "Backup job failed, continuing with deployment"
                        break
                    fi
                    
                    sleep 10
                    wait_time=$((wait_time + 10))
                done
                
                if [[ $wait_time -ge $max_wait ]]; then
                    warn "Backup job timed out, continuing with deployment"
                fi
            fi
        else
            info "No backup cronjob found, skipping backup"
        fi
    fi
}

deploy_application() {
    log "Starting deployment to environment: $ENVIRONMENT"
    log "Image tag: $IMAGE_TAG"
    log "Namespace: $NAMESPACE"
    
    local helm_args=(
        "upgrade"
        "--install"
        "fueltune"
        "$PROJECT_ROOT/infrastructure/helm/fueltune"
        "--namespace" "$NAMESPACE"
        "--create-namespace"
        "--values" "$PROJECT_ROOT/infrastructure/helm/fueltune/values-${ENVIRONMENT}.yaml"
        "--set" "image.tag=$IMAGE_TAG"
        "--set" "app.version=$IMAGE_TAG"
        "--wait"
        "--timeout" "${TIMEOUT}s"
    )
    
    # Add dry-run flag if specified
    if [[ "$DRY_RUN" == "true" ]]; then
        helm_args+=("--dry-run" "--debug")
        log "DRY RUN: Would execute: helm ${helm_args[*]}"
    fi
    
    # Execute deployment
    if [[ "$DRY_RUN" == "false" ]]; then
        log "Executing Helm deployment..."
        if ! helm "${helm_args[@]}"; then
            error "Helm deployment failed"
        fi
        log "Helm deployment completed"
    else
        # Just show what would be deployed
        helm "${helm_args[@]}"
        return 0
    fi
}

wait_for_deployment() {
    if [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi
    
    log "Waiting for deployment to be ready..."
    
    # Wait for deployment to be available
    if ! kubectl wait --for=condition=available deployment/fueltune-app \
        --timeout="${TIMEOUT}s" -n "$NAMESPACE"; then
        error "Deployment failed to become available within timeout"
    fi
    
    # Wait for all pods to be ready
    local ready_pods
    local total_pods
    local wait_count=0
    local max_wait_cycles=$((TIMEOUT / 10))
    
    while [[ $wait_count -lt $max_wait_cycles ]]; do
        ready_pods=$(kubectl get deployment fueltune-app -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' || echo "0")
        total_pods=$(kubectl get deployment fueltune-app -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' || echo "0")
        
        if [[ "$ready_pods" == "$total_pods" ]] && [[ "$ready_pods" -gt 0 ]]; then
            log "All pods are ready ($ready_pods/$total_pods)"
            break
        fi
        
        info "Waiting for pods to be ready ($ready_pods/$total_pods)..."
        sleep 10
        wait_count=$((wait_count + 1))
    done
    
    if [[ $wait_count -ge $max_wait_cycles ]]; then
        error "Pods failed to become ready within timeout"
    fi
}

run_health_checks() {
    if [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi
    
    log "Running health checks..."
    
    # Get service information
    local service_exists
    service_exists=$(kubectl get service fueltune-service -n "$NAMESPACE" >/dev/null 2>&1 && echo "true" || echo "false")
    
    if [[ "$service_exists" == "false" ]]; then
        warn "Service not found, skipping health checks"
        return 0
    fi
    
    # Port forward for health check
    local local_port=8080
    kubectl port-forward service/fueltune-service "$local_port:80" -n "$NAMESPACE" &
    local port_forward_pid=$!
    
    # Wait for port forward to establish
    sleep 5
    
    # Perform health check
    local health_check_passed=false
    local max_attempts=10
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -f "http://localhost:$local_port/_stcore/health" >/dev/null 2>&1; then
            health_check_passed=true
            break
        fi
        
        info "Health check attempt $((attempt + 1))/$max_attempts failed, retrying in 10s..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    # Clean up port forward
    kill $port_forward_pid 2>/dev/null || true
    
    if [[ "$health_check_passed" == "true" ]]; then
        log "Health checks passed"
    else
        error "Health checks failed after $max_attempts attempts"
    fi
}

rollback_deployment() {
    log "Rolling back deployment..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would rollback Helm release"
        return 0
    fi
    
    # Get rollback revision (previous version)
    local revision
    revision=$(helm history fueltune -n "$NAMESPACE" -o json | jq -r '.[].revision' | tail -2 | head -1 2>/dev/null || echo "")
    
    if [[ -z "$revision" ]]; then
        error "No previous revision found for rollback"
    fi
    
    log "Rolling back to revision: $revision"
    
    if ! helm rollback fueltune "$revision" -n "$NAMESPACE" --wait --timeout="${TIMEOUT}s"; then
        error "Rollback failed"
    fi
    
    log "Rollback completed successfully"
    wait_for_deployment
    run_health_checks
}

show_deployment_status() {
    if [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi
    
    log "Deployment Status Summary:"
    echo "=========================="
    
    # Deployment info
    local current_version
    current_version=$(get_current_deployment)
    echo "Current Version: $current_version"
    
    # Pod status
    echo ""
    echo "Pod Status:"
    kubectl get pods -n "$NAMESPACE" -l app=fueltune
    
    # Service status
    echo ""
    echo "Service Status:"
    kubectl get services -n "$NAMESPACE"
    
    # Ingress status
    if kubectl get ingress -n "$NAMESPACE" >/dev/null 2>&1; then
        echo ""
        echo "Ingress Status:"
        kubectl get ingress -n "$NAMESPACE"
    fi
    
    # HPA status
    if kubectl get hpa -n "$NAMESPACE" >/dev/null 2>&1; then
        echo ""
        echo "HPA Status:"
        kubectl get hpa -n "$NAMESPACE"
    fi
    
    echo ""
    log "Deployment completed successfully! 🎉"
}

cleanup_on_exit() {
    # Clean up any background processes
    jobs -p | xargs -r kill 2>/dev/null || true
}

# =============================================
# Main Function
# =============================================
main() {
    # Set up cleanup trap
    trap cleanup_on_exit EXIT
    
    # Parse command line arguments
    local rollback_requested=false
    local force_deploy=false
    
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
            -t|--tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --rollback)
                rollback_requested=true
                shift
                ;;
            --force)
                force_deploy=true
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
        *) error "Invalid environment: $ENVIRONMENT. Use development, staging, or production." ;;
    esac
    
    # Main deployment flow
    log "Starting FuelTune Streamlit deployment"
    log "Environment: $ENVIRONMENT"
    log "Namespace: $NAMESPACE"
    
    if [[ "$rollback_requested" == "true" ]]; then
        check_prerequisites
        rollback_deployment
        show_deployment_status
        return 0
    fi
    
    # Check if already at target version (unless forced)
    if [[ "$force_deploy" == "false" ]]; then
        local current_version
        current_version=$(get_current_deployment)
        if [[ "$current_version" == "$IMAGE_TAG" ]]; then
            log "Already at target version ($IMAGE_TAG), skipping deployment"
            log "Use --force to deploy anyway"
            return 0
        fi
    fi
    
    # Standard deployment flow
    check_prerequisites
    backup_current_deployment
    deploy_application
    wait_for_deployment
    run_health_checks
    show_deployment_status
}

# Run main function with all arguments
main "$@"