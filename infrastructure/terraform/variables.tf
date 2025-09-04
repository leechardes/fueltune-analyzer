# =============================================
# FuelTune Streamlit - Terraform Variables
# =============================================

# =============================================
# General Variables
# =============================================
variable "environment" {
  description = "Environment name (production, staging, development)"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["production", "staging", "development"], var.environment)
    error_message = "Environment must be one of: production, staging, development."
  }
}

variable "region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "fueltune"
}

# =============================================
# Network Variables
# =============================================
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
  
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
}

# =============================================
# EKS Variables
# =============================================
variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"
}

variable "cluster_endpoint_public_access_cidrs" {
  description = "List of CIDR blocks for public access to cluster endpoint"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "node_instance_types" {
  description = "List of EC2 instance types for EKS nodes"
  type        = list(string)
  default     = ["t3.large", "t3.xlarge"]
}

variable "node_group_desired_size" {
  description = "Desired number of nodes in the EKS node group"
  type        = number
  default     = 3
  
  validation {
    condition     = var.node_group_desired_size >= 1
    error_message = "Node group desired size must be at least 1."
  }
}

variable "node_group_max_size" {
  description = "Maximum number of nodes in the EKS node group"
  type        = number
  default     = 10
  
  validation {
    condition     = var.node_group_max_size >= var.node_group_desired_size
    error_message = "Node group max size must be greater than or equal to desired size."
  }
}

variable "node_group_min_size" {
  description = "Minimum number of nodes in the EKS node group"
  type        = number
  default     = 1
  
  validation {
    condition     = var.node_group_min_size >= 1
    error_message = "Node group min size must be at least 1."
  }
}

variable "node_disk_size" {
  description = "Disk size for EKS nodes (in GB)"
  type        = number
  default     = 50
  
  validation {
    condition     = var.node_disk_size >= 20
    error_message = "Node disk size must be at least 20 GB."
  }
}

# =============================================
# Database Variables
# =============================================
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS instance (in GB)"
  type        = number
  default     = 100
  
  validation {
    condition     = var.db_allocated_storage >= 20
    error_message = "Database allocated storage must be at least 20 GB."
  }
}

variable "postgres_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "15.4"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "fueltune_prod"
  
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.db_name))
    error_message = "Database name must start with a letter and contain only letters, numbers, and underscores."
  }
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "fueltune"
  
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.db_username))
    error_message = "Database username must start with a letter and contain only letters, numbers, and underscores."
  }
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
  
  validation {
    condition     = length(var.db_password) >= 8
    error_message = "Database password must be at least 8 characters long."
  }
}

variable "db_backup_retention_period" {
  description = "Database backup retention period (days)"
  type        = number
  default     = 7
  
  validation {
    condition     = var.db_backup_retention_period >= 1 && var.db_backup_retention_period <= 35
    error_message = "Database backup retention period must be between 1 and 35 days."
  }
}

# =============================================
# Redis Variables
# =============================================
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_nodes" {
  description = "Number of Redis nodes"
  type        = number
  default     = 2
  
  validation {
    condition     = var.redis_num_nodes >= 1
    error_message = "Redis number of nodes must be at least 1."
  }
}

variable "redis_auth_token" {
  description = "Auth token for Redis cluster"
  type        = string
  sensitive   = true
  default     = null
  
  validation {
    condition = var.redis_auth_token == null || (
      length(var.redis_auth_token) >= 16 && 
      length(var.redis_auth_token) <= 128 &&
      can(regex("^[a-zA-Z0-9!&#$^<>-]*$", var.redis_auth_token))
    )
    error_message = "Redis auth token must be between 16-128 characters and contain only printable ASCII characters except '/', '\"', and '@'."
  }
}

# =============================================
# SSL/TLS Variables
# =============================================
variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "fueltune.example.com"
}

variable "certificate_arn" {
  description = "ARN of the SSL certificate in ACM"
  type        = string
  default     = null
}

variable "create_certificate" {
  description = "Whether to create a new SSL certificate"
  type        = bool
  default     = true
}

# =============================================
# Monitoring Variables
# =============================================
variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention period (days)"
  type        = number
  default     = 30
  
  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.log_retention_days)
    error_message = "Log retention days must be one of the supported values."
  }
}

# =============================================
# Backup Variables
# =============================================
variable "enable_backups" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Backup retention period (days)"
  type        = number
  default     = 30
  
  validation {
    condition     = var.backup_retention_days >= 1
    error_message = "Backup retention days must be at least 1."
  }
}

# =============================================
# Security Variables
# =============================================
variable "enable_waf" {
  description = "Enable AWS WAF for the load balancer"
  type        = bool
  default     = true
}

variable "allowed_cidr_blocks" {
  description = "List of CIDR blocks allowed to access the application"
  type        = list(string)
  default     = ["0.0.0.0/0"]
  
  validation {
    condition = length(var.allowed_cidr_blocks) > 0 && alltrue([
      for cidr in var.allowed_cidr_blocks : can(cidrhost(cidr, 0))
    ])
    error_message = "All CIDR blocks must be valid IPv4 CIDR notation."
  }
}

variable "enable_secrets_manager" {
  description = "Enable AWS Secrets Manager for sensitive data"
  type        = bool
  default     = true
}

# =============================================
# Cost Optimization Variables
# =============================================
variable "enable_spot_instances" {
  description = "Enable spot instances for cost optimization"
  type        = bool
  default     = false
}

variable "spot_instance_percentage" {
  description = "Percentage of spot instances in the node group"
  type        = number
  default     = 50
  
  validation {
    condition     = var.spot_instance_percentage >= 0 && var.spot_instance_percentage <= 100
    error_message = "Spot instance percentage must be between 0 and 100."
  }
}

# =============================================
# Application Variables
# =============================================
variable "app_version" {
  description = "Application version to deploy"
  type        = string
  default     = "latest"
}

variable "container_registry" {
  description = "Container registry URL"
  type        = string
  default     = "ghcr.io"
}

variable "image_repository" {
  description = "Container image repository"
  type        = string
  default     = "fueltune/streamlit"
}

# =============================================
# Feature Flags
# =============================================
variable "enable_autoscaling" {
  description = "Enable horizontal pod autoscaling"
  type        = bool
  default     = true
}

variable "enable_ingress_controller" {
  description = "Install NGINX ingress controller"
  type        = bool
  default     = true
}

variable "enable_cert_manager" {
  description = "Install cert-manager for SSL certificate management"
  type        = bool
  default     = true
}

variable "enable_external_dns" {
  description = "Install external-dns for DNS management"
  type        = bool
  default     = true
}

variable "enable_cluster_autoscaler" {
  description = "Enable cluster autoscaler"
  type        = bool
  default     = true
}

# =============================================
# Notification Variables
# =============================================
variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications"
  type        = string
  default     = ""
  sensitive   = true
}

variable "email_notifications" {
  description = "Email addresses for notifications"
  type        = list(string)
  default     = []
  
  validation {
    condition = alltrue([
      for email in var.email_notifications : can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", email))
    ])
    error_message = "All email addresses must be valid."
  }
}