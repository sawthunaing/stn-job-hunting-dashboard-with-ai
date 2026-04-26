###############################################################################
# Trajectory infrastructure (all-Docker, single-EC2 edition).
#
# Provisions:
#   - 1x t4g.small EC2 (ARM, ~$12/mo) running:
#       * Postgres in Docker
#       * FastAPI backend in Docker
#       * Next.js frontend in Docker (production mode)
#   - Security group: SSH from your IP, ports 3000 (frontend) and 8000 (API)
#     open to the world
#   - An Elastic IP so the address doesn't change on reboot
#
# After apply, SSH in and follow the deploy steps to:
#   1. git clone your repo
#   2. drop in a production config.json
#   3. docker compose up -d --build
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

variable "region" {
  default = "eu-west-2"
}

variable "my_ip" {
  description = "Your IP in CIDR form for SSH access, e.g. 1.2.3.4/32"
}

variable "ssh_public_key" {
  description = "Contents of your ~/.ssh/id_ed25519.pub"
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_security_group" "app" {
  name        = "trajectory-app"
  description = "App stack: SSH from my IP, frontend + API public"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH (locked to your IP)"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description = "Frontend (Next.js)"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "API (FastAPI)"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_key_pair" "main" {
  key_name   = "trajectory-key"
  public_key = var.ssh_public_key
}

data "aws_ami" "al2023_arm" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-arm64"]
  }
  filter {
    name   = "architecture"
    values = ["arm64"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "app" {
  ami                    = data.aws_ami.al2023_arm.id
  instance_type          = "t4g.small"
  key_name               = aws_key_pair.main.key_name
  vpc_security_group_ids = [aws_security_group.app.id]
  subnet_id              = data.aws_subnets.default.ids[0]

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  user_data = <<-EOF
    #!/bin/bash
    set -e
    dnf update -y
    dnf install -y docker git
    systemctl enable --now docker
    usermod -aG docker ec2-user

    # Install docker compose v2 plugin for ARM64
    DOCKER_CONFIG=/usr/local/lib/docker
    mkdir -p $DOCKER_CONFIG/cli-plugins
    curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-aarch64 \
      -o $DOCKER_CONFIG/cli-plugins/docker-compose
    chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
  EOF

  tags = { Name = "trajectory-app" }
}

resource "aws_eip" "app" {
  instance = aws_instance.app.id
  domain   = "vpc"
}

output "frontend_url" {
  value = "http://${aws_eip.app.public_ip}:3000"
}

output "api_url" {
  value = "http://${aws_eip.app.public_ip}:8000"
}

output "ssh_command" {
  value = "ssh ec2-user@${aws_eip.app.public_ip}"
}

output "public_ip" {
  value = aws_eip.app.public_ip
}
