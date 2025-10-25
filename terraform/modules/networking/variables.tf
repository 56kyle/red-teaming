variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
}

variable "subnet_cidr" {
  description = "CIDR block for public subnet"
  type        = string
}

variable "allowed_vnc_cidr" {
  description = "CIDR blocks allowed for VNC access"
  type        = string
}

variable "enable_vnc" {
  description = "Enable VNC server on the Mac instance"
  type        = bool
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
}