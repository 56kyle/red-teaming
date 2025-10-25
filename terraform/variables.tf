variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
}

variable "instance_name" {
  description = "Name tag for the EC2 Mac instance"
  type        = string
  default     = "atlas-testing-mac"
}

variable "instance_type" {
  description = "EC2 instance type (Mac instances)"
  type        = string
  default     = "mac2.metal"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  description = "CIDR block for public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "allowed_vnc_cidr" {
  description = "CIDR blocks allowed for VNC access"
  type        = string
  default     = "0.0.0.0/0" # Change this to your IP or range for security
}

variable "enable_vnc" {
  description = "Enable VNC server on the Mac instance"
  type        = bool
  default     = true
}

variable "vnc_password" {
  description = "Password for VNC access (set in terraform.tfvars)"
  type        = string
  sensitive   = true
  default     = "AtlasRedTeam123!" # Change this!
}

# Systems Manager Session Manager IAM role is configured in main.tf
# No SSH keys needed - access via AWS Systems Manager

variable "min_host_allocation_days" {
  description = "Minimum days to allocate Dedicated Host (AWS requirement: 1 day minimum)"
  type        = number
  default     = 1
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "AtlasRedTeaming"
    Environment = "testing"
    ManagedBy   = "Terraform"
  }
}
