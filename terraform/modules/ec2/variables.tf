variable "instance_name" {
  description = "Name tag for the EC2 Mac instance"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type (Mac instances)"
  type        = string
}

variable "iam_instance_profile_name" {
  description = "Name of the IAM instance profile"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for the instance"
  type        = string
}

variable "security_group_id" {
  description = "Security group ID for the instance"
  type        = string
}

variable "enable_vnc" {
  description = "Enable VNC server on the Mac instance"
  type        = bool
}

variable "vnc_password" {
  description = "Password for VNC access"
  type        = string
  sensitive   = true
}

variable "root_volume_size" {
  description = "Size of the root volume in GB"
  type        = number
}

variable "root_volume_type" {
  description = "Type of the root volume"
  type        = string
}

variable "internet_gateway_id" {
  description = "Internet gateway ID for EIP dependency"
  type        = string
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
}