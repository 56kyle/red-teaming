# Red Teaming Infrastructure for OpenAI Atlas Browser

AWS Mac instance infrastructure for red-teaming OpenAI's Atlas browser.

## Quick Start

```bash
# Set environment variable
export TF_VAR_vnc_password="YourSecurePassword123!"
export TF_VAR_allowed_vnc_cidr="YOUR_IP/32"  # Optional

# Deploy
cd terraform
terraform init
terraform apply

# Connect
INSTANCE_ID=$(terraform output -raw instance_id)
aws ssm start-session --target $INSTANCE_ID --region us-west-2 \
  --document-name AWS-StartInteractiveCommand
```

## Documentation

- **[docs/terraform.md](./docs/terraform.md)** - Terraform quick start
- **[terraform/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Step-by-step deployment checklist
- **[CLAUDE.md](./CLAUDE.md)** - Full architecture & design details

## What Gets Created

- EC2 Mac2.metal instance (Apple M2, 250GB storage, us-west-2)
- Dedicated Host (required for Mac instances)
- VPC, public subnet, security group (VNC port 5900)
- Elastic IP (stable public address)
- IAM role (Systems Manager access)
- S3-backed Terraform state (encrypted, locked)

## Access Methods

1. **Systems Manager** (recommended): `aws ssm start-session --target <instance-id>`
2. **VNC**: Connect to public IP on port 5900 with password

## Costs

- ~$1.90/hour for Dedicated Host + $0.15/hour for storage = ~$2.05/hour
- Run `terraform destroy` when done to stop charges
- 24-hour minimum commitment for Dedicated Host

## Troubleshooting

**Can't connect via Systems Manager?**
- Wait 2-3 minutes for SSM agent registration
- Verify security group allows outbound HTTPS (443)
- Check IAM has `AmazonSSMManagedInstanceCore` policy

See [DEPLOYMENT.md](docs/DEPLOYMENT.md#troubleshooting-during-deployment) for more.

---

See [CLAUDE.md](./CLAUDE.md) for full project architecture.