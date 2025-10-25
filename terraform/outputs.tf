# EC2 Instance Outputs
output "instance_id" {
  description = "ID of the EC2 Mac instance"
  value       = module.ec2.instance_id
}

output "instance_public_ip" {
  description = "Public IP address of the Mac instance"
  value       = module.ec2.instance_public_ip
}

output "instance_private_ip" {
  description = "Private IP address of the Mac instance"
  value       = module.ec2.instance_private_ip
}

output "instance_dns_name" {
  description = "Public DNS name of the Mac instance"
  value       = module.ec2.instance_dns_name
}

output "ami_id" {
  description = "AMI ID used for the instance"
  value       = module.ec2.ami_id
}

output "dedicated_host_id" {
  description = "ID of the dedicated host"
  value       = module.ec2.dedicated_host_id
}

# Access Methods
output "session_manager_command" {
  description = "Command to start a Session Manager session"
  value       = "aws ssm start-session --target ${module.ec2.instance_id} --region ${var.aws_region}"
}

output "session_manager_shell_command" {
  description = "Command to start an interactive shell via Session Manager"
  value       = "aws ssm start-session --target ${module.ec2.instance_id} --region ${var.aws_region} --document-name AWS-StartInteractiveCommand"
}

output "vnc_connection" {
  description = "VNC connection details"
  value = var.enable_vnc ? {
    host     = module.ec2.instance_public_ip
    port     = 5900
    password = var.vnc_password
    command  = "vncviewer -passwd <(echo '${var.vnc_password}' | vncpasswd -f) ${module.ec2.instance_public_ip}:5900"
  } : null
}

# Network Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "subnet_id" {
  description = "ID of the public subnet"
  value       = module.networking.subnet_id
}

output "security_group_id" {
  description = "ID of the security group"
  value       = module.networking.security_group_id
}

output "internet_gateway_id" {
  description = "ID of the internet gateway"
  value       = module.networking.internet_gateway_id
}

# IAM Outputs
output "iam_role_name" {
  description = "Name of the IAM role for Systems Manager"
  value       = module.iam.iam_role_name
}

# Comprehensive Connection Info
output "connection_info" {
  description = "Summary of connection information"
  value = {
    instance_id       = module.ec2.instance_id
    public_ip         = module.ec2.instance_public_ip
    private_ip        = module.ec2.instance_private_ip
    access_method     = "AWS Systems Manager Session Manager"
    vnc_enabled       = var.enable_vnc
    vnc_port          = 5900
    vnc_host          = module.ec2.instance_public_ip
    instance_type     = var.instance_type
    ami_id            = module.ec2.ami_id
    region            = var.aws_region
    iam_role          = module.iam.iam_role_name
    vpc_id            = module.networking.vpc_id
    security_group_id = module.networking.security_group_id
  }
}
