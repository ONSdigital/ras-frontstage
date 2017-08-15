import os
import logging
from frontstage import app
from frontstage.cloud.cloud_foundry import ONSCloudFoundry
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))

if __name__ == '__main__':
    cf = ONSCloudFoundry()
    # First check if front-stage is deployed in a Cloud Foundry environment
    if cf.detected:
        port = cf.port
        protocol = cf.protocol
        logger.info('* Cloud Foundry environment detected.')
        logger.info('* Cloud Foundry port "{}"'.format(port))
        logger.info('* Cloud Foundry protocol "{}"'.format(protocol))
    else:
        port = os.getenv('FS_DEV_PORT', 5001)
    logger.info('* starting listening port "{}"'.format(port))
    app.run(debug=True, host='0.0.0.0', port=int(port))
