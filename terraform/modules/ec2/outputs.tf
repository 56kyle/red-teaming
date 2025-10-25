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

output "dedicated_host_id" {
  description = "ID of the dedicated host"
  value       = aws_ec2_host.mac_host.id
}

output "eip_id" {
  description = "ID of the Elastic IP"
  value       = aws_eip.mac_eip.id
}

output "ami_id" {
  description = "AMI ID of the instance"
  value       = data.aws_ami.mac2.id
}