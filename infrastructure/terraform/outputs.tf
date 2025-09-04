# =============================================
# FuelTune Streamlit - Terraform Outputs
# =============================================

# =============================================
# Network Outputs
# =============================================
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "nat_gateway_ids" {
  description = "IDs of the NAT Gateways"
  value       = aws_nat_gateway.main[*].id
}

# =============================================
# EKS Outputs
# =============================================
output "cluster_id" {
  description = "EKS cluster ID"
  value       = aws_eks_cluster.main.id
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.main.name
}

output "cluster_arn" {
  description = "EKS cluster ARN"
  value       = aws_eks_cluster.main.arn
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = aws_eks_cluster.main.certificate_authority[0].data
}

output "cluster_version" {
  description = "EKS cluster Kubernetes version"
  value       = aws_eks_cluster.main.version
}

output "node_group_arn" {
  description = "EKS node group ARN"
  value       = aws_eks_node_group.main.arn
}

output "node_group_status" {
  description = "EKS node group status"
  value       = aws_eks_node_group.main.status
}

# =============================================
# Database Outputs
# =============================================
output "db_instance_id" {
  description = "RDS instance ID"
  value       = aws_db_instance.main.id
}

output "db_instance_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "db_instance_port" {
  description = "RDS instance port"
  value       = aws_db_instance.main.port
}

output "db_instance_name" {
  description = "RDS instance database name"
  value       = aws_db_instance.main.db_name
}

output "db_instance_username" {
  description = "RDS instance username"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "database_url" {
  description = "PostgreSQL connection URL"
  value       = "postgresql://${aws_db_instance.main.username}:${var.db_password}@${aws_db_instance.main.endpoint}:${aws_db_instance.main.port}/${aws_db_instance.main.db_name}"
  sensitive   = true
}

# =============================================
# Redis Outputs
# =============================================
output "redis_cluster_id" {
  description = "ElastiCache Redis cluster ID"
  value       = aws_elasticache_replication_group.main.id
}

output "redis_primary_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
  sensitive   = true
}

output "redis_reader_endpoint" {
  description = "ElastiCache Redis reader endpoint"
  value       = aws_elasticache_replication_group.main.reader_endpoint_address
  sensitive   = true
}

output "redis_port" {
  description = "ElastiCache Redis port"
  value       = aws_elasticache_replication_group.main.port
}

output "redis_url" {
  description = "Redis connection URL"
  value       = var.redis_auth_token != null ? "redis://:${var.redis_auth_token}@${aws_elasticache_replication_group.main.primary_endpoint_address}:${aws_elasticache_replication_group.main.port}" : "redis://${aws_elasticache_replication_group.main.primary_endpoint_address}:${aws_elasticache_replication_group.main.port}"
  sensitive   = true
}

# =============================================
# Load Balancer Outputs
# =============================================
output "load_balancer_arn" {
  description = "ALB ARN"
  value       = aws_lb.main.arn
}

output "load_balancer_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name
}

output "load_balancer_zone_id" {
  description = "ALB zone ID"
  value       = aws_lb.main.zone_id
}

# =============================================
# Security Outputs
# =============================================
output "eks_cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = aws_security_group.eks_cluster.id
}

output "eks_nodes_security_group_id" {
  description = "EKS nodes security group ID"
  value       = aws_security_group.eks_nodes.id
}

output "rds_security_group_id" {
  description = "RDS security group ID"
  value       = aws_security_group.rds.id
}

output "alb_security_group_id" {
  description = "ALB security group ID"
  value       = aws_security_group.alb.id
}

# =============================================
# IAM Outputs
# =============================================
output "eks_cluster_role_arn" {
  description = "EKS cluster IAM role ARN"
  value       = aws_iam_role.eks_cluster.arn
}

output "eks_nodes_role_arn" {
  description = "EKS nodes IAM role ARN"
  value       = aws_iam_role.eks_nodes.arn
}

# =============================================
# KMS Outputs
# =============================================
output "eks_kms_key_arn" {
  description = "EKS KMS key ARN"
  value       = aws_kms_key.eks.arn
}

output "rds_kms_key_arn" {
  description = "RDS KMS key ARN"
  value       = aws_kms_key.rds.arn
}

# =============================================
# S3 Outputs
# =============================================
output "alb_logs_bucket" {
  description = "S3 bucket for ALB access logs"
  value       = aws_s3_bucket.alb_logs.id
}

output "backups_bucket" {
  description = "S3 bucket for backups"
  value       = aws_s3_bucket.backups.id
}

# =============================================
# CloudWatch Outputs
# =============================================
output "cloudwatch_log_group_name" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.eks.name
}

# =============================================
# Application Outputs
# =============================================
output "application_url" {
  description = "Application URL"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_lb.main.dns_name}"
}

output "monitoring_urls" {
  description = "Monitoring URLs"
  value = {
    grafana    = var.domain_name != "" ? "https://monitoring.${var.domain_name}/grafana" : "https://${aws_lb.main.dns_name}/grafana"
    prometheus = var.domain_name != "" ? "https://monitoring.${var.domain_name}/prometheus" : "https://${aws_lb.main.dns_name}/prometheus"
  }
}

# =============================================
# Kubectl Configuration
# =============================================
output "kubectl_config" {
  description = "kubectl config command"
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${aws_eks_cluster.main.name}"
}

# =============================================
# Connection Information
# =============================================
output "connection_info" {
  description = "Connection information for the deployed infrastructure"
  value = {
    cluster_name     = aws_eks_cluster.main.name
    cluster_endpoint = aws_eks_cluster.main.endpoint
    region          = var.region
    vpc_id          = aws_vpc.main.id
    application_url = var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_lb.main.dns_name}"
  }
}

# =============================================
# Resource Tags
# =============================================
output "common_tags" {
  description = "Common tags applied to resources"
  value       = local.common_tags
}

# =============================================
# Environment Information
# =============================================
output "environment_info" {
  description = "Environment information"
  value = {
    environment   = var.environment
    project_name  = var.project_name
    region        = var.region
    created_at    = timestamp()
  }
}