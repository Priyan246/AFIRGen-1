#!/usr/bin/env python3
"""
AFIRGen Security Groups Validation Script

This script validates that AWS security groups follow the principle of least privilege.
It checks for common security misconfigurations and ensures compliance with best practices.

Usage:
    python test_security_groups.py [--profile PROFILE] [--region REGION]

Requirements:
    pip install boto3 colorama tabulate
"""

import argparse
import sys
from typing import List, Dict, Tuple
from dataclasses import dataclass

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    from colorama import Fore, Style, init
    from tabulate import tabulate
except ImportError as e:
    print(f"Error: Missing required package. Install with: pip install boto3 colorama tabulate")
    sys.exit(1)

# Initialize colorama
init(autoreset=True)

@dataclass
class SecurityIssue:
    """Represents a security issue found in security groups"""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    group_id: str
    group_name: str
    issue: str
    recommendation: str

class SecurityGroupValidator:
    """Validates AWS security groups for least privilege compliance"""
    
    def __init__(self, profile: str = None, region: str = 'us-east-1'):
        """Initialize AWS session"""
        try:
            if profile:
                session = boto3.Session(profile_name=profile, region_name=region)
            else:
                session = boto3.Session(region_name=region)
            
            self.ec2 = session.client('ec2')
            self.region = region
            self.issues: List[SecurityIssue] = []
        except NoCredentialsError:
            print(f"{Fore.RED}Error: AWS credentials not found. Configure with 'aws configure'")
            sys.exit(1)
        except Exception as e:
            print(f"{Fore.RED}Error initializing AWS session: {e}")
            sys.exit(1)
    
    def get_security_groups(self, project_name: str = 'afirgen') -> List[Dict]:
        """Fetch all security groups for the project"""
        try:
            response = self.ec2.describe_security_groups(
                Filters=[
                    {'Name': 'tag:Project', 'Values': [project_name]},
                ]
            )
            return response['SecurityGroups']
        except ClientError as e:
            print(f"{Fore.YELLOW}Warning: Could not fetch security groups: {e}")
            return []
    
    def check_unrestricted_ingress(self, sg: Dict) -> None:
        """Check for unrestricted ingress rules (0.0.0.0/0)"""
        group_id = sg['GroupId']
        group_name = sg['GroupName']
        
        # ALB is allowed to have 0.0.0.0/0 on ports 80 and 443
        is_alb = 'alb' in group_name.lower()
        
        for rule in sg.get('IpPermissions', []):
            for ip_range in rule.get('IpRanges', []):
                if ip_range.get('CidrIp') == '0.0.0.0/0':
                    from_port = rule.get('FromPort', 'all')
                    to_port = rule.get('ToPort', 'all')
                    protocol = rule.get('IpProtocol', 'all')
                    
                    # Allow ALB to have 80 and 443 open
                    if is_alb and from_port in [80, 443]:
                        continue
                    
                    severity = 'CRITICAL' if from_port in [22, 3389, 3306] else 'HIGH'
                    self.issues.append(SecurityIssue(
                        severity=severity,
                        group_id=group_id,
                        group_name=group_name,
                        issue=f"Unrestricted ingress on port {from_port}-{to_port} ({protocol}) from 0.0.0.0/0",
                        recommendation="Restrict to specific security groups or IP ranges"
                    ))
    
    def check_unrestricted_egress(self, sg: Dict) -> None:
        """Check for unrestricted egress rules"""
        group_id = sg['GroupId']
        group_name = sg['GroupName']
        
        # Services that need internet access for AWS services
        needs_internet = any(x in group_name.lower() for x in ['backend', 'gguf', 'asr', 'backup'])
        
        for rule in sg.get('IpPermissionsEgress', []):
            # Check for allow all egress (0.0.0.0/0 on all ports)
            if rule.get('IpProtocol') == '-1':
                for ip_range in rule.get('IpRanges', []):
                    if ip_range.get('CidrIp') == '0.0.0.0/0':
                        if not needs_internet:
                            self.issues.append(SecurityIssue(
                                severity='MEDIUM',
                                group_id=group_id,
                                group_name=group_name,
                                issue="Unrestricted egress to 0.0.0.0/0 on all ports",
                                recommendation="Restrict egress to specific security groups or use VPC endpoints"
                            ))
    
    def check_database_exposure(self, sg: Dict) -> None:
        """Check if database ports are exposed to internet"""
        group_id = sg['GroupId']
        group_name = sg['GroupName']
        
        database_ports = [3306, 5432, 1433, 27017, 6379]  # MySQL, PostgreSQL, MSSQL, MongoDB, Redis
        
        for rule in sg.get('IpPermissions', []):
            from_port = rule.get('FromPort')
            if from_port in database_ports:
                for ip_range in rule.get('IpRanges', []):
                    if ip_range.get('CidrIp') == '0.0.0.0/0':
                        self.issues.append(SecurityIssue(
                            severity='CRITICAL',
                            group_id=group_id,
                            group_name=group_name,
                            issue=f"Database port {from_port} exposed to internet",
                            recommendation="Restrict database access to application security groups only"
                        ))
    
    def check_ssh_rdp_exposure(self, sg: Dict) -> None:
        """Check if SSH or RDP ports are exposed"""
        group_id = sg['GroupId']
        group_name = sg['GroupName']
        
        admin_ports = {22: 'SSH', 3389: 'RDP'}
        
        for rule in sg.get('IpPermissions', []):
            from_port = rule.get('FromPort')
            if from_port in admin_ports:
                for ip_range in rule.get('IpRanges', []):
                    cidr = ip_range.get('CidrIp')
                    if cidr == '0.0.0.0/0':
                        self.issues.append(SecurityIssue(
                            severity='CRITICAL',
                            group_id=group_id,
                            group_name=group_name,
                            issue=f"{admin_ports[from_port]} port {from_port} exposed to internet",
                            recommendation="Use AWS Systems Manager Session Manager or restrict to VPN/bastion IP"
                        ))
                    elif not cidr.endswith('/32'):
                        self.issues.append(SecurityIssue(
                            severity='HIGH',
                            group_id=group_id,
                            group_name=group_name,
                            issue=f"{admin_ports[from_port]} port {from_port} exposed to {cidr}",
                            recommendation="Restrict to specific IP addresses (/32)"
                        ))
    
    def check_unused_security_groups(self, sg: Dict) -> None:
        """Check for security groups with no attached resources"""
        group_id = sg['GroupId']
        group_name = sg['GroupName']
        
        # Check if security group is attached to any network interfaces
        try:
            response = self.ec2.describe_network_interfaces(
                Filters=[{'Name': 'group-id', 'Values': [group_id]}]
            )
            if not response['NetworkInterfaces']:
                self.issues.append(SecurityIssue(
                    severity='LOW',
                    group_id=group_id,
                    group_name=group_name,
                    issue="Security group not attached to any resources",
                    recommendation="Remove unused security groups to reduce attack surface"
                ))
        except ClientError:
            pass  # Skip if we can't check
    
    def check_security_group_references(self, sg: Dict) -> None:
        """Check if rules use security group references instead of CIDR blocks"""
        group_id = sg['GroupId']
        group_name = sg['GroupName']
        
        # Skip ALB as it needs to accept from internet
        if 'alb' in group_name.lower():
            return
        
        for rule in sg.get('IpPermissions', []):
            # Check if rule uses CIDR blocks instead of security group references
            if rule.get('IpRanges') and not rule.get('UserIdGroupPairs'):
                from_port = rule.get('FromPort', 'all')
                for ip_range in rule.get('IpRanges', []):
                    cidr = ip_range.get('CidrIp')
                    # Internal services should use security group references
                    if cidr.startswith('10.') or cidr.startswith('172.') or cidr.startswith('192.168.'):
                        self.issues.append(SecurityIssue(
                            severity='LOW',
                            group_id=group_id,
                            group_name=group_name,
                            issue=f"Rule uses CIDR block {cidr} instead of security group reference",
                            recommendation="Use security group references for better maintainability"
                        ))
    
    def check_vpc_flow_logs(self) -> None:
        """Check if VPC Flow Logs are enabled"""
        try:
            # Get VPCs with afirgen tag
            vpcs = self.ec2.describe_vpcs(
                Filters=[{'Name': 'tag:Project', 'Values': ['afirgen']}]
            )
            
            for vpc in vpcs['Vpcs']:
                vpc_id = vpc['VpcId']
                
                # Check if flow logs are enabled
                flow_logs = self.ec2.describe_flow_logs(
                    Filters=[{'Name': 'resource-id', 'Values': [vpc_id]}]
                )
                
                if not flow_logs['FlowLogs']:
                    self.issues.append(SecurityIssue(
                        severity='MEDIUM',
                        group_id=vpc_id,
                        group_name='VPC',
                        issue="VPC Flow Logs not enabled",
                        recommendation="Enable VPC Flow Logs for security monitoring and troubleshooting"
                    ))
        except ClientError:
            pass  # Skip if we can't check
    
    def validate_all(self, project_name: str = 'afirgen') -> Tuple[int, int, int, int]:
        """Run all validation checks"""
        print(f"{Fore.CYAN}Fetching security groups for project: {project_name}...")
        security_groups = self.get_security_groups(project_name)
        
        if not security_groups:
            print(f"{Fore.YELLOW}No security groups found with tag Project={project_name}")
            print(f"{Fore.YELLOW}Make sure security groups are tagged correctly or deployed")
            return 0, 0, 0, 0
        
        print(f"{Fore.GREEN}Found {len(security_groups)} security groups")
        print(f"{Fore.CYAN}Running validation checks...\n")
        
        for sg in security_groups:
            self.check_unrestricted_ingress(sg)
            self.check_unrestricted_egress(sg)
            self.check_database_exposure(sg)
            self.check_ssh_rdp_exposure(sg)
            self.check_unused_security_groups(sg)
            self.check_security_group_references(sg)
        
        # Check VPC-level settings
        self.check_vpc_flow_logs()
        
        # Count issues by severity
        critical = sum(1 for i in self.issues if i.severity == 'CRITICAL')
        high = sum(1 for i in self.issues if i.severity == 'HIGH')
        medium = sum(1 for i in self.issues if i.severity == 'MEDIUM')
        low = sum(1 for i in self.issues if i.severity == 'LOW')
        
        return critical, high, medium, low
    
    def print_results(self) -> None:
        """Print validation results"""
        if not self.issues:
            print(f"{Fore.GREEN}✓ All security group checks passed!")
            print(f"{Fore.GREEN}✓ Security groups follow least privilege principles")
            return
        
        # Group issues by severity
        critical_issues = [i for i in self.issues if i.severity == 'CRITICAL']
        high_issues = [i for i in self.issues if i.severity == 'HIGH']
        medium_issues = [i for i in self.issues if i.severity == 'MEDIUM']
        low_issues = [i for i in self.issues if i.severity == 'LOW']
        
        # Print critical issues
        if critical_issues:
            print(f"\n{Fore.RED}{'='*80}")
            print(f"{Fore.RED}CRITICAL ISSUES ({len(critical_issues)})")
            print(f"{Fore.RED}{'='*80}")
            for issue in critical_issues:
                print(f"\n{Fore.RED}[CRITICAL] {issue.group_name} ({issue.group_id})")
                print(f"{Fore.WHITE}Issue: {issue.issue}")
                print(f"{Fore.YELLOW}Recommendation: {issue.recommendation}")
        
        # Print high issues
        if high_issues:
            print(f"\n{Fore.YELLOW}{'='*80}")
            print(f"{Fore.YELLOW}HIGH PRIORITY ISSUES ({len(high_issues)})")
            print(f"{Fore.YELLOW}{'='*80}")
            for issue in high_issues:
                print(f"\n{Fore.YELLOW}[HIGH] {issue.group_name} ({issue.group_id})")
                print(f"{Fore.WHITE}Issue: {issue.issue}")
                print(f"{Fore.CYAN}Recommendation: {issue.recommendation}")
        
        # Print medium issues
        if medium_issues:
            print(f"\n{Fore.CYAN}{'='*80}")
            print(f"{Fore.CYAN}MEDIUM PRIORITY ISSUES ({len(medium_issues)})")
            print(f"{Fore.CYAN}{'='*80}")
            for issue in medium_issues:
                print(f"\n{Fore.CYAN}[MEDIUM] {issue.group_name} ({issue.group_id})")
                print(f"{Fore.WHITE}Issue: {issue.issue}")
                print(f"{Fore.CYAN}Recommendation: {issue.recommendation}")
        
        # Print low issues
        if low_issues:
            print(f"\n{Fore.WHITE}{'='*80}")
            print(f"{Fore.WHITE}LOW PRIORITY ISSUES ({len(low_issues)})")
            print(f"{Fore.WHITE}{'='*80}")
            for issue in low_issues:
                print(f"\n{Fore.WHITE}[LOW] {issue.group_name} ({issue.group_id})")
                print(f"{Fore.WHITE}Issue: {issue.issue}")
                print(f"{Fore.WHITE}Recommendation: {issue.recommendation}")
    
    def print_summary(self, critical: int, high: int, medium: int, low: int) -> None:
        """Print summary of findings"""
        print(f"\n{'='*80}")
        print(f"{Fore.CYAN}VALIDATION SUMMARY")
        print(f"{'='*80}")
        
        summary_data = [
            [f"{Fore.RED}CRITICAL", critical],
            [f"{Fore.YELLOW}HIGH", high],
            [f"{Fore.CYAN}MEDIUM", medium],
            [f"{Fore.WHITE}LOW", low],
            [f"{Fore.GREEN}TOTAL", critical + high + medium + low]
        ]
        
        print(tabulate(summary_data, headers=['Severity', 'Count'], tablefmt='grid'))
        
        if critical > 0:
            print(f"\n{Fore.RED}⚠ CRITICAL issues found! Address immediately.")
            return 1
        elif high > 0:
            print(f"\n{Fore.YELLOW}⚠ HIGH priority issues found. Address soon.")
            return 1
        elif medium > 0 or low > 0:
            print(f"\n{Fore.CYAN}ℹ Some issues found. Review and address as needed.")
            return 0
        else:
            print(f"\n{Fore.GREEN}✓ No issues found. Security groups are properly configured!")
            return 0

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Validate AFIRGen AWS security groups for least privilege compliance'
    )
    parser.add_argument(
        '--profile',
        help='AWS profile name',
        default=None
    )
    parser.add_argument(
        '--region',
        help='AWS region',
        default='us-east-1'
    )
    parser.add_argument(
        '--project',
        help='Project name tag',
        default='afirgen'
    )
    
    args = parser.parse_args()
    
    print(f"{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}AFIRGen Security Groups Validation")
    print(f"{Fore.CYAN}{'='*80}")
    print(f"{Fore.WHITE}Region: {args.region}")
    print(f"{Fore.WHITE}Project: {args.project}")
    if args.profile:
        print(f"{Fore.WHITE}Profile: {args.profile}")
    print()
    
    validator = SecurityGroupValidator(profile=args.profile, region=args.region)
    critical, high, medium, low = validator.validate_all(project_name=args.project)
    
    validator.print_results()
    exit_code = validator.print_summary(critical, high, medium, low)
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
