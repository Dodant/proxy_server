import os, time, uuid
from io import BytesIO
from PIL import Image
import warnings, logging
from logging.handlers import RotatingFileHandler

from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.log')
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

@app.route('/prx', methods=['POST'])
def prx_image():
    if 'image' not in request.files or 'method' not in request.form:
        return jsonify({'error': 'No image or method provided'}), 400

    print("Headers:\n", request.headers)
    print("Body:\n", request.get_data(as_text=True))
    print("Form Data:\n", request.form)
    print("Form method:\n", request.form.get('method'))
    
    if 'method' not in request.form:
        return jsonify(error='No method part'), 400
        
    if 'image' not in request.files:
        return jsonify(error='No image part'), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify(error='No selected file'), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        userID, hostIP, port = "compu", "220.117.189.130", 2322
        address = f"{userID}@{hostIP}"
        path = f"/home/{userID}/Downloads/tmp2/image-outpainting_2"
        method = request.form.get('method')

        os.system(f"scp -P {port} ./{filepath} {address}:{path}/req_img/")
        os.system(f"ssh {address} -p {port} \"curl -X POST -F 'image=@{path}/req_img/{filename}' -F 'method={method}' http://127.0.0.1:5004/process_image --output {path}/req_img/{''.join(filename.split('.')[:-1])}_{method}.jpg\"")
        os.system(f"scp -P {port} {address}:{path}/req_img/{''.join(filename.split('.')[:-1])}_{method}.jpg ./{app.config['DOWNLOAD_FOLDER']}")
        # os.system(f"ssh {address} -p {port} \"rm -r {path}/req_img/*\"")
        
        download_path = os.path.join(app.config['DOWNLOAD_FOLDER'], f"{''.join(filename.split('.')[:-1])}_{method}.jpg")
        if os.path.exists(download_path):
            with open(download_path, 'rb') as file: 
                img_data = file.read()
            return send_file(BytesIO(img_data), mimetype='image/jpeg')
        else:
            return jsonify(error='File not found'), 404

    return jsonify(error='Invalid file type'), 400

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']): os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['DOWNLOAD_FOLDER']): os.makedirs(app.config['DOWNLOAD_FOLDER'])
    
    hostIP = '0.0.0.0'
    app.run(host=hostIP, port=5004, debug=True)