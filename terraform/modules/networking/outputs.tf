output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.mac_vpc.id
}

output "subnet_id" {
  description = "ID of the public subnet"
  value       = aws_subnet.public.id
}

output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.mac_instance.id
}

output "internet_gateway_id" {
  description = "ID of the internet gateway"
  value       = aws_internet_gateway.main.id
}

output "route_table_id" {
  description = "ID of the route table"
  value       = aws_route_table.public.id
}