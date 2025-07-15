"""
Automation Runner for Blockchain Anomaly Detection System

This script provides a unified interface to manage all automation workflows:
- Start/stop automation services
- Monitor workflow status
- Configure schedules
- Manual workflow triggers
"""

import os
import sys
import asyncio
import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from automation.flows.health_monitoring import system_health_check_flow
from automation.flows.model_retraining import automated_model_retraining_flow
from automation.flows.system_monitoring import system_monitoring_flow

class AutomationManager:
    """Manages all automation workflows for the blockchain anomaly detection system"""
    
    def __init__(self):
        self.flows = {
            'health_check': system_health_check_flow,
            'model_retraining': automated_model_retraining_flow,
            'system_monitoring': system_monitoring_flow
        }
        
        self.config_file = "automation/config/automation_config.json"
        self.load_config()
    
    def load_config(self):
        """Load automation configuration"""
        default_config = {
            "enabled": True,
            "schedules": {
                "health_check": "*/15 * * * *",  # Every 15 minutes
                "system_monitoring": "*/5 * * * *",  # Every 5 minutes
                "model_retraining": "0 2 * * *"  # Daily at 2 AM
            },
            "notifications": {
                "telegram_enabled": True,
                "email_enabled": False
            },
            "thresholds": {
                "cpu_alert": 80,
                "memory_alert": 85,
                "disk_alert": 90,
                "error_rate_alert": 0.1
            }
        }
        
        try:
            os.makedirs("automation/config", exist_ok=True)
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = default_config
                self.save_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = default_config
    
    def save_config(self):
        """Save automation configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    async def run_health_check(self):
        """Run health check manually"""
        print("🔍 Running health check...")
        try:
            result = await self.flows['health_check']()
            print(f"✅ Health check completed: {result['system_status']}")
            return result
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return None
    
    async def run_system_monitoring(self):
        """Run system monitoring manually"""
        print("📊 Running system monitoring...")
        try:
            result = await self.flows['system_monitoring']()
            print(f"✅ System monitoring completed")
            return result
        except Exception as e:
            print(f"❌ System monitoring failed: {e}")
            return None
    
    async def run_model_retraining(self):
        """Run model retraining manually"""
        print("🤖 Running model retraining...")
        try:
            result = await self.flows['model_retraining']()
            print(f"✅ Model retraining completed")
            return result
        except Exception as e:
            print(f"❌ Model retraining failed: {e}")
            return None
    
    def start_prefect_server(self):
        """Start Prefect server"""
        print("🚀 Starting Prefect server...")
        try:
            # Start server in background
            process = subprocess.Popen(
                ["prefect", "server", "start"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("✅ Prefect server started (check http://localhost:4200)")
            return process
        except Exception as e:
            print(f"❌ Failed to start Prefect server: {e}")
            return None
    
    def start_prefect_agent(self, work_pool: str = "default-agent-pool"):
        """Start Prefect agent"""
        print(f"🤖 Starting Prefect agent for work pool: {work_pool}")
        try:
            process = subprocess.Popen(
                ["prefect", "agent", "start", "--work-pool", work_pool],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("✅ Prefect agent started")
            return process
        except Exception as e:
            print(f"❌ Failed to start Prefect agent: {e}")
            return None
    
    def deploy_workflows(self):
        """Deploy all workflows to Prefect"""
        print("📦 Deploying workflows...")
        try:
            from automation.deployments.deploy_flows import deploy_all
            deployment_ids = deploy_all()
            print(f"✅ Deployed {len(deployment_ids)} workflows")
            return deployment_ids
        except Exception as e:
            print(f"❌ Failed to deploy workflows: {e}")
            return []
    
    def check_prefect_status(self):
        """Check Prefect server and agent status"""
        print("🔍 Checking Prefect status...")
        try:
            # Check server status
            result = subprocess.run(
                ["prefect", "server", "database", "reset", "--help"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Prefect server is accessible")
            else:
                print("❌ Prefect server is not accessible")
            
            # Check deployments
            result = subprocess.run(
                ["prefect", "deployment", "ls"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Deployments are accessible")
                print(result.stdout)
            else:
                print("❌ Could not list deployments")
            
        except Exception as e:
            print(f"❌ Error checking Prefect status: {e}")
    
    def show_status(self):
        """Show current automation status"""
        print("\n📊 Automation Status Dashboard")
        print("=" * 50)
        
        # Configuration status
        print(f"🔧 Configuration:")
        print(f"  • Automation enabled: {self.config.get('enabled', False)}")
        print(f"  • Telegram notifications: {self.config.get('notifications', {}).get('telegram_enabled', False)}")
        
        # File status
        print(f"\n📁 File Status:")
        files_to_check = [
            "models/anomaly_model.pkl",
            "anomaly_events.csv",
            "whale_events.csv",
            "data_pipeline.log"
        ]
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                print(f"  ✅ {file_path} ({size:,} bytes, modified: {modified.strftime('%Y-%m-%d %H:%M:%S')})")
            else:
                print(f"  ❌ {file_path} (missing)")
        
        # Health status
        print(f"\n🏥 System Health:")
        
        # Check if data pipeline is running
        if os.path.exists("data_pipeline.log"):
            log_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime("data_pipeline.log"))
            if log_age.total_seconds() < 300:  # 5 minutes
                print(f"  ✅ Data pipeline: Active (last update: {log_age.total_seconds():.0f}s ago)")
            else:
                print(f"  ⚠️ Data pipeline: Stale (last update: {log_age.total_seconds()/60:.1f}m ago)")
        else:
            print(f"  ❌ Data pipeline: Not running")
        
        # Check recent data
        try:
            import pandas as pd
            if os.path.exists("anomaly_events.csv"):
                df = pd.read_csv("anomaly_events.csv")
                print(f"  📊 Anomaly events: {len(df)} total")
            
            if os.path.exists("whale_events.csv"):
                df = pd.read_csv("whale_events.csv")
                print(f"  🐋 Whale events: {len(df)} total")
        except Exception as e:
            print(f"  ❌ Error reading data files: {e}")
    
    def interactive_menu(self):
        """Interactive menu for automation management"""
        while True:
            print("\n🤖 Blockchain Anomaly Detection - Automation Manager")
            print("=" * 60)
            print("1. Show Status")
            print("2. Run Health Check")
            print("3. Run System Monitoring")
            print("4. Run Model Retraining")
            print("5. Deploy Workflows")
            print("6. Start Prefect Server")
            print("7. Start Prefect Agent")
            print("8. Check Prefect Status")
            print("9. Configure Settings")
            print("0. Exit")
            
            try:
                choice = input("\nEnter your choice (0-9): ").strip()
                
                if choice == '0':
                    print("👋 Goodbye!")
                    break
                elif choice == '1':
                    self.show_status()
                elif choice == '2':
                    asyncio.run(self.run_health_check())
                elif choice == '3':
                    asyncio.run(self.run_system_monitoring())
                elif choice == '4':
                    asyncio.run(self.run_model_retraining())
                elif choice == '5':
                    self.deploy_workflows()
                elif choice == '6':
                    self.start_prefect_server()
                elif choice == '7':
                    self.start_prefect_agent()
                elif choice == '8':
                    self.check_prefect_status()
                elif choice == '9':
                    self.configure_settings()
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def configure_settings(self):
        """Configure automation settings"""
        print("\n⚙️ Configuration Settings")
        print("=" * 30)
        
        # Enable/disable automation
        current = self.config.get('enabled', True)
        response = input(f"Enable automation? (current: {current}) [y/n]: ").strip().lower()
        if response in ['y', 'yes']:
            self.config['enabled'] = True
        elif response in ['n', 'no']:
            self.config['enabled'] = False
        
        # Configure thresholds
        print("\nAlert Thresholds:")
        thresholds = self.config.get('thresholds', {})
        
        try:
            cpu_threshold = input(f"CPU alert threshold % (current: {thresholds.get('cpu_alert', 80)}): ").strip()
            if cpu_threshold:
                thresholds['cpu_alert'] = int(cpu_threshold)
            
            memory_threshold = input(f"Memory alert threshold % (current: {thresholds.get('memory_alert', 85)}): ").strip()
            if memory_threshold:
                thresholds['memory_alert'] = int(memory_threshold)
            
            self.config['thresholds'] = thresholds
            self.save_config()
            print("✅ Configuration saved!")
            
        except ValueError:
            print("❌ Invalid input. Configuration not changed.")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Blockchain Anomaly Detection - Automation Manager")
    parser.add_argument('--action', choices=['status', 'health', 'monitor', 'retrain', 'deploy', 'interactive'], 
                       help='Action to perform')
    parser.add_argument('--start-server', action='store_true', help='Start Prefect server')
    parser.add_argument('--start-agent', action='store_true', help='Start Prefect agent')
    
    args = parser.parse_args()
    
    manager = AutomationManager()
    
    if args.start_server:
        manager.start_prefect_server()
        return
    
    if args.start_agent:
        manager.start_prefect_agent()
        return
    
    if args.action == 'status':
        manager.show_status()
    elif args.action == 'health':
        asyncio.run(manager.run_health_check())
    elif args.action == 'monitor':
        asyncio.run(manager.run_system_monitoring())
    elif args.action == 'retrain':
        asyncio.run(manager.run_model_retraining())
    elif args.action == 'deploy':
        manager.deploy_workflows()
    elif args.action == 'interactive' or not args.action:
        manager.interactive_menu()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()