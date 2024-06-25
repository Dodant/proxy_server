import os
import os.path as pth
import time
import uuid
from io import BytesIO
from PIL import Image
import warnings
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

import config

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

log_file_path = pth.join(pth.dirname(pth.abspath(__file__)), 'app.log')
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)

app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

warnings.filterwarnings('ignore')


def log_image_info(file_data):
    try:
        image = Image.open(BytesIO(file_data))
        app.logger.info(f"Image format: {image.format}")
        app.logger.info(f"Image size: {image.size}")
        app.logger.info(f"Image mode: {image.mode}")
    except Exception as e:
        app.logger.error(f"Error reading image data: {str(e)}")
        
@app.before_request
def log_request_info():
    request.id = uuid.uuid4()
    request.start_time = time.time()
    app.logger.info(f"Request ID: {request.id} - {request.method} {request.url}")
    app.logger.info(f"Headers: {request.headers}")
    
    if 'image' in request.files:
        image_file = request.files['image']
        file_data = image_file.read()
        log_image_info(file_data)
        image_file.seek(0)
    else:
        app.logger.info(f"Body: {request.get_data()}")

@app.after_request
def log_response_info(response):
    duration = time.time() - request.start_time
    app.logger.info(f"Request ID: {request.id} - Duration: {duration:.3f}s")
    app.logger.info(f"Response: {response.status}")
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Exception: {str(e)}", exc_info=True)
    return "An error occurred", 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_uploaded_file(file):
    filename = secure_filename(file.filename)
    filepath = pth.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return filepath, filename

def execute_remote_commands(filepath, filename, method):
    base_filename = ''.join(filename.split('.')[:-1])
    remote_filepath = pth.join(config.path, 'req_img', filename)
    output_filename = f"{base_filename}_{method}.jpg"
    output_filepath = pth.join(config.path, 'req_img', output_filename)

    scp_upload_cmd = f"scp -P {config.port} ./{filepath} {config.address}:{remote_filepath}"
    curl_cmd = f"ssh {config.address} -p {config.port} \"curl -X POST -F 'image=@{remote_filepath}' -F 'method={method}' http://127.0.0.1:{config.outerport}/process_image --output {output_filepath}\""
    scp_download_cmd = f"scp -P {config.port} {config.address}:{output_filepath} ./{app.config['DOWNLOAD_FOLDER']}"
    cleanup_cmd = f"ssh {config.address} -p {config.port} \"rm -r {config.path}/req_img/*\""

    for cmd in [scp_upload_cmd, curl_cmd, scp_download_cmd, cleanup_cmd]:
        os.system(cmd)

    return output_filename

@app.route('/prx', methods=['POST'])
def prx_image():
    if 'image' not in request.files or 'method' not in request.form:
        return jsonify({'error': 'No image or method provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify(error='No selected file'), 400
    
    if file and allowed_file(file.filename):
        filepath, filename = save_uploaded_file(file)
        method = request.form.get('method')
        output_filename = execute_remote_commands(filepath, filename, method)
        download_path = pth.join(app.config['DOWNLOAD_FOLDER'], output_filename)

        if pth.exists(download_path):
            with open(download_path, 'rb') as file: 
                img_data = file.read()
            return send_file(BytesIO(img_data), mimetype='image/jpeg')
        else:
            return jsonify(error='File not found'), 404

    return jsonify(error='Invalid file type'), 400

if __name__ == '__main__':
    if not pth.exists(app.config['UPLOAD_FOLDER']): os.makedirs(app.config['UPLOAD_FOLDER'])
    if not pth.exists(app.config['DOWNLOAD_FOLDER']): os.makedirs(app.config['DOWNLOAD_FOLDER'])
    
    hostIP= '0.0.0.0'
    app.run(host=hostIP, port=config.outerport, debug=True)