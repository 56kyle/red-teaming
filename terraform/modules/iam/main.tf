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