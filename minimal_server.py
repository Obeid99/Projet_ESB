#!/usr/bin/env python3
"""
Minimal ESB Chatbot Server
"""

from flask import Flask, render_template_string

app = Flask(__name__)

# Simple HTML template
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ESB Multi-Agent Chatbot</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .chat-container { display: flex; gap: 20px; height: 600px; }
        .chat-main { flex: 3; border: 1px solid #ddd; border-radius: 10px; padding: 20px; }
        .chat-sidebar { flex: 1; background: #f8f9fa; border-radius: 10px; padding: 20px; }
        .message { margin: 10px 0; padding: 15px; border-radius: 10px; }
        .user { background: #007bff; color: white; margin-left: 20%; }
        .bot { background: #e9ecef; margin-right: 20%; }
        .input-area { margin-top: 20px; display: flex; gap: 10px; }
        .input-area input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .input-area button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .status { padding: 10px; background: #d4edda; border-radius: 5px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 ESB Multi-Agent Chatbot System</h1>
            <div class="status">✅ System is running successfully! Enhanced UI with right sidebar layout.</div>
        </div>
        
        <div class="chat-container">
            <div class="chat-main">
                <h3>💬 Chat Interface</h3>
                <div id="messages">
                    <div class="message bot">
                        <strong>ESB Assistant:</strong> Hello! I'm your ESB Multi-Agent Chatbot. I can help you with:
                        <ul>
                            <li>📚 Course information and registration</li>
                            <li>🏫 Campus facilities and services</li>
                            <li>🎯 Career guidance and support</li>
                            <li>💡 Academic assistance</li>
                        </ul>
                        How can I help you today?
                    </div>
                </div>
                
                <div class="input-area">
                    <input type="text" id="messageInput" placeholder="Type your message here..." onkeypress="if(event.key==='Enter') sendMessage()">
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
            
            <div class="chat-sidebar">
                <h3>⚡ Agent Processing</h3>
                <div id="agentStatus">
                    <div style="padding: 10px; background: white; border-radius: 5px; margin-bottom: 10px;">
                        <strong>SentimentAgent</strong><br>
                        <small>Ready for sentiment analysis</small>
                    </div>
                    <div style="padding: 10px; background: white; border-radius: 5px; margin-bottom: 10px;">
                        <strong>IntentAgent</strong><br>
                        <small>Ready for intent classification</small>
                    </div>
                    <div style="padding: 10px; background: white; border-radius: 5px; margin-bottom: 10px;">
                        <strong>WebAgent</strong><br>
                        <small>Ready for information gathering</small>
                    </div>
                    <div style="padding: 10px; background: white; border-radius: 5px; margin-bottom: 10px;">
                        <strong>RefinerAgent</strong><br>
                        <small>Ready for response generation</small>
                    </div>
                </div>
                
                <h3>💡 Try These Examples</h3>
                <div style="font-size: 14px;">
                    <div style="margin: 5px 0; cursor: pointer; color: #007bff;" onclick="setMessage('I love ESB!')">• "I love ESB!"</div>
                    <div style="margin: 5px 0; cursor: pointer; color: #007bff;" onclick="setMessage('I need help with registration')">• "I need help with registration"</div>
                    <div style="margin: 5px 0; cursor: pointer; color: #007bff;" onclick="setMessage('Tell me about courses')">• "Tell me about courses"</div>
                    <div style="margin: 5px 0; cursor: pointer; color: #007bff;" onclick="setMessage('I am feeling stressed')">• "I am feeling stressed"</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            // Add user message
            addMessage('user', message);
            input.value = '';
            
            // Simulate bot response
            setTimeout(() => {
                addBotResponse(message);
            }, 1000);
        }
        
        function addMessage(type, content) {
            const messages = document.getElementById('messages');
            const div = document.createElement('div');
            div.className = `message ${type}`;
            div.innerHTML = `<strong>${type === 'user' ? 'You' : 'ESB Assistant'}:</strong> ${content}`;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function addBotResponse(userMessage) {
            let response = "Thank you for your message! ";
            
            // Simple sentiment-aware responses
            const msg = userMessage.toLowerCase();
            if (msg.includes('love') || msg.includes('great') || msg.includes('amazing')) {
                response += "I'm so glad to hear your positive feedback! 😊 Your enthusiasm makes our day. ";
            } else if (msg.includes('stress') || msg.includes('overwhelm') || msg.includes('difficult')) {
                response += "I understand you're going through a tough time. 🤗 Take a deep breath - you're not alone and we're here to support you. ";
            } else if (msg.includes('help') || msg.includes('need')) {
                response += "I'm here to help you! 💪 Let me guide you through this step by step. ";
            }
            
            if (msg.includes('registration')) {
                response += "For registration assistance, please log into the student portal during your registration window. Contact the registrar's office if you encounter any issues.";
            } else if (msg.includes('course')) {
                response += "ESB offers comprehensive business programs including Finance, Marketing, Management, and Operations. Would you like specific information about any program?";
            } else if (msg.includes('stress')) {
                response += "Consider reaching out to our counseling services, taking breaks when needed, and remember that asking for help is a sign of strength.";
            } else {
                response += "I'm here to assist with course information, registration, campus facilities, and academic support. What specific area would you like help with?";
            }
            
            addMessage('bot', response);
            
            // Update sidebar with processing simulation
            updateProcessing();
        }
        
        function updateProcessing() {
            const status = document.getElementById('agentStatus');
            status.innerHTML = `
                <div style="padding: 10px; background: #d4edda; border-radius: 5px; margin-bottom: 5px;">
                    <strong>SentimentAgent</strong> <span style="float: right; font-size: 11px; background: #28a745; color: white; padding: 2px 6px; border-radius: 10px;">15ms</span><br>
                    <small>positive (0.85)</small>
                </div>
                <div style="padding: 10px; background: #d4edda; border-radius: 5px; margin-bottom: 5px;">
                    <strong>IntentAgent</strong> <span style="float: right; font-size: 11px; background: #28a745; color: white; padding: 2px 6px; border-radius: 10px;">8ms</span><br>
                    <small>general_info</small>
                </div>
                <div style="padding: 10px; background: #d4edda; border-radius: 5px; margin-bottom: 5px;">
                    <strong>WebAgent</strong> <span style="float: right; font-size: 11px; background: #28a745; color: white; padding: 2px 6px; border-radius: 10px;">245ms</span><br>
                    <small>2 sources found</small>
                </div>
                <div style="padding: 10px; background: #d4edda; border-radius: 5px; margin-bottom: 5px;">
                    <strong>RefinerAgent</strong> <span style="float: right; font-size: 11px; background: #28a745; color: white; padding: 2px 6px; border-radius: 10px;">12ms</span><br>
                    <small>Response generated</small>
                </div>
            `;
        }
        
        function setMessage(text) {
            document.getElementById('messageInput').value = text;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(TEMPLATE)

if __name__ == "__main__":
    print("🤖 ESB Multi-Agent Chatbot System")
    print("=" * 40)
    print("✅ Minimal server starting...")
    print("🌐 Open your browser to: http://localhost:5000")
    print("💬 Enhanced UI with right sidebar layout!")
    print("=" * 40)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )
