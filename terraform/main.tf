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

# Networking Module
module "networking" {
  source = "./modules/networking"

  vpc_cidr         = var.vpc_cidr
  subnet_cidr      = var.subnet_cidr
  allowed_vnc_cidr = var.allowed_vnc_cidr
  enable_vnc       = var.enable_vnc
  tags             = var.tags
}

# IAM Module
module "iam" {
  source = "./modules/iam"

  tags = var.tags
}

# EC2 Module
module "ec2" {
  source = "./modules/ec2"

  instance_name             = var.instance_name
  instance_type             = var.instance_type
  iam_instance_profile_name = module.iam.instance_profile_name
  subnet_id                 = module.networking.subnet_id
  security_group_id         = module.networking.security_group_id
  enable_vnc                = var.enable_vnc
  vnc_password              = var.vnc_password
  root_volume_size          = var.root_volume_size
  root_volume_type          = var.root_volume_type
  internet_gateway_id       = module.networking.internet_gateway_id
  tags                      = var.tags
}
