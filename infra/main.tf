###############################################################################
# Trajectory infrastructure - personal job hunt tool.
#
# Provisions:
#   - 1x t4g.small EC2 (ARM, ~$12/mo) running the FastAPI backend in Docker
#   - 1x db.t4g.micro RDS Postgres (~$13/mo, free tier eligible)
#   - Security groups locked to your IP for SSH and the API port
#   - An Elastic IP so the address doesn't change on reboot
#
# Frontend goes on AWS Amplify (configured in console).
###############################################################################

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.70" }
  }
}

provider "aws" {
  region = var.region
}

variable "region"         { default = "eu-west-2" }
variable "my_ip"          { description = "Your IP in CIDR form, e.g. 1.2.3.4/32" }
variable "db_password"    { sensitive = true }
variable "api_key"        { sensitive = true }
variable "openai_api_key" { sensitive = true }
variable "ssh_public_key" { description = "Contents of your ~/.ssh/id_ed25519.pub" }

data "aws_vpc" "default" { default = true }
data "aws_subnets" "default" {
  filter { name = "vpc-id"; values = [data.aws_vpc.default.id] }
}

resource "aws_security_group" "api" {
  name        = "trajectory-api"
  description = "API + SSH from my IP"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }
  ingress {
    description = "API"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "db" {
  name        = "trajectory-db"
  description = "Postgres from API only"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.api.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_subnet_group" "main" {
  name       = "trajectory-db-subnets"
  subnet_ids = data.aws_subnets.default.ids
}

resource "aws_db_instance" "postgres" {
  identifier              = "trajectory-db"
  engine                  = "postgres"
  engine_version          = "16.4"
  instance_class          = "db.t4g.micro"
  allocated_storage       = 20
  storage_type            = "gp3"
  db_name                 = "trajectory"
  username                = "trajectory"
  password                = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.main.name
  vpc_security_group_ids  = [aws_security_group.db.id]
  skip_final_snapshot     = true
  publicly_accessible     = false
  backup_retention_period = 7
  apply_immediately       = true
}

resource "aws_key_pair" "main" {
  key_name   = "trajectory-key"
  public_key = var.ssh_public_key
}

data "aws_ami" "al2023_arm" {
  most_recent = true
  owners      = ["amazon"]
  filter { name = "name";          values = ["al2023-ami-2023.*-arm64"] }
  filter { name = "architecture";  values = ["arm64"] }
  filter { name = "virtualization-type"; values = ["hvm"] }
}

resource "aws_instance" "api" {
  ami                    = data.aws_ami.al2023_arm.id
  instance_type          = "t4g.small"
  key_name               = aws_key_pair.main.key_name
  vpc_security_group_ids = [aws_security_group.api.id]
  subnet_id              = data.aws_subnets.default.ids[0]

  user_data = <<-EOF
    #!/bin/bash
    set -e
    dnf update -y
    dnf install -y docker git
    systemctl enable --now docker
    usermod -aG docker ec2-user

    mkdir -p /etc/trajectory
    cat > /etc/trajectory/api.env <<'ENV'
    DATABASE_URL=postgresql+psycopg://trajectory:${var.db_password}@${aws_db_instance.postgres.address}:5432/trajectory
    OPENAI_API_KEY=${var.openai_api_key}
    OPENAI_MODEL=gpt-4o-mini
    API_KEY=${var.api_key}
    CORS_ORIGIN=*
    PROFILE_PATH=/etc/trajectory/profile.md
    ENV

    echo "# Profile not yet uploaded" > /etc/trajectory/profile.md
  EOF

  tags = { Name = "trajectory-api" }
}

resource "aws_eip" "api" {
  instance = aws_instance.api.id
  domain   = "vpc"
}

output "api_url"     { value = "http://${aws_eip.api.public_ip}:8000" }
output "ssh_command" { value = "ssh ec2-user@${aws_eip.api.public_ip}" }
output "db_address"  { value = aws_db_instance.postgres.address }
