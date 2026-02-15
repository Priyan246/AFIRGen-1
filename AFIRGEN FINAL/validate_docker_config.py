#!/usr/bin/env python3
"""
Docker Configuration Validation Script
Validates that docker-compose.yaml is correctly configured for AFIRGen deployment.
"""

import os
import sys
import yaml
from pathlib import Path

def validate_docker_compose():
    """Validate docker-compose.yaml configuration"""
    print("=" * 80)
    print("Docker Configuration Validation")
    print("=" * 80)
    
    # Check if docker-compose.yaml exists
    compose_file = Path("docker-compose.yaml")
    if not compose_file.exists():
        print("❌ docker-compose.yaml not found!")
        return False
    
    print("✅ docker-compose.yaml found")
    
    # Load and parse docker-compose.yaml
    try:
        with open(compose_file, 'r') as f:
            config = yaml.safe_load(f)
        print("✅ docker-compose.yaml is valid YAML")
    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML: {e}")
        return False
    
    # Validate services exist
    required_services = [
        'fir_pipeline', 'gguf_model_server', 'asr_ocr_model_server',
        'mysql', 'frontend', 'nginx', 'backup'
    ]
    
    services = config.get('services', {})
    print(f"\n📋 Checking {len(required_services)} required services...")
    
    all_services_ok = True
    for service in required_services:
        if service in services:
            print(f"  ✅ {service}")
        else:
            print(f"  ❌ {service} - MISSING")
            all_services_ok = False
    
    if not all_services_ok:
        return False
    
    # Validate build contexts match actual folders
    print("\n📁 Checking build contexts match actual folders...")
    build_contexts = {
        'fir_pipeline': './main backend',
        'gguf_model_server': './gguf model server',
        'asr_ocr_model_server': './asr ocr model server',
        'frontend': './frontend',
        'nginx': './nginx'
    }
    
    all_paths_ok = True
    for service, expected_path in build_contexts.items():
        actual_context = services[service].get('build', {}).get('context', '')
        folder_exists = Path(expected_path).exists()
        
        if actual_context == expected_path and folder_exists:
            print(f"  ✅ {service}: {expected_path}")
        elif actual_context != expected_path:
            print(f"  ❌ {service}: Expected '{expected_path}', got '{actual_context}'")
            all_paths_ok = False
        elif not folder_exists:
            print(f"  ❌ {service}: Folder '{expected_path}' does not exist")
            all_paths_ok = False
    
    if not all_paths_ok:
        return False
    
    # Validate health check start periods for model servers
    print("\n🏥 Checking health check configurations...")
    model_servers = ['gguf_model_server', 'asr_ocr_model_server']
    
    all_health_checks_ok = True
    for service in model_servers:
        healthcheck = services[service].get('healthcheck', {})
        start_period = healthcheck.get('start_period', '')
        
        if start_period == '180s':
            print(f"  ✅ {service}: start_period = 180s")
        else:
            print(f"  ❌ {service}: start_period = {start_period} (expected 180s)")
            all_health_checks_ok = False
    
    if not all_health_checks_ok:
        return False
    
    # Validate volume mounts
    print("\n💾 Checking volume mounts...")
    required_volumes = {
        'fir_pipeline': [
            './general retrieval db:/app/kb:ro',
            'chroma_data:/app/chroma_kb',
            'sessions_data:/app',
            'temp_files:/app/temp_files'
        ],
        'gguf_model_server': [
            './models:/app/models:ro'
        ],
        'asr_ocr_model_server': [
            './models:/app/models:ro',
            'temp_asr_ocr:/app/temp_asr_ocr'
        ],
        'mysql': [
            'mysql_data:/var/lib/mysql'
        ],
        'nginx': [
            './nginx/ssl:/etc/nginx/ssl:ro',
            './nginx/nginx.conf:/etc/nginx/nginx.conf:ro',
            'certbot_www:/var/www/certbot'
        ],
        'backup': [
            'backup_data:/app/backups',
            'sessions_data:/app:ro'
        ]
    }
    
    all_volumes_ok = True
    for service, expected_volumes in required_volumes.items():
        actual_volumes = services[service].get('volumes', [])
        
        for expected_vol in expected_volumes:
            if expected_vol in actual_volumes:
                print(f"  ✅ {service}: {expected_vol}")
            else:
                print(f"  ❌ {service}: Missing volume '{expected_vol}'")
                all_volumes_ok = False
    
    if not all_volumes_ok:
        return False
    
    # Validate named volumes are defined
    print("\n📦 Checking named volumes are defined...")
    required_named_volumes = [
        'mysql_data', 'chroma_data', 'sessions_data',
        'temp_files', 'temp_asr_ocr', 'backup_data', 'certbot_www'
    ]
    
    defined_volumes = config.get('volumes', {})
    all_named_volumes_ok = True
    
    for volume in required_named_volumes:
        if volume in defined_volumes:
            print(f"  ✅ {volume}")
        else:
            print(f"  ❌ {volume} - NOT DEFINED")
            all_named_volumes_ok = False
    
    if not all_named_volumes_ok:
        return False
    
    # Validate resource limits
    print("\n⚙️  Checking resource limits...")
    services_with_limits = [
        'fir_pipeline', 'gguf_model_server', 'asr_ocr_model_server',
        'mysql', 'frontend', 'nginx', 'backup'
    ]
    
    all_limits_ok = True
    for service in services_with_limits:
        deploy = services[service].get('deploy', {})
        resources = deploy.get('resources', {})
        limits = resources.get('limits', {})
        
        if 'cpus' in limits and 'memory' in limits:
            print(f"  ✅ {service}: CPU={limits['cpus']}, Memory={limits['memory']}")
        else:
            print(f"  ❌ {service}: Missing resource limits")
            all_limits_ok = False
    
    if not all_limits_ok:
        return False
    
    # Validate restart policies
    print("\n🔄 Checking restart policies...")
    all_restart_ok = True
    for service in required_services:
        restart = services[service].get('restart', '')
        if restart == 'always':
            print(f"  ✅ {service}: restart = always")
        else:
            print(f"  ❌ {service}: restart = {restart} (expected 'always')")
            all_restart_ok = False
    
    if not all_restart_ok:
        return False
    
    # Validate network configuration
    print("\n🌐 Checking network configuration...")
    networks = config.get('networks', {})
    if 'afirgen_network' in networks:
        print("  ✅ afirgen_network defined")
    else:
        print("  ❌ afirgen_network not defined")
        return False
    
    # Check all services are on the network
    all_on_network = True
    for service in required_services:
        service_networks = services[service].get('networks', [])
        if 'afirgen_network' in service_networks:
            print(f"  ✅ {service} on afirgen_network")
        else:
            print(f"  ❌ {service} not on afirgen_network")
            all_on_network = False
    
    if not all_on_network:
        return False
    
    print("\n" + "=" * 80)
    print("✅ All validation checks passed!")
    print("=" * 80)
    print("\nDocker configuration is ready for deployment.")
    print("\nTo start services:")
    print("  docker-compose up -d")
    print("\nTo check service status:")
    print("  docker-compose ps")
    print("\nTo view logs:")
    print("  docker-compose logs -f")
    
    return True

if __name__ == "__main__":
    try:
        success = validate_docker_compose()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
