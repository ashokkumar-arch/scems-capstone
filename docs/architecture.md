# SCEMS Architecture Decision Records

This document captures the key architectural decisions made during the SCEMS capstone project — what was chosen, what alternatives were considered, and why.

---

## ADR-001: Single CloudFormation Template vs Nested Stacks

**Decision:** Single monolithic CloudFormation template (1,011 lines).

**Alternatives considered:** Nested stacks (a root template referencing child templates for networking, IoT, compute, and CI/CD layers separately).

**Rationale:** For a capstone project with a single deployment environment, a monolithic template is simpler to manage, easier to review as a single artifact, and avoids the S3 staging requirement for nested stack templates. In a production multi-environment deployment (dev, staging, prod), nested stacks or AWS CDK would be preferable — separating the VPC/networking layer (which changes rarely) from the application layer (which changes with every release), and using CloudFormation StackSets for multi-account deployments.

---

## ADR-002: Amazon Timestream vs DynamoDB vs RDS for Time-Series Data

**Decision:** Amazon Timestream.

**Alternatives considered:** DynamoDB (with sort key on timestamp), RDS PostgreSQL with TimescaleDB extension.

**Rationale:** Timestream is purpose-built for time-series data. It provides automatic data tiering (memory store for hot data, magnetic store for cold), built-in SQL query support with time-series functions, and serverless scaling — no capacity planning required. DynamoDB with a timestamp sort key works but requires manual TTL management and lacks native time-series query functions. RDS with TimescaleDB is powerful but requires managing a database instance, patching, and backups manually. For IoT sensor data with a "last N readings" access pattern, Timestream is the correct choice.

---

## ADR-003: AWS IoT Python SDK vs MQTT Direct vs HTTP API

**Decision:** AWS IoT Python SDK with MQTT.

**Alternatives considered:** Direct MQTT library (paho-mqtt) with manual TLS configuration; HTTPS API calls to IoT Core's REST endpoint.

**Rationale:** The AWS IoT Python SDK handles the mTLS certificate loading, the connection lifecycle (reconnect on drop), QoS acknowledgement, and the MQTT protocol details automatically. paho-mqtt would require implementing these manually. The HTTP REST endpoint for IoT Core has higher per-message overhead and latency than MQTT, and does not support the persistent connection model that makes MQTT efficient for high-frequency sensor data. MQTT with QoS 1 is the industry standard for IoT telemetry.

---

## ADR-004: ECS Fargate vs EC2-backed ECS vs Lambda for the Dashboard

**Decision:** ECS Fargate.

**Alternatives considered:** EC2-backed ECS (managing the EC2 instances that run the containers); Lambda with Function URL (serverless HTTP endpoint).

**Rationale:** Fargate eliminates EC2 instance management (patching, scaling the underlying hosts, paying for idle capacity). Lambda with Function URL would work for a simple dashboard but has a 15-minute execution timeout and cold-start latency that would affect dashboard load time after periods of inactivity. Fargate provides always-on container execution without managing servers — the right middle ground for a long-running web application with modest traffic.

---

## ADR-005: Customer-Managed KMS Key vs AWS-Managed Key

**Decision:** Customer-managed KMS key (CMK).

**Alternatives considered:** AWS-managed key (the default Timestream encryption option, `aws/timestream`).

**Rationale:** An AWS-managed key is automatic and free, but the customer has no control over key policy, key rotation, or key deletion. A customer-managed key provides: explicit key policy (visible and auditable), automatic rotation on a configurable schedule, the ability to disable or delete the key (disabling access to all encrypted data — a compliance-relevant capability), and CloudTrail logging of every API call that uses the key. For data where encryption is a compliance requirement rather than a convenience, CMK is the correct choice.

---

## ADR-006: Flask vs FastAPI vs Static Site for the Dashboard

**Decision:** Flask.

**Alternatives considered:** FastAPI (async, higher performance); static site (JavaScript fetching Timestream directly from the browser).

**Rationale:** Flask is simple, well-understood, and the dashboard has a single route (`/`) with a single Timestream query. FastAPI's async capabilities and performance advantages are not needed at this scale. A static site fetching Timestream from the browser would require exposing Timestream credentials to the browser — a significant security problem. The server-side Flask approach keeps AWS credentials (via the ECS task IAM role) on the server where they belong, and the browser receives only rendered HTML.

---

## Enterprise Architecture Notes

The following decisions would change in a production enterprise deployment:

| Capstone decision | Production alternative | Reason |
|---|---|---|
| Public subnets for all compute | Private subnets + NAT Gateway + VPC Endpoints | No public IPs on compute resources |
| SSH on EC2 | SSM Session Manager | No open inbound ports, IAM-controlled access |
| HTTP ALB | HTTPS ALB + ACM + Route 53 | TLS termination, proper DNS name |
| Single AZ ECS task | Multi-AZ ECS service + Auto Scaling | High availability |
| No image scanning | Trivy in CodeBuild + ECR scan on push | Prevent vulnerable images reaching production |
| Auto-deploy on commit | Manual approval gate before deploy | Change control for government systems |

See the [Enterprise Extension portfolio guide](https://ashokkumar-arch.github.io/projects/scems/05-enterprise-extension.html) for complete details including the Cloud FinOps optimisation model.
