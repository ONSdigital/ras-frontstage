import os
from app.application import app, setup_logging

if __name__ == '__main__':
    setup_logging()
    PORT = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=PORT)
