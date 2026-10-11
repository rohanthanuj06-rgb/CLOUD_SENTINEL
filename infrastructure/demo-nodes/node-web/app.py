import os
import sys

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["NODE_ID"] = "cs-node-web"
os.environ["SERVICE_NAME"] = "web"
os.environ["PORT"] = "8001"

from common_node import run_server

if __name__ == "__main__":
    run_server()
