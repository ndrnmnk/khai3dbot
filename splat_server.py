from flask import Flask, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

SPLATS_FOLDER = os.path.join(os.getcwd(), 'splats')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory(SPLATS_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
