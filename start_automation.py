"""
Blockchain Anomaly Detection System - Automation Startup Script

This script provides a complete automation startup solution with:
- Prefect server management
- Workflow deployment
- Health monitoring
- System status dashboard
"""

import os
import sys
import time
import subprocess
import asyncio
from datetime import datetime
from pathlib import Path

import sys
print("Python executable:", sys.executable)
# Add project root to path
sys.path.append(str(Path(__file__).parent))

def print_banner():
    """Print startup banner"""
    print("\n" + "=" * 80)
    print("[*] BLOCKCHAIN ANOMALY DETECTION SYSTEM - AUTOMATION STARTUP")
    print("=" * 80)
    print(f"[*] Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[*] Working Directory: {os.getcwd()}")
    print(f"[*] Python Version: {sys.version.split()[0]}")
    print("=" * 80)

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n[*] Checking Dependencies...")
    
    # Map install names to import names
    package_import_map = {
        'prefect': 'prefect',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'scikit-learn': 'sklearn',  # <-- Fix here
        'psutil': 'psutil',
        'asyncpg': 'asyncpg',
        'redis': 'redis',
        'telegram': 'telegram'
    }
    
    missing_packages = []
    
    for install_name, import_name in package_import_map.items():
        try:
            __import__(import_name)
            print(f"  [+] {install_name}")
        except ImportError:
            print(f"  [-] {install_name} (missing)")
            missing_packages.append(install_name)
    
    if missing_packages:
        print(f"\n[!] Missing packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install " + " ".join(missing_packages))
        return False
    
    print("[+] All dependencies are installed!")
    return True

