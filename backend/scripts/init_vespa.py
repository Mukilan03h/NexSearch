"""
Script to initialize Vespa application package.
"""
from src.storage.vespa_client import VespaClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    logger.info("Initializing Vespa...")
    client = VespaClient()
    
    if client.wait_for_ready(max_wait=60):
        # Path relative to inside the container
        if client.deploy_application("/app/vespa"):
            logger.info("Vespa application deployed successfully!")
        else:
            logger.error("Failed to deploy Vespa application.")
    else:
        logger.error("Vespa service not ready.")

if __name__ == "__main__":
    main()
