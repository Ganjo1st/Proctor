import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('proctor_logger.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

try:
    # Example function to test logging
    def test_logging():
        logger.info('Initializing Proctor Logger')
        x = 1 / 0  # Intentional error for logging demonstration

    test_logging()
except Exception as e:
    logger.error('An error occurred: %s', e)
    
