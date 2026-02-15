# AFIRGen Security Groups - Validation Checklist

## Pre-Deployment Validation

### Infrastructure Review
- [ ] VPC CIDR block does not overlap with other VPCs
- [ ] Sufficient IP addresses in subnets (at least /24)
- [ ] Public subnets in different availability zones
- [ ] Private subnets in different availability zones
- [ ] NAT Gateways deployed in each AZ for high availability
- [ ] Internet Gateway attached to VPC
- [ ] Route tables properly configured

### Security Group Configuration
- [ ] All security groups have descriptive names
- [ ] All security groups have proper tags (Project, Environment, Component)
- [ ] No security groups have default "allow all" rules
- [ ] Security group rules use references instead of CIDR blocks (where applicable)
- [ ] No unused security groups exist

### ALB Security Group
- [ ] Allows HTTPS (443) from 0.0.0.0/0
- [ ] Allows HTTP (80) from 0.0.0.0/0 for redirect
- [ ] Egress only to Nginx security group
- [ ] No other ports exposed

### Nginx Security Group
- [ ] Allows traffic only from ALB security group
- [ ] Egress to main backend (port 8000)
- [ ] Egress to frontend (port 80)
- [ ] No direct internet access

### Main Backend Security Group
- [ ] Allows traffic only from Nginx security group (port 8000)
- [ ] Egress to GGUF model server (port 8001)
- [ ] Egress to ASR/OCR server (port 8002)
- [ ] Egress to RDS (port 3306)
- [ ] Egress to EFS (port 2049)
- [ ] Egress to VPC endpoints (port 443)
- [ ] No direct internet access except via VPC endpoints

### GGUF Model Server Security Group
- [ ] Allows traffic only from main backend (port 8001)
- [ ] Egress to S3 via VPC endpoint (port 443)
- [ ] No other egress rules

### ASR/OCR Server Security Group
- [ ] Allows traffic only from main backend (port 8002)
- [ ] Egress to S3 via VPC endpoint (port 443)
- [ ] No other egress rules

### Frontend Security Group
- [ ] Allows traffic only from Nginx security group (port 80)
- [ ] No egress rules (static content only)

### RDS Security Group
- [ ] Allows MySQL (3306) only from main backend security group
- [ ] Allows MySQL (3306) only from backup security group
- [ ] No public access (0.0.0.0/0)
- [ ] No egress rules

### EFS Security Group
- [ ] Allows NFS (2049) only from main backend security group
- [ ] No public access
- [ ] No egress rules

### Backup Service Security Group
- [ ] No ingress rules
- [ ] Egress to RDS (port 3306)
- [ ] Egress to S3 via VPC endpoint (port 443)
- [ ] Egress to Secrets Manager via VPC endpoint (port 443)

### VPC Endpoints Security Group
- [ ] Allows HTTPS (443) from main backend
- [ ] Allows HTTPS (443) from GGUF model server
- [ ] Allows HTTPS (443) from ASR/OCR server
- [ ] Allows HTTPS (443) from backup service
- [ ] No egress rules

## VPC Endpoints Validation

### Gateway Endpoints
- [ ] S3 gateway endpoint created
- [ ] S3 endpoint attached to all route tables
- [ ] S3 endpoint policy restricts to project buckets

### Interface Endpoints
- [ ] Secrets Manager endpoint created
- [ ] CloudWatch Logs endpoint created
- [ ] CloudWatch Monitoring endpoint created
- [ ] ECR API endpoint created
- [ ] ECR DKR endpoint created
- [ ] ECS endpoint created
- [ ] ECS Telemetry endpoint created
- [ ] All interface endpoints in private subnets
- [ ] All interface endpoints use VPC endpoints security group
- [ ] Private DNS enabled for all interface endpoints

## Monitoring and Logging

### VPC Flow Logs
- [ ] VPC Flow Logs enabled for VPC
- [ ] Flow logs capture ALL traffic (not just ACCEPT or REJECT)
- [ ] Flow logs sent to CloudWatch Logs
- [ ] Log retention set to 30 days minimum
- [ ] IAM role for Flow Logs has proper permissions

### CloudWatch Alarms
- [ ] Alarm for high number of rejected connections
- [ ] Alarm for unusual traffic patterns
- [ ] SNS topic configured for alerts
- [ ] Email subscription to SNS topic confirmed

### AWS Security Hub
- [ ] Security Hub enabled in region
- [ ] CIS AWS Foundations Benchmark enabled
- [ ] Security Hub findings reviewed

## Post-Deployment Validation

### Automated Validation
- [ ] Run `python test_security_groups.py` - all checks pass
- [ ] No CRITICAL issues found
- [ ] No HIGH priority issues found
- [ ] MEDIUM and LOW issues documented and accepted

### Connectivity Testing

#### External Access
- [ ] Can access ALB via HTTPS from internet
- [ ] HTTP redirects to HTTPS
- [ ] SSL certificate valid
- [ ] Frontend loads correctly

