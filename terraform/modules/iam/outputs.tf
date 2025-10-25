output "iam_role_name" {
  description = "Name of the IAM role"
  value       = aws_iam_role.ssm_role.name
}

output "iam_role_arn" {
  description = "ARN of the IAM role"
  value       = aws_iam_role.ssm_role.arn
}

output "instance_profile_name" {
  description = "Name of the IAM instance profile"
  value       = aws_iam_instance_profile.ssm_profile.name
}