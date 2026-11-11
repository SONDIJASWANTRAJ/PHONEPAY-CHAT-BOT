# PhonePe AI Chatbot Implementation

A fully functional, PhonePe-branded AI-powered support chatbot implementation, featuring automated transaction status lookup, dispute management, FAQ handling, and modern UI.

## Features
- **Transaction Management:** Check status of transactions using Transaction IDs.
- **Support Tickets:** Raise disputes/tickets directly through the chatbot.
- **Knowledge Base:** Handles queries about UPI PINs, Failed Transactions, Wallet, Cashback, and Fraud Reporting.
- **Modern UI:** Responsive, PhonePe-branded interface with quick action chips and rich message rendering.

## Getting Started

### Prerequisites
- Python 3.8+ installed on your Windows machine.
- `pip` for installing dependencies.

### Installation

1. **Clone or Open the folder** containing the chatbot files.
2. **Setup Virtual Environment** (Recommended):
   Open a terminal/command prompt in the project folder:
   ```bash
   python -m venv venv
   ```
3. **Activate Environment & Install Dependencies**:
   ```bash
   # Windows
   venv\Scripts\activate
   pip install flask pandas numpy
   ```

### Executing the Chatbot
1. Ensure your terminal is in the project folder and the virtual environment is activated.
2. Run the application:
   ```bash
   python app.py
   ```
3. Open your browser and navigate to: **http://127.0.0.1:5000/**

## Data Storage
- `transactions.csv`: Contains mock transaction records.
- `tickets.csv`: Stores support tickets and dispute logs.

You can add more data to these CSV files to expand the chatbot's capabilities!