#### Internal Service Communication
- [ ] Nginx can reach main backend (port 8000)
- [ ] Nginx can reach frontend (port 80)
- [ ] Main backend can reach GGUF server (port 8001)
- [ ] Main backend can reach ASR/OCR server (port 8002)
- [ ] Main backend can reach RDS (port 3306)
- [ ] Main backend can reach EFS (port 2049)
- [ ] Backup service can reach RDS (port 3306)

#### AWS Service Access
- [ ] Main backend can access Secrets Manager
- [ ] Main backend can write to CloudWatch Logs
- [ ] GGUF server can download models from S3
- [ ] ASR/OCR server can download models from S3
- [ ] Backup service can upload to S3

#### Negative Testing (Should Fail)
- [ ] Cannot SSH to any instance from internet
- [ ] Cannot access RDS directly from internet
- [ ] Cannot access internal services from internet
- [ ] Model servers cannot communicate with each other
- [ ] Frontend cannot make outbound connections

### Performance Testing
- [ ] VPC endpoint latency acceptable (<10ms)
- [ ] No significant performance degradation vs NAT Gateway
- [ ] S3 downloads via VPC endpoint working
- [ ] Secrets Manager calls via VPC endpoint working

## Security Audit

### CIS AWS Foundations Benchmark
- [ ] 4.1: No security groups allow 0.0.0.0/0 ingress to port 22
- [ ] 4.2: No security groups allow 0.0.0.0/0 ingress to port 3389
- [ ] 4.3: Default security group restricts all traffic
- [ ] 4.4: VPC Flow Logs enabled
- [ ] 4.5: Routing tables for VPC peering are least access

### OWASP Top 10
- [ ] A01: Broken Access Control - Security groups enforce least privilege
- [ ] A02: Cryptographic Failures - All traffic encrypted (TLS)
- [ ] A03: Injection - Database not publicly accessible
- [ ] A05: Security Misconfiguration - No default credentials, proper SG rules
- [ ] A07: Identification and Authentication Failures - API authentication required

### Compliance Requirements
- [ ] PCI DSS Requirement 1: Network security controls implemented
- [ ] HIPAA 164.312(e)(1): Transmission security via TLS
- [ ] SOC 2 CC6.6: Logical access controls via security groups

## Cost Optimization

### VPC Endpoints vs NAT Gateway
- [ ] VPC endpoints deployed for frequently used services
- [ ] S3 gateway endpoint used (free)
- [ ] Interface endpoints cost justified by data transfer savings
- [ ] NAT Gateway data transfer monitored

### Resource Optimization
- [ ] No unused security groups
- [ ] No unused VPC endpoints
- [ ] VPC Flow Logs retention optimized
- [ ] CloudWatch Logs retention optimized

## Documentation

- [ ] Security group architecture diagram created
- [ ] All security group rules documented
- [ ] Runbook for common issues created
- [ ] Change management process documented
- [ ] Incident response plan includes security group changes

## Maintenance

### Regular Reviews
- [ ] Weekly: Run validation script
- [ ] Weekly: Review VPC Flow Logs for anomalies
- [ ] Monthly: Review security group rules for changes
- [ ] Monthly: Review unused security groups
- [ ] Quarterly: Full security audit
- [ ] Quarterly: Review and update documentation

### Change Management
- [ ] All security group changes via Terraform
- [ ] Pull request required for changes
- [ ] Changes tested in staging first
- [ ] Changes documented in changelog
- [ ] Rollback plan documented

## Incident Response

### Security Incident Procedures
- [ ] Procedure to lockdown all access documented
- [ ] Procedure to allow specific IP only documented
- [ ] Procedure to restore from backup documented
- [ ] Contact list for security incidents maintained
- [ ] Post-incident review process defined

## Sign-Off

### Technical Review
- [ ] DevOps Engineer reviewed and approved
- [ ] Security Engineer reviewed and approved
- [ ] Network Engineer reviewed and approved

### Management Approval
- [ ] Technical Lead approved
- [ ] Security Manager approved
- [ ] Project Manager approved

### Deployment Authorization
- [ ] Staging deployment successful
- [ ] Production deployment authorized
- [ ] Rollback plan confirmed
- [ ] Monitoring confirmed operational

---

**Validation Date**: _______________
**Validated By**: _______________
**Approved By**: _______________
**Deployment Date**: _______________

## Notes

Use this space to document any deviations from the checklist or additional validation steps taken:

```
[Add notes here]
```

## Validation Results

### Automated Tests
```bash
# Run validation script
python test_security_groups.py --region us-east-1 --project afirgen

# Results:
# CRITICAL: 0
# HIGH: 0
# MEDIUM: 0
# LOW: 0
# Status: PASS
```

### Manual Tests
```
[Document manual test results here]
```

### Issues Found
```
[Document any issues found and their resolution]
```

---

**Status**: [ ] PASS [ ] FAIL [ ] CONDITIONAL PASS
**Next Review Date**: _______________
