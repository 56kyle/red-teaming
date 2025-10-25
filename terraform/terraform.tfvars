# AWS Configuration
aws_region = "us-west-2"

# Instance Configuration
instance_name = "atlas-testing-mac"
instance_type = "mac2.metal"

# Network Configuration
vpc_cidr    = "10.0.0.0/16"
subnet_cidr = "10.0.1.0/24"

# VNC Configuration
enable_vnc = true

# Dedicated Host Configuration
min_host_allocation_days = 1

# Tags
tags = {
  Project     = "AtlasRedTeaming"
  Environment = "testing"
  ManagedBy   = "Terraform"
}

# Environment variables for sensitive values:
# TF_VAR_allowed_vnc_cidr="x.x.x.x/32"  (your IP for VNC access)
# TF_VAR_vnc_password="YourSecurePassword"
