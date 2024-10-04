# from flask import Flask
# from selenium import webdriver
# from selenium.webdriver.common.by import By

# app = Flask(__name__)

# @app.route('/')
# def index():
#     return 'Hello World'

# @app.route('/test')
# def test():
#     """ This is just a simple test that creates a driver, fetch a simple page and check that content could be read """
#     chrome_options = webdriver.ChromeOptions()
#     chrome_options.add_argument('--no-sandbox')
#     chrome_options.add_argument('--headless')
#     chrome_options.add_argument('--disable-gpu')
#     chrome_options.add_argument('--disable-dev-shm-usage')
#     chrome_options.add_argument("--window-size=1920,1080")
#     driver = webdriver.Chrome(options=chrome_options)

#     driver.get('https://httpbin.org/html')

#     h1 = driver.find_element(by=By.TAG_NAME, value='h1')
#     inner_text = h1.text

#     driver.quit()

#     if inner_text == 'Herman Melville - Moby-Dick':
#         return 'OK', 200
#     else:
#         return 'Not Acceptable', 406 


import os
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from automation import run_automation
from flask_cors import CORS


app = Flask(__name__)
CORS(app)  # Allow requests from the React frontend
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Root route to display a welcome page
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']
    start_index = request.form.get('startIndex', type=int)
    end_index = request.form.get('endIndex', type=int)

    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    if start_index is None or end_index is None:
        return jsonify({"message": "Start or End index is missing."}), 400

    # Save the file to the upload folder
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Call the automation function from your existing script
    try:
        # Trigger automation with file and indices
        run_automation(file_path, start_index, end_index)
        return jsonify({"message": "File uploaded and automation process started!"}), 200
    except Exception as e:
        return jsonify({"message": f"Automation failed: {str(e)}"}), 500


if __name__ == '__main__':
    
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

