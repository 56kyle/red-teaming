# CLAUDE.md

Red Teaming Infrastructure for OpenAI Atlas Browser on AWS Mac Instance

## Project Overview

This repository contains Terraform infrastructure code to provision an AWS EC2 Mac (M2) instance for red-teaming OpenAI's Atlas browser. The setup includes:

- EC2 Mac2.metal instance in us-west-2
- Dedicated Host allocation (required for Mac instances)
- AWS Systems Manager Session Manager for secure remote access
- VNC server for GUI access
- S3 backend with native state locking (Terraform 1.10.0+)

## Architecture & Design Decisions

### Authentication & Access
- **Primary Access**: AWS Systems Manager Session Manager (no SSH keys, IAM-based, audit-logged)
- **Secondary Access**: VNC over public IP (encrypted session recommended)
- **Security Groups**: Minimal ingress - only VNC port 5900, all outbound allowed

### State Management
- **Backend**: S3 with native state locking (`.tflock` files, no DynamoDB)
- **Encryption**: State file encrypted at rest in S3
- **Versioning**: S3 bucket versioning enabled for state recovery

### Infrastructure
- **Instance Type**: mac2.metal (Apple M2 chip)
- **Region**: us-west-2 (Mac instance availability)
- **Volume**: 100GB gp3 encrypted root volume (sufficient for Atlas + Playwright)
- **Network**: Public subnet with Elastic IP for stable access
- **VNC**: Disabled by default (opt-in if needed)

## Prerequisites

1. **AWS Account** with appropriate IAM permissions:
   - EC2 (Dedicated Hosts, Instances)
   - IAM (Roles, Policies)
   - S3 (Bucket creation)
   - Systems Manager (Session Manager)

2. **Tools**:
   - Terraform >= 1.10.0
   - AWS CLI v2
   - Session Manager plugin: `aws-cli-bundle` or `sessionmanagerplugin`

3. **AWS Credentials**: Configure via `aws configure` or environment variables

## Setup Instructions

### 1. Initialize S3 Backend Bucket

Create the S3 bucket for Terraform state (one-time):

```bash
cd terraform
aws s3api create-bucket \
  --bucket atlas-mac-terraform \
  --region us-west-2 \
  --create-bucket-configuration LocationConstraint=us-west-2

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket atlas-mac-terraform \
  --versioning-configuration Status=Enabled

# Enable default encryption
aws s3api put-bucket-encryption \
  --bucket atlas-mac-terraform \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Block public access
aws s3api put-public-access-block \
  --bucket atlas-mac-terraform \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### 2. Set Environment Variables (Optional - VNC Only)

VNC is disabled by default. Only set these if you need GUI access via VNC:

```bash
# Enable VNC server
export TF_VAR_enable_vnc="true"

# Required: Set VNC password (must be provided if enable_vnc is true)
export TF_VAR_vnc_password="YourSecureVNCPassword123!"

# Required: Restrict VNC access to your IP (no default for security)
export TF_VAR_allowed_vnc_cidr="YOUR_IP/32"
```

Session Manager is the recommended primary access method (no setup needed).

### 3. Initialize Terraform

```bash
cd terraform
terraform init
```

### 4. Plan & Apply

```bash
# Review what will be created
terraform plan

# Create infrastructure
terraform apply
```

Note: Mac instance allocation requires a minimum 24-hour commitment. First allocation may take 5-10 minutes.

## Usage

### Connect via Session Manager

```bash
# Get instance ID from outputs
INSTANCE_ID=$(terraform output -raw instance_id)

# Start interactive shell
aws ssm start-session --target $INSTANCE_ID --region us-west-2 --document-name AWS-StartInteractiveCommand
```

### Connect via VNC

```bash
# Get VNC host from outputs
VNC_HOST=$(terraform output -raw instance_public_ip)

# macOS/Linux
vncviewer $VNC_HOST:5900

# Or use the open command
open vnc://$VNC_HOST:5900
```

### View Instance Details

```bash
terraform output
terraform output connection_info
```

## Cost Considerations

- **Dedicated Host**: ~$1.90/hour (us-west-2, Mac2)
- **Data Transfer**: Minimal if using Session Manager only
- **Storage**: ~$4/month (100GB gp3 volume)
- **Total**: ~$130-170/month for 24/7 operation

Terminate when not in use:

```bash
terraform destroy
```

## Troubleshooting

### Session Manager not connecting
- Ensure IAM user has `AmazonSSMManagedInstanceCore` policy
- Check instance has public IP (Elastic IP assigned)
- Verify security group allows outbound HTTPS (port 443)

### VNC password not working
- SSH via Session Manager and check VNC logs:
  ```
  cat ~/.vnc/vnc.log
  cat ~/.vnc/vnc.err
  ```

### Instance not appearing in Session Manager
- Allow 2-3 minutes for SSM agent to register
- Check EC2 instance has IAM role attached
- Verify instance public IP is reachable

## File Structure

```
terraform/
├── main.tf              # EC2 instance, IAM, Dedicated Host
├── backend.tf           # S3 backend with native locking
├── security.tf          # VPC, subnets, security groups
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── terraform.tfvars     # Variable values (env var overrides)
├── vnc_setup.sh         # VNC installation & configuration
└── .gitignore          # Ignore state files
```
