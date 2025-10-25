# AWS Mac Instance Terraform Setup for Atlas Red Teaming

Quick start guide for provisioning a Mac instance to test OpenAI's Atlas browser.

## Quick Start

```bash
# 1. Set environment variables (required)
export TF_VAR_vnc_password="SecurePassword123!"
export TF_VAR_allowed_vnc_cidr="YOUR_IP/32"  # Optional, restricts VNC access

# 2. Initialize (one time)
terraform init

# 3. Create infrastructure
terraform plan    # Review first
terraform apply   # Create resources

# 4. Connect
terraform output  # View connection info
aws ssm start-session --target $(terraform output -raw instance_id) --region us-west-2 --document-name AWS-StartInteractiveCommand
```

## What Gets Created

- **EC2 Mac2.metal Instance** (M2 chip) in us-west-2
- **Dedicated Host** (required for Mac instances)
- **VPC & Security Group** (VNC port 5900 open)
- **Elastic IP** (stable public IP)
- **IAM Role** (for Systems Manager access)
- **250GB encrypted storage** (gp3)

## Access Methods

### Primary: AWS Systems Manager (Recommended)
```bash
# Interactive shell
aws ssm start-session --target <instance-id> --region us-west-2 --document-name AWS-StartInteractiveCommand

# Port forwarding (for VNC through encrypted tunnel)
aws ssm start-session --target <instance-id> --region us-west-2 \
  --document-name AWS-StartPortForwardingSession \
  --parameters "localPortNumber=5900,portNumber=5900"
```

### Secondary: VNC (Direct)
```bash
# Get public IP
terraform output -raw instance_public_ip

# Connect
vncviewer <public-ip>:5900
```

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `TF_VAR_vnc_password` | VNC server password | `"MySecure!Pass"` |
| `TF_VAR_allowed_vnc_cidr` | VNC access restriction | `"1.2.3.4/32"` |
| `TF_VAR_aws_region` | AWS region (default: us-west-2) | `"us-west-2"` |

## Costs

- Dedicated Host: ~$1.90/hour
- Storage: ~$10/month
- Data transfer: Minimal

**Stop the clock**: `terraform destroy` (releases resources)

## Troubleshooting

**Can't connect via Systems Manager?**
- Wait 2-3 minutes for SSM agent to register
- Check security group allows outbound HTTPS (port 443)
- Verify IAM user has SSM permissions

**VNC not working?**
- Check VNC logs: `cat ~/.vnc/vnc.log`
- Verify password is correct
- Ensure security group allows port 5900

**Terraform state issues?**
- State is locked in S3 using native locking
- Lock files expire automatically after 5 minutes

## Important Notes

- **First launch**: Instance allocation takes 5-10 minutes
- **Minimum commitment**: 24 hours (AWS requirement for Dedicated Hosts)
- **macOS version**: Automatically gets latest Mac2 AMI (Ventura/Sonoma)
- **No SSH keys**: Access is strictly via Systems Manager or VNC

## Files

- `main.tf` - EC2, IAM, Dedicated Host resources
- `backend.tf` - S3 state backend with native locking
- `security.tf` - VPC, subnets, security groups
- `variables.tf` - Input variable definitions
- `outputs.tf` - Output values (IPs, commands, etc.)
- `terraform.tfvars` - Default variable values
- `vnc_setup.sh` - VNC installation script (runs on instance startup)

## See Also

Full documentation in `../CLAUDE.md`
