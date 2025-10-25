output "instance_id" {
  description = "ID of the EC2 Mac instance"
  value       = aws_instance.mac.id
}

output "instance_public_ip" {
  description = "Public IP address of the Mac instance"
  value       = aws_eip.mac_eip.public_ip
}

output "instance_private_ip" {
  description = "Private IP address of the Mac instance"
  value       = aws_instance.mac.private_ip
}

output "instance_dns_name" {
  description = "Public DNS name of the Mac instance"
  value       = aws_instance.mac.public_dns
}

output "session_manager_command" {
  description = "Command to start a Session Manager session"
  value       = "aws ssm start-session --target ${aws_instance.mac.id} --region ${var.aws_region}"
}

output "session_manager_shell_command" {
  description = "Command to start an interactive shell via Session Manager"
  value       = "aws ssm start-session --target ${aws_instance.mac.id} --region ${var.aws_region} --document-name AWS-StartInteractiveCommand"
}

output "vnc_connection" {
  description = "VNC connection details"
  value = var.enable_vnc ? {
    host     = aws_eip.mac_eip.public_ip
    port     = 5900
    password = var.vnc_password
    command  = "vncviewer -passwd <(echo '${var.vnc_password}' | vncpasswd -f) ${aws_eip.mac_eip.public_ip}:5900"
  } : null
}

output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.mac_instance.id
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.mac_vpc.id
}

output "subnet_id" {
  description = "ID of the subnet"
  value       = aws_subnet.public.id
}

output "dedicated_host_id" {
  description = "ID of the dedicated host"
  value       = aws_ec2_host.mac_host.id
}

output "connection_info" {
  description = "Summary of connection information"
  value = {
    instance_id   = aws_instance.mac.id
    public_ip     = aws_eip.mac_eip.public_ip
    access_method = "AWS Systems Manager Session Manager"
    vnc_enabled   = var.enable_vnc
    vnc_port      = 5900
    vnc_host      = aws_eip.mac_eip.public_ip
    instance_type = var.instance_type
    ami_id        = data.aws_ami.mac2.id
    region        = var.aws_region
    iam_role      = aws_iam_role.ssm_role.name
  }
}
