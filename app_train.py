from flask import Flask, request, jsonify, render_template_string
from model import Model
import uuid

app = Flask(__name__)
global MODEL
MODEL=Model()
def chat(prompt):
    MODEL.chat("What Challenges Does Airbnb Face?",web=False,rag=True,tokens=450,use_gpt=True,use_sub_gpt=True,iters=3)
    return MODEL.conscious[-1]['content']

# Store conversation history
conversations = {}

# HTML template for the chat interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat Based Model Training</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            height: 100vh;
            background-color: #f0f2f5;
        }
        header {
            background-color:  #f69e00;
            color: white;
            padding: 1rem;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h1 {
            margin: 0;
            font-size: 1.5rem;
        }
        .container {
            flex: 1;
            display: flex;
            flex-direction: column;
            max-width: 800px;
            margin: 0 auto;
            width: 100%;
            padding: 1rem;
            box-sizing: border-box;
        }
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        .message {
            margin-bottom: 1rem;
            padding: 0.8rem;
            border-radius: 8px;
            max-width: 80%;
        }
        .user-message {
            background-color: #e3f2fd;
            margin-left: auto;
            border-bottom-right-radius: 0;
        }
        .bot-message {
            background-color: #f1f1f1;
            margin-right: auto;
            border-bottom-left-radius: 0;
            white-space: pre-wrap;
        }
        .input-container {
            display: flex;
            gap: 0.5rem;
        }
        #user-input {
            flex: 1;
            padding: 0.8rem;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 1rem;
        }
        button {
            padding: 0.8rem 1.5rem;
            background-color: #f69e00;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
        }
        button:hover {
            background-color: #3d6293;
        }
        .typing-indicator {
            display: none;
            margin-bottom: 1rem;
            font-style: italic;
            color: #666;
        }
    </style>
</head>
<body>
    <header>
        <h1>Chat Based Model Training</h1>
    </header>
    <div class="container">
        <div class="chat-container" id="chat-container">
            <!-- Messages will be dynamically added here -->
        </div>
        <div class="typing-indicator" id="typing-indicator">Model is typing...</div>
        <div class="input-container">
            <input type="text" id="user-input" placeholder="Type a message..." autofocus>
            <button id="send-button">Send</button>
        </div>
    </div>

    <script>
        // Create a unique session ID
        const sessionId = Date.now().toString();
        
        // DOM elements
        const chatContainer = document.getElementById('chat-container');
        const userInput = document.getElementById('user-input');
        const sendButton = document.getElementById('send-button');
        const typingIndicator = document.getElementById('typing-indicator');

        // Function to add a message to the chat
        function addMessage(content, isUser) {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message');
            messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
            messageDiv.textContent = content;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        // Function to send a message
        async function sendMessage() {
            const message = userInput.value.trim();
            if (!message) return;

            // Display user message
            addMessage(message, true);
            userInput.value = '';

            // Show typing indicator
            typingIndicator.style.display = 'block';

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
                
                // Display bot response
                addMessage(data.response, false);
            } catch (error) {
                console.error('Error:', error);
                typingIndicator.style.display = 'none';
                addMessage('An error occurred. Please try again.', false);
            }
        }

        // Event listeners
        sendButton.addEventListener('click', sendMessage);
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
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
    
    # Get response from model
    context = conversations[session_id].copy()
    response = chat(message)
    
    # Add assistant response to context
    conversations[session_id].append({"role": "assistant", "content": response})
    
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)