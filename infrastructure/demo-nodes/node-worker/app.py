import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["NODE_ID"] = "cs-node-worker"
os.environ["SERVICE_NAME"] = "worker"
os.environ["PORT"] = "8003"

from common_node import run_server

if __name__ == "__main__":
    run_server()
