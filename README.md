# SCEMS — Smart City Environmental Monitoring System

**AWS IoT Capstone Project · Purdue University Global**

A cloud-native IoT environmental monitoring system deployed end-to-end on AWS using a single CloudFormation template. Simulated environmental sensors publish telemetry over MQTT with X.509/mTLS authentication, a serverless pipeline ingests and stores the data in an encrypted time-series database, and a containerised web dashboard serves the readings — with full CI/CD automation from code commit to production container deployment.

---

## Architecture

```
EC2 (IoT Sensor)
  │  MQTT over TLS (port 8883)
  ▼
AWS IoT Core ──── IoT Topic Rule ──── Lambda ──── Amazon Timestream (KMS-encrypted)
                                                          │
                                          ECS Fargate (Flask dashboard)
                                                          │
                                               ALB ──── Browser

CI/CD:
CodeCommit ──── CodePipeline ──── CodeBuild ──── ECR ──── ECS Fargate (deploy)
```

## AWS Services

| Layer | Service | Purpose |
|---|---|---|
| IoT | AWS IoT Core | Device connectivity, X.509/mTLS auth, MQTT broker, Topic Rules |
| Compute | Amazon EC2 (t2.micro) | Simulated IoT sensor — publishes readings every 5 seconds |
| Processing | AWS Lambda | Transforms IoT payload → Timestream multi-measure record |
| Storage | Amazon Timestream | Time-series database (KMS-encrypted, 24hr memory / 365d magnetic) |
| Encryption | AWS KMS | Customer-managed key for Timestream encryption at rest |
| Application | Amazon ECS Fargate | Flask dashboard container (0.25 vCPU, 0.5 GB) |
| Networking | Application Load Balancer | HTTP endpoint for the dashboard |
| Registry | Amazon ECR | Private container image registry |
| CI/CD | AWS CodePipeline | Pipeline orchestration: Source → Build → Deploy |
| CI/CD | AWS CodeBuild | Docker image build and ECR push |
| Source | AWS CodeCommit | Git repository for application source |
| Security | AWS Security Hub | Security posture monitoring and compliance |
| Backup | AWS Backup | Automated EC2/EBS backups with vault lock |
| Cost | AWS Budgets | Monthly cost alert at 80% threshold |

## IAM Design — Six Least-Privilege Roles

Six distinct IAM roles, one per service boundary, each scoped to specific resource ARNs:

| Role | Key Permissions | Scope |
|---|---|---|
| Lambda Execution | `timestream:WriteRecords`, `kms:Decrypt` | Specific table ARN, specific KMS key ARN |
| ECS Task Execution | ECR pull, CloudWatch Logs write | For ECS infrastructure use only |
| ECS Task | `timestream:Query`, `timestream:Select`, `kms:Decrypt` | Specific database/table ARNs, specific KMS key ARN |
| CodeBuild Service | ECR push, CloudWatch Logs | Scoped to specific log group prefix |
| CodePipeline Service | CodeCommit read, CodeBuild start, ECS deploy | AWS managed policy pattern (production would scope to specific ARNs) |
| EC2 Instance Profile | IoT credential provider, CloudWatch Logs | For sensor-to-IoT-Core credential exchange only |

## Repository Structure

```
scems-capstone/
├── README.md
├── infrastructure/
│   └── scems-ecs.yaml          # Complete CloudFormation template (1,011 lines)
├── application/
│   ├── app.py                  # Flask dashboard (final version)
│   ├── Dockerfile              # python:3.9-slim based container
│   ├── requirements.txt        # Flask, boto3, dependencies
│   ├── buildspec.yml           # CodeBuild pipeline specification
│   ├── imagedefinitions.json   # ECS deploy stage input
│   └── templates/
│       └── index.html          # Dashboard HTML template
└── docs/
    └── architecture.md         # Architecture decision records
```

## Deployment

Prerequisites: AWS CLI configured, EC2 key pair named `IoT_Device_VM` in us-east-1.

```bash
# Deploy the complete stack
aws cloudformation create-stack \
  --stack-name scems \
  --template-body file://infrastructure/scems-ecs.yaml \
  --parameters ParameterKey=KeyName,ParameterValue=IoT_Device_VM \
  --capabilities CAPABILITY_NAMED_IAM

# Monitor stack creation
aws cloudformation describe-stacks --stack-name scems \
  --query 'Stacks[0].StackStatus'

# Get the ALB endpoint once CREATE_COMPLETE
aws cloudformation describe-stacks --stack-name scems \
  --query 'Stacks[0].Outputs'
```

Stack creation takes approximately 8–12 minutes. Once complete, the CodeCommit repository URL is in the stack outputs — push the application source to trigger the first pipeline execution.

## Capstone Context and Honest Scope

This system was built as an academic capstone in a sandbox environment. Several production-grade considerations were intentionally simplified:

- All compute runs in **public subnets** (no private subnet / NAT Gateway separation)
- ALB serves **plain HTTP** (no Route 53, no ACM TLS, no WAF)
- EC2 security group allows **SSH from 0.0.0.0/0** (no SSM Session Manager)
- IoT device policy uses **Resource: "\*"** (not scoped to specific topic ARNs)
- CodePipeline uses **AWS managed policy** (not scoped to specific resource ARNs)

The portfolio's [Enterprise Extension guide](https://ashokkumar-arch.github.io/projects/scems/05-enterprise-extension.html) documents how each of these gaps would be closed in a production enterprise deployment, including the complete Cloud FinOps cost optimisation model.

## Portfolio

Full implementation walkthrough with teaching-guide depth:
**[ashokkumar-arch.github.io/projects/scems/01-overview-architecture.html](https://ashokkumar-arch.github.io/projects/scems/01-overview-architecture.html)**

---

*Purdue University Global · Bachelor of Science in Cloud Computing and Solutions · Graduated September 2024*
