# 🧾 Invoice Agent

An AI-powered invoice management system built with Google Gemini and Stripe integration. This intelligent agent helps you create invoices, manage customers, and handle billing operations using natural language commands.

## ✨ Features

- 🤖 **AI-Powered**: Uses Google Gemini for natural language processing
- 💳 **Stripe Integration**: Complete invoice and customer management
- 💱 **INR Support**: Default currency set to Indian Rupees (₹)
- 🔄 **Real-time Chat**: WebSocket-based communication
- 🎨 **Modern UI**: Streamlit-based frontend with chat interface
- 🔐 **Secure API**: API key authentication
- ⚡ **Fast Setup**: Built with uv for rapid dependency management

## 🛠 Built With

- **Python 3.13+**
- **FastAPI** - Backend API framework
- **Streamlit** - Frontend chat interface
- **Google Gemini AI** - Natural language processing
- **Stripe** - Payment and invoice management
- **WebSockets** - Real-time communication
- **uv** - Ultra-fast Python package installer and resolver

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- Google Gemini API key
- Stripe API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd "Invoice Agent"
   ```

2. **Install dependencies with uv**
   ```bash
   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install dependencies
   uv pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your API keys:
   ```env
   GOOGLE_API_KEY=your_google_gemini_api_key_here
   STRIPE_API_KEY=your_stripe_secret_key_here
   API_KEY=your_custom_api_key_here
   ```

4. **Run the backend**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Run the frontend (in a new terminal)**
   ```bash
   streamlit run frontend.py --server.port 8501
   ```

## 📖 Usage

### Natural Language Commands

The AI agent understands natural language commands for invoice operations:

- **Create Customer**: "Create a customer with email john@example.com and name John Doe"
- **Create Invoice**: "Create an invoice for customer cus_abc123 for ₹5000 for consulting services"
- **List Invoices**: "Show me all invoices" or "List invoices for customer cus_abc123"

### API Endpoints

#### REST API

- `GET /` - Health check (requires API key)
- `POST /clear-chat` - Clear conversation history
- `WebSocket /ws/chat` - Real-time chat interface

#### Example API Usage

```bash
# Health check
curl -H "X-API-Key: your_api_key" http://localhost:8000/

# WebSocket connection for chat
# Use the Streamlit frontend or connect via WebSocket client
```

### Streamlit Frontend

1. Open your browser to `http://localhost:8501`
2. Start chatting with the AI agent
3. Use natural language to manage invoices and customers

## 🏗 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │    FastAPI      │    │   Google        │
│   Frontend      │◄──►│    Backend      │◄──►│   Gemini AI     │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │     Stripe      │
                       │      API        │
                       └─────────────────┘
```

## 📁 Project Structure

```
Invoice Agent/
├── main.py                 # FastAPI backend with Gemini integration
├── frontend.py             # Streamlit chat interface
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .env                   # Your environment variables (gitignored)
├── README.md              # This file
└── PDFs/                  # Sample invoice PDFs
    ├── Invoice-JNYJTTEV-0001.pdf
    └── Invoice-QW1MGQIR-0001.pdf
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key | ✅ |
| `STRIPE_API_KEY` | Stripe secret key | ✅ |
| `API_KEY` | Custom API key for authentication | ✅ |
| `LOG_LEVEL` | Logging level (default: info) | ❌ |
| `ENVIRONMENT` | Environment (default: production) | ❌ |

### Currency Settings

The system defaults to INR (Indian Rupees). To change the default currency, modify the `create_invoice` function in `main.py`.

## 🧪 Testing

### Test the Backend API

```bash
# Health check
curl -H "X-API-Key: your_api_key" http://localhost:8000/

# Clear chat history
curl -X POST -H "X-API-Key: your_api_key" http://localhost:8000/clear-chat
```

### Test with Streamlit

1. Run both backend and frontend
2. Open `http://localhost:8501`
3. Try commands like:
   - "Create a customer with email test@example.com"
   - "Create an invoice for ₹1000"
   - "Show me all invoices"

## 🔍 Stripe Dashboard

To view created invoices and customers:

1. Log in to your [Stripe Dashboard](https://dashboard.stripe.com/)
2. Navigate to **Customers** to see created customers
3. Navigate to **Invoices** to see generated invoices
4. Use test mode for development

## 🚨 Troubleshooting

### Common Issues

1. **"Module not found" errors**
   ```bash
   uv pip install -r requirements.txt
   ```

2. **API key errors**
   - Check your `.env` file has correct API keys
   - Ensure environment variables are loaded

3. **Stripe connection issues**
   - Verify your Stripe API key is valid
   - Check if you're using the correct key (test vs live)

4. **Port already in use**
   ```bash
   # Find process using port 8000
   lsof -ti:8000 | xargs kill -9
   
   # Or use different port
   uvicorn main:app --port 8001
   ```

### Debug Mode

Run with debug logging:
```bash
LOG_LEVEL=debug uvicorn main:app --reload
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.