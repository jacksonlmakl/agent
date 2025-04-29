from flask import Flask, request, jsonify, render_template_string
from model import Model
import uuid
import time
import threading

# Initialize the model outside of routes to ensure it persists between requests
global MODEL
MODEL = Model()

def chat(prompt):
    # We want to get a response immediately without waiting for background processing
    r = MODEL.chat(prompt, web=False, rag=True, tokens=300, use_gpt=False, use_sub_gpt=True, iters=3)
    return r

app = Flask(__name__)

# Store conversation history
conversations = {}

# HTML template for the chat interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Train</title>
    <!-- Include Marked.js for Markdown rendering -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/4.0.2/marked.min.js"></script>
    <style>
        :root {
            --primary-color: #00847E;    /* Teal instead of purple */
            --primary-light: #E4F7F6;    /* Light teal background */
            --secondary-color: #F4364C;  /* Red accent instead of green */
            --text-color: #1F2937;       /* Darker text */
            --light-text: #6B7280;       /* Different gray tone */
            --border-color: #D1D5DB;     /* Slightly darker border */
            --bg-color: #F9FAFB;         /* Slightly different background */
            --message-user-bg: #E4F7F6;  /* Light teal for user messages */
            --message-bot-bg: #FFFFFF;   /* White remains for bot messages */
            --shadow: 0 2px 8px rgba(0,0,0,0.08); /* Slightly stronger shadow */
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
            height: 100vh;
            overflow: hidden;
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
        
        main {
            flex: 1;
            display: flex;
            flex-direction: column;
            max-width: 900px;
            width: 100%;
            margin: 0 auto;
            padding: 0;
            overflow: hidden;
        }
        
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 24px 12px;
            scroll-behavior: smooth;
        }
        
        .message-wrapper {
            display: flex;
            flex-direction: column;
            margin-bottom: 24px;
            max-width: 100%;
        }
        
        .message {
            padding: 16px 20px;
            border-radius: 12px;
            line-height: 1.5;
            font-size: 1rem;
            max-width: 90%;
            overflow-wrap: break-word;
        }
        
        .message pre {
            white-space: pre-wrap;
            background-color: #f6f8fa;
            border-radius: 6px;
            padding: 12px;
            overflow-x: auto;
            margin: 10px 0;
        }
        
        .message code {
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.875rem;
            background-color: rgba(0,0,0,0.05);
            padding: 2px 4px;
            border-radius: 3px;
        }
        
        .message pre code {
            background-color: transparent;
            padding: 0;
        }
        
        .message p {
            margin-bottom: 10px;
        }
        
        .message p:last-child {
            margin-bottom: 0;
        }
        
        .message ul, .message ol {
            margin: 10px 0;
            padding-left: 24px;
        }
        
        .message h1, .message h2, .message h3, .message h4 {
            margin: 16px 0 8px;
        }
        
        .user-message-wrapper {
            align-items: flex-end;
            margin-left: auto;
        }
        
        .bot-message-wrapper {
            align-items: flex-start;
        }
        
        .message-avatar {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
        }
        
        .user-avatar {
            background-color: var(--primary-color);
        }
        
        .bot-avatar {
            background-color: var(--secondary-color);
        }
        
        .user-message {
            background-color: var(--message-user-bg);
            color: var(--text-color);
            border-bottom-right-radius: 4px;
        }
        
        .bot-message {
            background-color: var(--message-bot-bg);
            color: var(--text-color);
            border-bottom-left-radius: 4px;
            box-shadow: var(--shadow);
        }
        
        .input-container {
            background-color: white;
            padding: 16px;
            border-top: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            position: relative;
        }
        
        .input-box {
            display: flex;
            width: 100%;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: var(--shadow);
        }
        
        #user-input {
            flex: 1;
            padding: 14px;
            border: none;
            outline: none;
            font-size: 1rem;
            resize: none;
            max-height: 200px;
            min-height: 48px;
            line-height: 1.5;
            background-color: white;
        }
        
        #send-button {
            background-color: var(--primary-color);
            color: white;
            border: none;
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: background-color 0.2s;
            flex-shrink: 0;
        }
        
        #send-button:hover {
            background-color: #4630b8;
        }
        
        #send-button:disabled {
            background-color: #a9a6c9;
            cursor: not-allowed;
        }
        
        .send-icon {
            width: 20px;
            height: 20px;
            background-color: white;
            mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='22' y1='2' x2='11' y2='13'%3E%3C/line%3E%3Cpolygon points='22 2 15 22 11 13 2 9 22 2'%3E%3C/polygon%3E%3C/svg%3E") no-repeat center center;
            -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='22' y1='2' x2='11' y2='13'%3E%3C/line%3E%3Cpolygon points='22 2 15 22 11 13 2 9 22 2'%3E%3C/polygon%3E%3C/svg%3E") no-repeat center center;
        }
        
        .typing-indicator {
            display: none;
            padding: 12px;
            color: var(--light-text);
            align-items: center;
            font-size: 0.9rem;
        }
        
        .typing-animation {
            display: inline-flex;
            margin-left: 8px;
        }
        
        .typing-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: var(--light-text);
            margin: 0 2px;
            animation: typing-bounce 1.4s infinite ease-in-out both;
        }
        
        .typing-dot:nth-child(1) {
            animation-delay: -0.32s;
        }
        
        .typing-dot:nth-child(2) {
            animation-delay: -0.16s;
        }
        
        @keyframes typing-bounce {
            0%, 80%, 100% {
                transform: scale(0);
            }
            40% {
                transform: scale(1);
            }
        }
        
        @media (max-width: 768px) {
            .message {
                max-width: 95%;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="logo">
            <span class="logo-icon"></span>
            Train
        </div>
    </header>
    <main>
        <div class="chat-container" id="chat-container">
            <!-- Messages will be dynamically added here -->
        </div>
        <div class="typing-indicator" id="typing-indicator">
            <div class="message-avatar bot-avatar">AI</div>
            &nbsp; Thinking
            <div class="typing-animation">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
        <div class="input-container">
            <div class="input-box">
                <textarea id="user-input" placeholder="Message..." rows="1" autofocus></textarea>
                <button id="send-button" disabled>
                    <span class="send-icon"></span>
                </button>
            </div>
        </div>
    </main>

    <script>
        // Create a unique session ID
        const sessionId = Date.now().toString();
        
        // DOM elements
        const chatContainer = document.getElementById('chat-container');
        const userInput = document.getElementById('user-input');
        const sendButton = document.getElementById('send-button');
        const typingIndicator = document.getElementById('typing-indicator');
        
        // Auto-resize textarea
        userInput.addEventListener('input', function() {
            // Reset height to auto to get the right scrollHeight
            this.style.height = 'auto';
            // Set new height
            const newHeight = Math.min(this.scrollHeight, 200);
            this.style.height = newHeight + 'px';
            
            // Enable/disable send button based on input
            sendButton.disabled = this.value.trim() === '';
        });
        
        // Function to add a message to the chat
        function addMessage(content, isUser) {
            const messageWrapper = document.createElement('div');
            messageWrapper.classList.add('message-wrapper');
            messageWrapper.classList.add(isUser ? 'user-message-wrapper' : 'bot-message-wrapper');
            
            const avatar = document.createElement('div');
            avatar.classList.add('message-avatar');
            avatar.classList.add(isUser ? 'user-avatar' : 'bot-avatar');
            avatar.textContent = isUser ? 'U' : 'AI';
            messageWrapper.appendChild(avatar);
            
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message');
            messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
            
            if (isUser) {
                messageDiv.textContent = content;
            } else {
                // Use marked.js to render markdown for bot messages
                messageDiv.innerHTML = marked.parse(content);
            }
            
            messageWrapper.appendChild(messageDiv);
            chatContainer.appendChild(messageWrapper);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // Function to send a message
        async function sendMessage() {
            const message = userInput.value.trim();
            if (!message) return;
            
            // Display user message
            addMessage(message, true);
            
            // Clear input and reset height
            userInput.value = '';
            userInput.style.height = 'auto';
            sendButton.disabled = true;
            
            // Show typing indicator
            typingIndicator.style.display = 'flex';
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            try {
                // Send message to backend
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: sessionId
                    }),
                });
                
                const data = await response.json();
                
                // Hide typing indicator
                typingIndicator.style.display = 'none';
                
                // Display bot response with markdown rendering
                addMessage(data.response, false);
            } catch (error) {
                console.error('Error:', error);
                typingIndicator.style.display = 'none';
                addMessage('An error occurred. Please try again.', false);
            }
        }
        
        // Event listeners
        sendButton.addEventListener('click', sendMessage);
        userInput.addEventListener('keydown', (e) => {
            // Send on Enter (without Shift key)
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!sendButton.disabled) {
                    sendMessage();
                }
            }
        });
        
        // Focus input on page load
        window.addEventListener('load', () => {
            userInput.focus();
        });
        
        // Welcome message
        addMessage('Hello! How can I help you today?', false);
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def handle_chat():
    data = request.json
    message = data.get('message', '')
    session_id = data.get('session_id', str(uuid.uuid4()))
    
    # Initialize or get existing conversation
    if session_id not in conversations:
        conversations[session_id] = []
    
    # Add user message to context
    if message:
        conversations[session_id].append({"role": "user", "content": message})
    
    # Get response from model - this will start background processing but return immediately
    response = chat(message)
    
    # Add assistant response to context
    conversations[session_id].append({"role": "assistant", "content": response})
    
    # Return the response to the client without waiting for background tasks
    return jsonify({"response": response})

# Clean up old conversations periodically
def cleanup_old_conversations():
    while True:
        try:
            time.sleep(3600)  # Check once per hour
            current_time = time.time()
            # Keep only conversations from the last 24 hours
            cutoff_time = current_time - (24 * 3600)
            
            # We need to find a way to determine when a conversation was last active
            # For now, we'll just limit the total number of conversations
            if len(conversations) > 100:
                # Remove oldest 20 conversations - assumes keys (session_ids) are chronological
                keys_to_remove = sorted(conversations.keys())[:20]
                for key in keys_to_remove:
                    if key in conversations:
                        del conversations[key]
                        
        except Exception as e:
            print(f"Error in cleanup thread: {e}")

# Start the cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_conversations, daemon=True)
cleanup_thread.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)