# VPC
resource "aws_vpc" "mac_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(
    var.tags,
    { Name = "atlas-mac-vpc" }
  )
}

# Public Subnet
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.mac_vpc.id
  cidr_block              = var.subnet_cidr
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = merge(
    var.tags,
    { Name = "atlas-mac-public-subnet" }
  )
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.mac_vpc.id

  tags = merge(
    var.tags,
    { Name = "atlas-mac-igw" }
  )
}

# Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.mac_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(
    var.tags,
    { Name = "atlas-mac-rt" }
  )
}

# Route Table Association
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Security Group for Mac Instance
resource "aws_security_group" "mac_instance" {
  name        = "atlas-mac-sg"
  description = "Security group for Atlas Mac testing instance"
  vpc_id      = aws_vpc.mac_vpc.id

  tags = merge(
    var.tags,
    { Name = "atlas-mac-sg" }
  )
}

# Note: SSH is not needed - access is via AWS Systems Manager Session Manager
# Systems Manager uses the EC2 Instance Connect service and doesn't require open ports

# Ingress: VNC
resource "aws_security_group_rule" "vnc_in" {
  count             = var.enable_vnc ? 1 : 0
  type              = "ingress"
  from_port         = 5900
  to_port           = 5900
  protocol          = "tcp"
  cidr_blocks       = [var.allowed_vnc_cidr]
  security_group_id = aws_security_group.mac_instance.id

  description = "VNC access"
}

# Ingress: VNC HTTP (optional, some VNC clients use 6080)
resource "aws_security_group_rule" "vnc_http_in" {
  count             = var.enable_vnc ? 1 : 0
  type              = "ingress"
  from_port         = 6080
  to_port           = 6080
  protocol          = "tcp"
  cidr_blocks       = [var.allowed_vnc_cidr]
  security_group_id = aws_security_group.mac_instance.id

  description = "VNC HTTP access"
}

# Egress: Allow all outbound traffic
resource "aws_security_group_rule" "all_out" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.mac_instance.id

  description = "Allow all outbound traffic"
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}
