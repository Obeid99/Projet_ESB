# 🤖 ESB Multi-Agent Chatbot System

A sophisticated multi-agent chatbot system designed for ESB (Esprit School of Business) that combines traditional NLP techniques with modern LLM capabilities for intelligent student support.

## 🌟 Features

### 🧠 **Hybrid Intelligence**
- **Multi-Model Sentiment Analysis**: TextBlob + VADER + Ollama LLM
- **LLM-Powered Intent Classification**: Dynamic intent detection using local LLMs
- **Context-Aware Responses**: Emotion-appropriate communication templates
- **Real-time Web Information**: Live data gathering for accurate responses

### 🤖 **Multi-Agent Architecture**
- **SentimentAgent**: Analyzes emotional tone with 80-90% accuracy
- **IntentAgent**: Classifies user intentions with LLM intelligence
- **WebAgent**: Gathers real-time information from multiple sources
- **RefinerAgent**: Generates contextual, empathetic responses
- **SelfReflectionAgent**: Provides meta-cognitive insights
- **BigHeadAgent**: Orchestrates the entire workflow

### 🦙 **Local LLM Integration**
- **Ollama Support**: Complete privacy with local processing
- **No API Costs**: Cost-free operation with local models
- **Fallback Systems**: Graceful degradation to traditional methods
- **Configurable Models**: Support for various Ollama models

## 📁 Project Structure

```
esb_chatbot/
├── src/                    # Source code
│   ├── agents/            # Agent implementations
│   │   ├── sentiment_agent.py
│   │   ├── intent_agent.py
│   │   ├── web_agent.py
│   │   ├── refiner_agent.py
│   │   ├── self_reflection_agent.py
│   │   └── bighead_agent.py
│   ├── core/              # Core functionality
│   │   ├── models.py      # Data models
│   │   ├── config.py      # Configuration
│   │   └── database.py    # Database management
│   ├── analyzers/         # Analysis tools
│   │   └── sentiment_analyzer.py
│   ├── web/               # Web interface
│   │   ├── web_interface.py
│   │   └── templates/
│   └── utils/             # Utilities
│       └── logging_config.py
├── tests/                 # Test suite
├── docs/                  # Documentation
├── data/                  # Database and logs
├── main.py               # Entry point
├── requirements.txt      # Dependencies
└── setup.py             # Installation script
```

## 🚀 Quick Start

### 1. **Installation**

```bash
# Clone the repository
git clone <repository-url>
cd esb_chatbot

# Install dependencies
pip install -r requirements.txt

# Optional: Install Ollama for local LLM support
# Follow instructions at: https://ollama.ai/
```

### 2. **Setup Ollama (Optional but Recommended)**

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model (e.g., llama3.1:8b)
ollama pull llama3.1:8b

# Start Ollama service
ollama serve
```

### 3. **Run the System**

```bash
# Start the chatbot system
python main.py
```

Open your browser to `http://localhost:5000` to access the web interface.

## 🔧 Configuration

The system uses environment variables and configuration files:

```python
# Core settings
OLLAMA_MODEL = "llama3.1:8b"
OLLAMA_BASE_URL = "http://localhost:11434"
DATABASE_URL = "sqlite:///data/esb_chatbot.db"
LOG_LEVEL = "INFO"
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python tests/test_sentiment_agent.py
python tests/test_multi_agent_system.py
```

## 📊 Performance

- **Sentiment Analysis**: 80-90% accuracy with hybrid approach
- **Intent Classification**: 90% accuracy with LLM enhancement
- **Response Time**: 15-30 seconds for LLM analysis (local processing)
- **Fallback Speed**: <1 second for traditional methods

## 🎯 Use Cases

### **Student Support**
- Registration assistance with step-by-step guidance
- Academic support for struggling students
- Career guidance with actionable recommendations
- Emotional support with empathetic responses

### **Information Services**
- Campus facility information
- Course and schedule inquiries
- Document requests and procedures
- Event and activity updates

## 🛠️ Development

### **Adding New Agents**
1. Create agent class in `src/agents/`
2. Implement ReAct pattern (Reason → Act → Observe)
3. Add to agent registry in `__init__.py`
4. Update web interface integration

### **Extending Analysis**
1. Add new analyzers in `src/analyzers/`
2. Implement base analyzer interface
3. Update hybrid analyzer configuration
4. Add corresponding tests

## 📈 Monitoring

The system includes comprehensive logging and monitoring:

- **Agent Performance**: Processing times and success rates
- **Sentiment Tracking**: Historical sentiment analysis
- **Error Handling**: Graceful fallbacks and error recovery
- **Health Checks**: System status monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request


