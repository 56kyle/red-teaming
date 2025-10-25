# Deployment Checklist for Atlas Mac Instance

Use this checklist to ensure you have everything ready before deploying.

## Pre-Deployment

- [ ] AWS Account with appropriate permissions
  - [ ] EC2 (full access)
  - [ ] IAM (role creation)
  - [ ] S3 (bucket creation)
  - [ ] Systems Manager (Session Manager)

- [ ] Tools installed
  - [ ] Terraform >= 1.10.0 (`terraform version`)
  - [ ] AWS CLI v2 (`aws --version`)
  - [ ] Session Manager plugin (`aws ssm start-session --help`)
  - [ ] VNC client (optional but recommended)

- [ ] AWS Credentials configured
  - [ ] Run `aws sts get-caller-identity` to verify

## Deployment Steps

### Step 1: Create S3 Backend Bucket

```bash
# Copy the bucket creation commands from CLAUDE.md and run them
# Bucket name: atlas-mac-terraform-state
# Region: us-west-2
```

**After**: Verify with `aws s3 ls | grep atlas-mac`

### Step 2: Set Required Environment Variables

```bash
export TF_VAR_vnc_password="YourSecurePassword123!"
export TF_VAR_allowed_vnc_cidr="YOUR_IP/32"  # Recommended: restrict to your IP
```

**Check**: Echo variables to verify
```bash
echo $TF_VAR_vnc_password
echo $TF_VAR_allowed_vnc_cidr
```

### Step 3: Initialize Terraform

```bash
cd terraform
terraform init
```

**Verify**: Look for "Terraform has been successfully configured!"

### Step 4: Review Planned Changes

```bash
terraform plan > tfplan.txt
# Review tfplan.txt for expected resources
# Should see: 1 new VPC, 1 new EC2 Host, 1 new Instance, 1 IAM role, etc.
```

### Step 5: Create Infrastructure

```bash
terraform apply tfplan.txt
# Or: terraform apply (with interactive approval)
```

**Wait**: 5-10 minutes for Mac instance to be allocated

**Verify**:
```bash
terraform output
# Should show instance_id, public IP, connection commands
```

## Post-Deployment

### Immediate (within 5 minutes)

- [ ] Check instance is running: `aws ec2 describe-instances --instance-ids <id>`
- [ ] Get public IP: `terraform output -raw instance_public_ip`

### After 2-3 minutes

- [ ] Systems Manager Session Manager should be available
- [ ] Test connection:
```bash
INSTANCE_ID=$(terraform output -raw instance_id)
aws ssm start-session --target $INSTANCE_ID --region us-west-2 --document-name AWS-StartInteractiveCommand
```

### After 5+ minutes

- [ ] VNC server should be running
- [ ] Test VNC: `vncviewer <public-ip>:5900`
- [ ] Enter VNC password when prompted

## Troubleshooting During Deployment

| Issue | Solution |
|-------|----------|
| "Bucket already exists" | Use unique bucket name in backend.tf |
| "ResourceNotAvailable" | Mac instances not available in region (try us-west-2) |
| "Service role not found" | Wait 30 seconds for IAM propagation |
| "terraform init fails" | Run `aws configure` and verify credentials |

## Cost Management

**Hourly Cost**: ~$2.00/hour (Dedicated Host + instance)

**To minimize costs**:
- Destroy when not testing: `terraform destroy`
- Use for focused testing sessions only
- Monitor AWS billing dashboard

## Cleanup

When done testing:

```bash
# Terminate all resources
terraform destroy

# Verify deletion
terraform output  # Should error or be empty
```

## Post-Deployment Testing

### Test Systems Manager Access
```bash
aws ssm start-session --target $(terraform output -raw instance_id) --region us-west-2 --document-name AWS-StartInteractiveCommand
whoami  # Should show: ec2-user
```

### Test VNC Setup
```bash
# Inside SSM session:
cat ~/.vnc/vnc.log  # Should show VNC running
```

### Test Atlas Browser Access
1. Connect via VNC to Mac instance
2. Open Safari
3. Navigate to Atlas browser (or download from OpenAI)
4. Begin red teaming

## Support

For issues, check:
1. CLAUDE.md - Full documentation
2. README.md - Quick reference
3. AWS CloudWatch Logs (EC2 instance)
4. VNC logs: `~/.vnc/vnc.log` (via SSM session)

---

**Status**: Ready to deploy ✓