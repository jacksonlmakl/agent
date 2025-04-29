from flask import Flask, request, render_template_string, redirect, url_for, flash
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "upload_secret_key"  # For flash messages

# Configure upload folder
UPLOAD_FOLDER = 'documents'
ALLOWED_EXTENSIONS = {'pdf'}

# Create the upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# HTML template for the upload interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Upload</title>
    <style>
        :root {
            --primary-color: #5436DA;
            --primary-light: #EBE9F7;
            --secondary-color: #10A37F;
            --text-color: #343541;
            --light-text: #6E6E80;
            --border-color: #E5E5E5;
            --bg-color: #F7F7F8;
            --message-user-bg: #EBE9F7;
            --message-bot-bg: #FFFFFF;
            --shadow: 0 2px 6px rgba(0,0,0,0.05);
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }
        
        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        
        header {
            background-color: #FFFFFF;
            padding: 16px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: var(--shadow);
            z-index: 10;
        }
        
        .logo {
            font-weight: 700;
            font-size: 1.25rem;
            color: var(--primary-color);
            display: flex;
            align-items: center;
        }
        
        .logo-icon {
            display: inline-block;
            width: 28px;
            height: 28px;
            background-color: var(--primary-color);
            border-radius: 8px;
            margin-right: 8px;
            position: relative;
        }
        
        .logo-icon::after {
            content: "";
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 14px;
            height: 14px;
            background-color: white;
            mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'%3E%3C/path%3E%3C/svg%3E") no-repeat center center;
            -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'%3E%3C/path%3E%3C/svg%3E") no-repeat center center;
        }

        .nav-links {
            display: flex;
            position: absolute;
            right: 24px;
        }

        .nav-link {
            color: var(--primary-color);
            text-decoration: none;
            margin-left: 20px;
            font-weight: 500;
            font-size: 0.9rem;
            transition: opacity 0.2s;
        }

        .nav-link:hover {
            opacity: 0.8;
        }
        
        main {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px 20px;
        }
        
        .upload-container {
            background-color: white;
            border-radius: 12px;
            box-shadow: var(--shadow);
            width: 100%;
            max-width: 600px;
            padding: 32px;
            text-align: center;
        }
        
        h1 {
            color: var(--text-color);
            font-size: 1.5rem;
            margin-bottom: 8px;
        }
        
        p {
            color: var(--light-text);
            margin-bottom: 24px;
        }
        
        .upload-area {
            border: 2px dashed var(--border-color);
            border-radius: 8px;
            padding: 40px 20px;
            margin-bottom: 24px;
            cursor: pointer;
            transition: background-color 0.2s, border-color 0.2s;
            position: relative;
        }
        
        .upload-area:hover {
            background-color: var(--primary-light);
            border-color: var(--primary-color);
        }
        
        .upload-icon {
            width: 48px;
            height: 48px;
            margin: 0 auto 16px;
            opacity: 0.7;
        }
        
        .upload-icon svg {
            width: 100%;
            height: 100%;
            fill: none;
            stroke: var(--primary-color);
            stroke-width: 1.5;
        }
        
        .upload-text {
            font-size: 1rem;
            color: var(--text-color);
            margin-bottom: 8px;
        }
        
        .upload-hint {
            font-size: 0.875rem;
            color: var(--light-text);
        }
        
        .file-input {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0;
            cursor: pointer;
        }
        
        .upload-btn {
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .upload-btn:hover {
            background-color: #4630b8;
        }
        
        .upload-btn:disabled {
            background-color: #a9a6c9;
            cursor: not-allowed;
        }

        .selected-file {
            margin-top: 16px;
            padding: 12px;
            background-color: var(--primary-light);
            border-radius: 8px;
            display: none;
        }

        .file-name {
            font-weight: 500;
            color: var(--primary-color);
            word-break: break-all;
        }

        .remove-file {
            color: var(--secondary-color);
            background: none;
            border: none;
            cursor: pointer;
            font-size: 0.875rem;
            margin-top: 8px;
        }

        .flash-message {
            position: fixed;
            top: 80px;
            left: 50%;
            transform: translateX(-50%);
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            z-index: 100;
            font-size: 0.9rem;
            animation: fadeInOut 4s forwards;
        }

        .success {
            background-color: var(--secondary-color);
            color: white;
        }

        .error {
            background-color: #e53e3e;
            color: white;
        }

        @keyframes fadeInOut {
            0% { opacity: 0; transform: translate(-50%, -20px); }
            10% { opacity: 1; transform: translate(-50%, 0); }
            90% { opacity: 1; transform: translate(-50%, 0); }
            100% { opacity: 0; transform: translate(-50%, -20px); }
        }

        .uploaded-files {
            margin-top: 32px;
            width: 100%;
            text-align: left;
        }

        .uploaded-files h2 {
            font-size: 1.2rem;
            margin-bottom: 12px;
            color: var(--text-color);
        }

        .file-list {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
        }

        .file-item {
            padding: 12px 16px;
            display: flex;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
        }

        .file-item:last-child {
            border-bottom: none;
        }

        .file-icon {
            width: 32px;
            height: 32px;
            margin-right: 12px;
            background-color: var(--primary-light);
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: var(--primary-color);
        }

        .file-info {
            flex: 1;
        }

        .file-title {
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 4px;
            word-break: break-all;
        }

        .file-meta {
            font-size: 0.8rem;
            color: var(--light-text);
        }

        .empty-list {
            padding: 24px;
            text-align: center;
            color: var(--light-text);
            font-size: 0.9rem;
        }

        footer {
            padding: 20px;
            background-color: white;
            text-align: center;
            font-size: 0.8rem;
            color: var(--light-text);
            border-top: 1px solid var(--border-color);
        }
    </style>
</head>
<body>
    <header>
        <div class="logo">
            <span class="logo-icon"></span>
            AI Chat
        </div>
        <div class="nav-links">
            <a href="/chat" class="nav-link">Chat</a>
            <a href="/" class="nav-link">Upload</a>
        </div>
    </header>

    <main>
        <div class="upload-container">
            <h1>Upload Documents</h1>
            <p>Upload PDF files for analysis by our AI assistant.</p>
            
            <form action="/upload" method="post" enctype="multipart/form-data" id="upload-form">
                <div class="upload-area" id="upload-area">
                    <div class="upload-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="17 8 12 3 7 8"></polyline>
                            <line x1="12" y1="3" x2="12" y2="15"></line>
                        </svg>
                    </div>
                    <div class="upload-text">Drag & drop your file here</div>
                    <div class="upload-hint">or click to browse your files</div>
                    <input type="file" name="file" class="file-input" id="file-input" accept=".pdf">
                </div>
                
                <div class="selected-file" id="selected-file">
                    <div class="file-name" id="file-name"></div>
                    <button type="button" class="remove-file" id="remove-file">Remove</button>
                </div>
                
                <button type="submit" class="upload-btn" id="upload-btn" disabled>Upload Document</button>
            </form>
            
            <div class="uploaded-files">
                <h2>Your Documents</h2>
                <div class="file-list">
                    {% if files %}
                        {% for file in files %}
                            <div class="file-item">
                                <div class="file-icon">PDF</div>
                                <div class="file-info">
                                    <div class="file-title">{{ file.name }}</div>
                                    <div class="file-meta">Uploaded {{ file.date }}</div>
                                </div>
                            </div>
                        {% endfor %}
                    {% else %}
                        <div class="empty-list">
                            No documents uploaded yet.
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </main>

    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="flash-message {{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <footer>
        © 2025 AI Chat. All rights reserved.
    </footer>

    <script>
        // DOM elements
        const fileInput = document.getElementById('file-input');
        const uploadForm = document.getElementById('upload-form');
        const selectedFile = document.getElementById('selected-file');
        const fileName = document.getElementById('file-name');
        const removeFile = document.getElementById('remove-file');
        const uploadBtn = document.getElementById('upload-btn');
        const uploadArea = document.getElementById('upload-area');

        // Handle file selection
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                const file = this.files[0];
                
                if (isValidPdf(file)) {
                    fileName.textContent = file.name;
                    selectedFile.style.display = 'block';
                    uploadBtn.disabled = false;
                    uploadArea.style.borderColor = 'var(--primary-color)';
                    uploadArea.style.backgroundColor = 'var(--primary-light)';
                } else {
                    resetFileInput();
                    showCustomFlash('Please select a valid PDF file.', 'error');
                }
            } else {
                resetFileInput();
            }
        });

        // Handle drag and drop
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.style.borderColor = 'var(--primary-color)';
            this.style.backgroundColor = 'var(--primary-light)';
        });

        uploadArea.addEventListener('dragleave', function() {
            if (!fileInput.files.length) {
                this.style.borderColor = 'var(--border-color)';
                this.style.backgroundColor = '';
            }
        });

        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            
            if (e.dataTransfer.files.length > 0) {
                const file = e.dataTransfer.files[0];
                
                if (isValidPdf(file)) {
                    fileInput.files = e.dataTransfer.files;
                    fileName.textContent = file.name;
                    selectedFile.style.display = 'block';
                    uploadBtn.disabled = false;
                } else {
                    this.style.borderColor = 'var(--border-color)';
                    this.style.backgroundColor = '';
                    showCustomFlash('Please select a valid PDF file.', 'error');
                }
            }
        });

        // Remove selected file
        removeFile.addEventListener('click', function() {
            resetFileInput();
        });

        // Form submission
        uploadForm.addEventListener('submit', function() {
            uploadBtn.disabled = true;
            uploadBtn.textContent = 'Uploading...';
        });
        
        // Helper functions
        function resetFileInput() {
            fileInput.value = '';
            fileName.textContent = '';
            selectedFile.style.display = 'none';
            uploadBtn.disabled = true;
            uploadArea.style.borderColor = 'var(--border-color)';
            uploadArea.style.backgroundColor = '';
        }
        
        function isValidPdf(file) {
            return file.type === 'application/pdf';
        }
        
        function showCustomFlash(message, category) {
            const flashDiv = document.createElement('div');
            flashDiv.className = `flash-message ${category}`;
            flashDiv.textContent = message;
            document.body.appendChild(flashDiv);
            
            setTimeout(() => {
                flashDiv.remove();
            }, 4000);
        }

        // Auto-hide flash messages
        const flashMessages = document.querySelectorAll('.flash-message');
        flashMessages.forEach(message => {
            setTimeout(() => {
                message.remove();
            }, 4000);
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    # Get list of uploaded files
    files = []
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.lower().endswith('.pdf'):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file_stats = os.stat(file_path)
                # Basic file date - could be enhanced to show actual upload date if stored
                import datetime
                mod_time = datetime.datetime.fromtimestamp(file_stats.st_mtime)
                files.append({
                    'name': filename,
                    'date': mod_time.strftime('%b %d, %Y')
                })
    
    # Sort files by date (newest first)
    files.sort(key=lambda x: x['name'], reverse=True)
    
    return render_template_string(HTML_TEMPLATE, files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('home'))
    
    file = request.files['file']
    
    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('home'))
    
    if file and allowed_file(file.filename):
        # Create a secure filename and save
        filename = secure_filename(file.filename)
        
        # If file exists, append a unique identifier
        if os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{str(uuid.uuid4())[:8]}{ext}"
        
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        flash(f'File {filename} uploaded successfully!', 'success')
        return redirect(url_for('home'))
    
    flash('Invalid file type. Only PDF files are allowed.', 'error')
    return redirect(url_for('home'))

# Add route to access chat application
@app.route('/chat')
def chat():
    return redirect('http://localhost:5000')

if __name__ == '__main__':
    # Run on a different port than the chat app
    app.run(debug=True, host='0.0.0.0', port=5002)