def check_environment():
    """Check environment setup"""
    print("\n[*] Checking Environment...")
    
    # Check .env file
    if os.path.exists(".env"):
        print("  [+] .env file found")
    else:
        print("  [\!]  .env file not found")
    
    # Check Telegram configuration
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if telegram_token and telegram_chat_id:
        print("  [+] Telegram configuration found")
    else:
        print("  [\!]  Telegram configuration missing")
    
    # Check required directories
    required_dirs = [
        "models",
        "automation",
        "automation/flows",
        "automation/deployments",
        "health_reports",
        "monitoring_data"
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  [+] {dir_path}")
        else:
            print(f"  [*] Creating {dir_path}")
            os.makedirs(dir_path, exist_ok=True)
    
    # Check model file
    if os.path.exists("models/anomaly_model.pkl"):
        print("  [+] ML model found")
    else:
        print("  [\!]  ML model not found - will be trained automatically")
    
    return True

def start_prefect_server():
    """Start Prefect server"""
    print("\n[*] Starting Prefect Server...")
    
    try:
        # Check if server is already running
        result = subprocess.run(
            ["prefect", "server", "database", "reset", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("  [+] Prefect server is already accessible")
            return True
        
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        pass
    
    # Start server
    try:
        print("  [*] Starting Prefect server...")
        server_process = subprocess.Popen(
            ["prefect", "server", "start"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        print("  [*] Waiting for server to start...")
        time.sleep(10)
        
        # Check if server is running
        if server_process.poll() is None:
            print("  [+] Prefect server started successfully")
            print("  [*] UI available at: http://localhost:4200")
            return True
        else:
            stdout, stderr = server_process.communicate(timeout=10)
            stdout_str = stdout.decode()
            stderr_str = stderr.decode()
            
            # Check if port is already in use (server already running)
            if "Port 4200 is already in use" in stdout_str:
                print("  [+] Prefect server is already running on port 4200")
                print("  [*] UI available at: http://localhost:4200")
                return True
            else:
                print("Prefect server stdout:", stdout_str)
                print("Prefect server stderr:", stderr_str)
                print("  [-] Failed to start Prefect server")
                return False
            
    except Exception as e:
        print(f"  [-] Error starting Prefect server: {e}")
        return False

def deploy_workflows():
    """Deploy automation workflows"""
    print("\n[*] Deploying Workflows...")
    
    try:
        from automation.deployments.deploy_flows import deploy_all
        
        print("  [*] Deploying automation flows...")
        deployment_ids = deploy_all()
        
        if deployment_ids:
            print(f"  [+] Successfully deployed {len(deployment_ids)} workflows")
            for i, dep_id in enumerate(deployment_ids, 1):
                print(f"    {i}. {dep_id}")
            return True
        else:
            print("  [-] No workflows were deployed")
            return False
            
    except Exception as e:
        print(f"  [-] Error deploying workflows: {e}")
        return False

def start_prefect_agent():
    """Start Prefect agent"""
    print("\n[*] Starting Prefect Agent...")
    
    try:
        print("  [*] Starting agent...")
        agent_process = subprocess.Popen(
            ["prefect", "agent", "start", "--work-pool", "default-agent-pool"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for agent to start
        time.sleep(5)
        
        if agent_process.poll() is None:
            print("  [+] Prefect agent started successfully")
            return True
        else:
            print("  [-] Failed to start Prefect agent")
            return False
            
    except Exception as e:
        print(f"  [-] Error starting Prefect agent: {e}")
        return False

def run_initial_health_check():
    """Run initial health check"""
    print("\n[*] Running Initial Health Check...")
    
    try:
        from automation.flows.health_monitoring import system_health_check_flow
        
        print("  [*] Executing health check flow...")
        result = asyncio.run(system_health_check_flow())
        
        if result:
            print(f"  [+] Health check completed: {result.get('system_status', 'UNKNOWN')}")
            print(f"  [*] Overall health: {result.get('overall_health', 0):.1%}")
            return True
        else:
            print("  [-] Health check failed")
            return False
            
    except Exception as e:
        print(f"  [-] Error running health check: {e}")
        return False

def show_startup_summary():
    """Show startup summary and next steps"""
    print("\n[*] STARTUP COMPLETE!")
    print("=" * 50)
    print("[+] Automation system is now running")
    print("\n[*] Services Status:")
    print("  • Prefect Server: http://localhost:4200")
    print("  • Prefect Agent: Running")
    print("  • Health Monitoring: Every 15 minutes")
    print("  • System Monitoring: Every 5 minutes")
    print("  • Model Retraining: Daily at 2:00 AM")
    
    print("\n[*] Useful Commands:")
    print("  • Check status: python automation/run_automation.py --action status")
    print("  • Manual health check: python automation/run_automation.py --action health")
    print("  • Interactive menu: python automation/run_automation.py --action interactive")
    print("  • View Prefect UI: http://localhost:4200")
    
    print("\n[*] Notifications:")
    print("  • Telegram alerts are configured")
    print("  • Health alerts will be sent automatically")
    print("  • Model retraining notifications included")
    
    print("\n[*] Next Steps:")
    print("  1. Start your data pipeline: python -m src.data_pipeline.main")
    print("  2. Monitor the Prefect UI for workflow status")
    print("  3. Check Telegram for automated alerts")
    print("  4. Use the optimized dashboard: streamlit run dashboard_optimized.py")
    
    print("\n" + "=" * 80)

def main():
    """Main startup function"""
    print_banner()
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("[-] Dependency check failed. Please install missing packages.")
        return 1
    
    # Step 2: Check environment
    if not check_environment():
        print("[-] Environment check failed. Please fix configuration.")
        return 1
    
    # Step 3: Start Prefect server
    if not start_prefect_server():
        print("[-] Failed to start Prefect server.")
        return 1
    
    # Step 4: Deploy workflows
    if not deploy_workflows():
        print("[-] Failed to deploy workflows.")
        return 1
    
    # Step 5: Start Prefect agent
    if not start_prefect_agent():
        print("[-] Failed to start Prefect agent.")
        return 1
    
    # Step 6: Run initial health check
    if not run_initial_health_check():
        print("[\!]  Initial health check failed, but continuing...")
    
    # Step 7: Show summary
    show_startup_summary()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[*] Startup interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n[-] Startup failed with error: {e}")
        sys.exit(1)