import os
from frontstage import app


if __name__ == '__main__':
    DEV_PORT = os.getenv('DEV_PORT', 5001)
    app.run(debug=True, host='0.0.0.0', port=int(DEV_PORT))
