terraform {
  required_version = ">= 1.10.0" # For native S3 state locking

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

# Get latest Mac2 AMI
data "aws_ami" "mac2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn-ec2-macos-12.7*"] # Mac2 with Monterey/Ventura
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

# IAM Role for Systems Manager Session Manager access
resource "aws_iam_role" "ssm_role" {
  name = "atlas-mac-ssm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(
    var.tags,
    { Name = "atlas-mac-ssm-role" }
  )
}

# Attach Systems Manager policy for Session Manager access
resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "ssm_profile" {
  name = "atlas-mac-ssm-profile"
  role = aws_iam_role.ssm_role.name
}

# Dedicated Host for Mac instance (required for Mac instances)
resource "aws_ec2_host" "mac_host" {
  availability_zone      = data.aws_availability_zones.available.names[0]
  auto_placement         = "off"
  host_family            = "mac"
  instance_family        = "mac2"
  instance_type          = var.instance_type
  availability_zone_id   = data.aws_availability_zones.available.zone_ids[0]
  auto_placement_enabled = false

  tags = merge(
    var.tags,
    { Name = "atlas-mac-dedicated-host" }
  )
}

# Mac Instance
resource "aws_instance" "mac" {
  # Use the dedicated host
  host_id                = aws_ec2_host.mac_host.id
  instance_type          = var.instance_type
  ami                    = data.aws_ami.mac2.id
  iam_instance_profile   = aws_iam_instance_profile.ssm_profile.name
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.mac_instance.id]

  # Enable detailed monitoring
  monitoring = true

  # Root volume configuration
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 250 # Mac instances typically need more disk space
    delete_on_termination = true
    encrypted             = true

    tags = merge(
      var.tags,
      { Name = "atlas-mac-root-volume" }
    )
  }

  # User data for VNC setup
  user_data = var.enable_vnc ? base64encode(templatefile("${path.module}/vnc_setup.sh", {
    vnc_password = var.vnc_password
  })) : null

  tags = merge(
    var.tags,
    { Name = var.instance_name }
  )

  # Explicitly wait for the instance to reach running state
  depends_on = [aws_ec2_host.mac_host]

  lifecycle {
    create_before_destroy = false
    prevent_destroy       = false
  }
}

# Elastic IP for stable access
resource "aws_eip" "mac_eip" {
  instance = aws_instance.mac.id
  domain   = "vpc"

  tags = merge(
    var.tags,
    { Name = "atlas-mac-eip" }
  )

  depends_on = [aws_internet_gateway.main]
}
