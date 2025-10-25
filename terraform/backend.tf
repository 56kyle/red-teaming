terraform {
  backend "s3" {
    bucket                      = "atlas-mac-terraform" # Change this to your bucket name
    key                         = "mac-instance/terraform.tfstate"
    region                      = "us-east-2"
    encrypt                     = true
    use_lockfile                = true # Native S3 locking (Terraform 1.10.0+)
    skip_credentials_validation = false
    skip_metadata_api_check     = false
  }
}
