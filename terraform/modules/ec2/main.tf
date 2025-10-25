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

# Dedicated Host for Mac instance (required for Mac instances)
resource "aws_ec2_host" "mac_host" {
  availability_zone = data.aws_availability_zones.available.names[0]
  instance_type     = var.instance_type

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
  iam_instance_profile   = var.iam_instance_profile_name
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]

  # Enable detailed monitoring
  monitoring = true

  # Root volume configuration
  root_block_device {
    volume_type           = var.root_volume_type
    volume_size           = var.root_volume_size
    delete_on_termination = true
    encrypted             = true

    tags = merge(
      var.tags,
      { Name = "atlas-mac-root-volume" }
    )
  }

  # User data for VNC setup
  user_data = var.enable_vnc ? base64encode(templatefile("${path.module}/../../scripts/vnc_setup.sh", {
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

  depends_on = [var.internet_gateway_id]
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}