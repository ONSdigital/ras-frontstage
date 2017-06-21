import os
from app.application import app

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=PORT, debug=False)
