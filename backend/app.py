from flask import Flask, render_template, request, redirect, url_for, flash
import os

app = Flask(__name__, 
            template_folder='../frontend/templates', 
            static_folder='../frontend/static')  # This should correctly point to your static folder
# Set a secret key for session management
app.secret_key = '630808'  # Replace with a strong secret key

# Directory to save uploaded images
UPLOAD_FOLDER = 'uploads'  # Make sure this folder exists in your project root
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        # Save the file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        
        flash('File uploaded successfully')
        return redirect(url_for('home'))

    return render_template('upload.html')  # This should have a form for file uploads

if __name__ == '__main__':
    app.run(debug=True)
