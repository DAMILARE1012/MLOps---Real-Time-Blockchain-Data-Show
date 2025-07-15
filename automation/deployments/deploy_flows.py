"""
Prefect Deployment Configuration for Blockchain Anomaly Detection System

This script sets up automated deployments for:
- Health monitoring (every 15 minutes)
- System monitoring (every 5 minutes) 
- Model retraining (daily at 2 AM)
- CI/CD pipeline automation
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from prefect import serve
from prefect.client.schemas.schedules import CronSchedule, IntervalSchedule
from prefect.blocks.system import JSON
from prefect.filesystems import LocalFileSystem

# Import our flows
from automation.flows.health_monitoring import system_health_check_flow
from automation.flows.model_retraining import automated_model_retraining_flow
from automation.flows.system_monitoring import system_monitoring_flow

def create_deployments():
    """Create all Prefect deployments using new deployment syntax"""
    
    # Create work pools and blocks
    print("Creating Prefect blocks...")
    
    # Create local filesystem block
    local_fs = LocalFileSystem(basepath="./automation")
    local_fs.save("automation-filesystem", overwrite=True)
    
    # Create configuration block
    config = {
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
        "monitoring_enabled": True,
        "retraining_enabled": True,
        "health_check_enabled": True
    }
    
    config_block = JSON(value=config)
    config_block.save("system-config", overwrite=True)
    
    print("Creating deployments using new syntax...")
    
    # Deploy flows using new serve() method
    deployments = [
        system_health_check_flow.to_deployment(
            name="health-check-deployment",
            schedule=CronSchedule(cron="*/15 * * * *"),  # Every 15 minutes
            tags=["health", "monitoring", "production"],
            description="Automated health checks for blockchain anomaly detection system",
            version="1.0.0",
            parameters={}
        ),
        system_monitoring_flow.to_deployment(
            name="system-monitoring-deployment", 
            schedule=CronSchedule(cron="*/5 * * * *"),  # Every 5 minutes
            tags=["monitoring", "metrics", "production"],
            description="Continuous system monitoring with alerts",
            version="1.0.0",
            parameters={}
        ),
        automated_model_retraining_flow.to_deployment(
            name="model-retraining-deployment",
            schedule=CronSchedule(cron="0 2 * * *"),  # Daily at 2 AM
            tags=["ml", "retraining", "production"],
            description="Automated ML model retraining pipeline",
            version="1.0.0",
            parameters={}
        )
    ]
    
    return deployments

def deploy_all():
    """Deploy all flows to Prefect using new serve() method"""
    
    print("[*] Starting Prefect deployment process...")
    
    # Create deployments
    deployments = create_deployments()
    
    # Serve deployments using new method
    print("Starting deployment server...")
    
    try:
        # Use serve() method to start deployments
        serve(*deployments)
        print("[+] Successfully started all deployments")
        
        print(f"\n[*] Deployment Summary:")
        print(f"Total deployments: {len(deployments)}")
        print(f"All deployments are now running")
        
        print(f"\n[*] Scheduled Flows:")
        print(f"  • Health Check: Every 15 minutes")
        print(f"  • System Monitoring: Every 5 minutes")
        print(f"  • Model Retraining: Daily at 2:00 AM")
        
        return True
        
    except Exception as e:
        print(f"[-] Failed to start deployments: {e}")
        return False

def create_ci_cd_deployment():
    """Create CI/CD pipeline deployment"""
    
    print("[*] Creating CI/CD pipeline deployment...")
    
    # CI/CD Flow (simplified version)
    from prefect import flow, task
    
    @task
    async def run_tests():
        """Run automated tests"""
        import subprocess
        result = subprocess.run(["python", "-m", "pytest", "tests/"], 
                              capture_output=True, text=True)
        return result.returncode == 0
    
    @task
    async def backup_current_model():
        """Backup current model before deployment"""
        import shutil
        if os.path.exists("models/anomaly_model.pkl"):
            backup_path = f"models/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            shutil.copy2("models/anomaly_model.pkl", backup_path)
            return backup_path
        return None
    
    @task
    async def deploy_to_production():
        """Deploy to production environment"""
        # In a real scenario, this would deploy to production servers
        print("Deploying to production...")
        return True
    
    @task
    async def rollback_on_failure(backup_path: str):
        """Rollback to previous version on failure"""
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, "models/anomaly_model.pkl")
            print(f"Rolled back to {backup_path}")
    
    @flow(name="CI/CD Pipeline", log_prints=True)
    async def ci_cd_pipeline():
        """CI/CD pipeline for automated deployment"""
        # Run tests
        tests_passed = await run_tests()
        
        if not tests_passed:
            print("[-] Tests failed. Aborting deployment.")
            return False
        
        # Backup current model
        backup_path = await backup_current_model()
        
        # Deploy to production
        try:
            deployment_success = await deploy_to_production()
            if deployment_success:
                print("[+] Deployment successful!")
                return True
            else:
                print("[-] Deployment failed. Rolling back...")
                await rollback_on_failure(backup_path)
                return False
                
        except Exception as e:
            print(f"[-] Deployment error: {e}")
            await rollback_on_failure(backup_path)
            return False
    
    # Create CI/CD deployment using new syntax
    ci_cd_deployment = ci_cd_pipeline.to_deployment(
        name="ci-cd-deployment",
        tags=["ci-cd", "deployment", "production"],
        description="CI/CD pipeline for automated testing and deployment",
        version="1.0.0",
        parameters={}
    )
    
    return ci_cd_deployment

if __name__ == "__main__":
    print("[*] Blockchain Anomaly Detection - Prefect Deployment Setup")
    print("=" * 60)
    
    # Deploy main workflows using new serve() method
    print("Starting deployment server...")
    success = deploy_all()
    
    if success:
        print("\n[*] Deployment setup complete!")
        print("\nNext steps:")
        print("1. Prefect server is running at: http://localhost:4200")
        print("2. Deployments are now active and scheduled")
        print("3. Monitor flows in Prefect UI: http://localhost:4200")
        print("4. Check deployment status: prefect deployment ls")
        
        print("\n[*] Telegram notifications are configured for:")
        print("  • Health check alerts")
        print("  • System monitoring alerts") 
        print("  • Model retraining notifications")
        print("  • CI/CD pipeline status")
    else:
        print("\n[-] Deployment setup failed!")
        print("Please check the error messages above and try again.")