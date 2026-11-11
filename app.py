import os
import sys

# Ensure virtual environment site-packages are accessible
venv_site_packages = os.path.join(os.path.dirname(__file__), 'venv', 'Lib', 'site-packages')
if os.path.exists(venv_site_packages) and venv_site_packages not in sys.path:
    sys.path.insert(0, venv_site_packages)

# Fix for pandas/numpy on some environments
if not hasattr(os, 'add_dll_directory'):
    os.add_dll_directory = lambda x: None

from flask import Flask, render_template, request, jsonify
import pandas as pd
from datetime import datetime
import re

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSACTIONS_FILE = os.path.join(BASE_DIR, 'transactions.csv')
TICKETS_FILE = os.path.join(BASE_DIR, 'tickets.csv')

def load_transactions():
    try:
        if os.path.exists(TRANSACTIONS_FILE):
            return pd.read_csv(TRANSACTIONS_FILE)
    except Exception as e:
        print(f"Error loading transactions: {e}")
    return pd.DataFrame(columns=['transaction_id', 'status', 'amount', 'date', 'error_code', 'recipient', 'category', 'payment_mode'])

def load_tickets():
    try:
        if os.path.exists(TICKETS_FILE):
            return pd.read_csv(TICKETS_FILE)
    except Exception as e:
        print(f"Error loading tickets: {e}")
    return pd.DataFrame(columns=['ticket_id', 'transaction_id', 'issue_type', 'status', 'created_at', 'description'])

def save_ticket(transaction_id, issue_type, description="Dispute raised via chatbot"):
    df = load_tickets()
    new_id = f"TKT{9001 + len(df)}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_row = {
        'ticket_id': new_id,
        'transaction_id': transaction_id if transaction_id else 'N/A',
        'issue_type': issue_type,
        'status': 'Open',
        'created_at': timestamp,
        'description': description
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(TICKETS_FILE, index=False)
    return new_id

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json or {}
    user_message = data.get('message', '').strip()
    bot_response = get_bot_response(user_message)
    return jsonify({'response': bot_response})

@app.route('/api/tickets', methods=['POST'])
def api_create_ticket():
    data = request.json or {}
    txn_id = data.get('transaction_id', '').strip().upper()
    issue_type = data.get('issue_type', 'General Issue').strip()
    description = data.get('description', '').strip()

    if not issue_type:
        return jsonify({'success': False, 'error': 'Issue type is required.'}), 400

    ticket_id = save_ticket(txn_id, issue_type, description)
    return jsonify({
        'success': True,
        'ticket_id': ticket_id,
        'message': f"Support ticket <b>{ticket_id}</b> created successfully! Our support team will resolve it within 24-48 hours."
    })

@app.route('/api/transactions', methods=['GET'])
def api_transactions():
    df = load_transactions()
    return jsonify(df.to_dict(orient='records'))

def get_bot_response(msg):
    msg_lower = msg.lower()
    df = load_transactions()
    tickets_df = load_tickets()

    # Extract TXN ID if present
    txn_match = re.search(r'\b(TXN\d+)\b', msg, re.IGNORECASE)
    txn_id = txn_match.group(1).upper() if txn_match else None

    # Extract TKT ID if present
    tkt_match = re.search(r'\b(TKT\d+)\b', msg, re.IGNORECASE)
    tkt_id = tkt_match.group(1).upper() if tkt_match else None

    # Intent 1: Greetings
    if any(w in msg_lower for w in ['hi', 'hello', 'hey', 'start', 'good morning', 'good evening']):
        return (
            "👋 Hello! Welcome to **PhonePe Support**. I am your AI assistant.<br><br>"
            "How can I help you today? You can ask me about:<br>"
            "• Checking transaction status (e.g., <i>'Status of TXN1002'</i>)<br>"
            "• Failed transactions & refund timelines<br>"
            "• Raising a support ticket or dispute<br>"
            "• Resetting your UPI PIN<br>"
            "• Wallet, cashback & bill payment issues"
        )

    # Intent 2: Check Ticket Status
    elif 'ticket' in msg_lower or tkt_id:
        if tkt_id:
            if tickets_df.empty:
                return "❌ No support tickets found in our system."
            result = tickets_df[tickets_df['ticket_id'] == tkt_id]
            if not result.empty:
                row = result.iloc[0]
                badge_color = "orange" if row['status'] == 'Open' else ('blue' if row['status'] == 'In Progress' else 'green')
                return (
                    f"🎫 **Support Ticket Details ({tkt_id}):**<br>"
                    f"• Associated TXN: <b>{row['transaction_id']}</b><br>"
                    f"• Issue: {row['issue_type']}<br>"
                    f"• Status: <span style='color:{badge_color}; font-weight:bold;'>{row['status']}</span><br>"
                    f"• Created: {row['created_at']}<br>"
                    f"• Description: {row['description']}"
                )
            else:
                return f"❌ No support ticket found with ID <b>{tkt_id}</b>."
        else:
            if tickets_df.empty:
                return "You have no active support tickets."
            recent_tickets = tickets_df.tail(3)
            html = "📋 **Your Recent Support Tickets:**<br>"
            for _, row in recent_tickets.iterrows():
                html += f"• <b>{row['ticket_id']}</b> ({row['transaction_id']}) - Status: <b>{row['status']}</b><br>"
                html += f"  <i>{row['issue_type']}</i><br>"
            html += "<br>Type <code>check ticket TKT9001</code> for details."
            return html

    # Intent 3: Raise Ticket / Dispute
    elif 'raise' in msg_lower or 'dispute' in msg_lower or 'complaint' in msg_lower or 'file' in msg_lower:
        target_txn = txn_id if txn_id else "TXN1002"
        tkt = save_ticket(target_txn, "Transaction Dispute / Failed Payment", f"User requested dispute resolution for {target_txn}")
        return (
            f"✅ **Support Ticket Created Successfully!**<br>"
            f"• Ticket ID: <b>{tkt}</b><br>"
            f"• Reference TXN: <b>{target_txn}</b><br>"
            f"• Status: <b>Open</b><br>"
            f"Our support team will investigate and update you within 24-48 hours."
        )

    # Intent 4: Check Transaction Status
    elif 'status' in msg_lower or 'check' in msg_lower or 'txn' in msg_lower or txn_id:
        if not txn_id:
            # If no TXN ID given, show recent transactions list
            if df.empty:
                return "Sorry, our transaction database is currently empty."
            html = "📋 **Recent Transactions:**<br>Please select a transaction to check status:<br>"
            for _, row in df.iterrows():
                status_icon = "🟢" if row['status'] == 'Success' else ("🔴" if row['status'] == 'Failed' else "🟡")
                html += f"• {status_icon} <b>{row['transaction_id']}</b>: ₹{row['amount']} ({row['recipient']}) - <i>{row['status']}</i><br>"
            html += "<br>Type e.g. <code>status TXN1002</code> for detailed info."
            return html

        if df.empty:
            return "Sorry, our transaction database is currently empty."

        result = df[df['transaction_id'] == txn_id]
        if not result.empty:
            row = result.iloc[0]
            status_color = "green" if row['status'] == 'Success' else ("red" if row['status'] == 'Failed' else "orange")
            error_info = f"<br>• Error Code: <b>{row['error_code']}</b>" if row['error_code'] != 'None' else ""
            return (
                f"📋 **Transaction Details for {txn_id}:**<br>"
                f"• Status: <span style='color:{status_color}; font-weight:bold;'>{row['status']}</span><br>"
                f"• Amount: <b>₹{row['amount']}</b><br>"
                f"• Recipient: {row['recipient']}<br>"
                f"• Category: {row['category']}<br>"
                f"• Payment Mode: {row['payment_mode']}<br>"
                f"• Date: {row['date']}"
                f"{error_info}<br><br>"
                f"💡 Need help with this? Type <code>raise ticket for {txn_id}</code> to file a dispute."
            )
        else:
            return f"❌ No transaction found with ID <b>{txn_id}</b>. Please check your transaction history."

    # Intent 5: Recent Transactions Request
    elif 'recent' in msg_lower or 'history' in msg_lower or 'list' in msg_lower or 'transactions' in msg_lower:
        if df.empty:
            return "No transaction history found."
        html = "📋 **Your Recent Transactions:**<br>"
        for _, row in df.iterrows():
            status_icon = "🟢" if row['status'] == 'Success' else ("🔴" if row['status'] == 'Failed' else "🟡")
            html += f"• {status_icon} <b>{row['transaction_id']}</b>: ₹{row['amount']} to {row['recipient']} (<i>{row['status']}</i>)<br>"
        html += "<br>Type <code>status [TXN_ID]</code> (e.g. <code>status TXN1002</code>) for details."
        return html

    # Intent 6: Transaction Failed / Money Debited / Refund
    elif any(w in msg_lower for w in ['debited', 'failed', 'money cut', 'deducted', 'refund', 'error', 'timeout']):
        return (
            "🔍 **Money Debited but Transaction Failed / Pending:**<br>"
            "If your money was debited but the payment failed or is pending, please note that "
            "**PhonePe automatically processes refunds**:<br><br>"
            "• **UPI Bank Accounts:** Credited back within **3 to 5 business days**.<br>"
            "• **PhonePe Wallet / Gift Card:** Credited back **instantly** (within 24 hours).<br>"
            "• **Credit / Debit Cards:** Credited back within **5 to 7 business days**.<br><br>"
            "To check a specific transaction, type: <code>status TXN1002</code><br>"
            "To report this issue, type: <code>raise dispute</code>"
        )

    # Intent 7: UPI PIN Reset / Forgot PIN
    elif any(w in msg_lower for w in ['pin', 'reset', 'forgot', 'change pin', 'upi pin']):
        return (
            "🔑 **How to Reset or Change Your UPI PIN:**<br>"
            "1. Open **PhonePe** app and tap your **Profile Picture** (top-left corner).<br>"
            "2. Under the **Payment Methods** section, tap your bank account.<br>"
            "3. Click **Reset** or **Change** next to UPI PIN.<br>"
            "4. Enter the **last 6 digits of your Debit/ATM card** and the expiry date.<br>"
            "5. Enter the OTP received from your bank and set your new 4 or 6-digit UPI PIN.<br><br>"
            "⚠️ *Note: Never share your UPI PIN or ATM card details with anyone, including PhonePe support.*"
        )

    # Intent 8: Bank Account / Limits
    elif any(w in msg_lower for w in ['bank', 'add bank', 'limit', 'balance', 'transfer']):
        return (
            "🏦 **Bank Account & Limits Help:**<br>"
            "• **Add Bank Account:** Go to Profile -> Bank Accounts -> Add New Bank Account.<br>"
            "• **Check Balance:** Go to Check Bank Balance -> Select Bank -> Enter UPI PIN.<br>"
            "• **UPI Daily Limit:** Most banks allow up to ₹1 Lakh per day across UPI apps.<br>"
            "• **Primary Bank Account:** Tap your preferred bank in Profile and set as default for receiving money."
        )

    # Intent 9: Wallet & Cashback / Scratch Cards
    elif any(w in msg_lower for w in ['wallet', 'cashback', 'scratch', 'reward', 'gift']):
        return (
            "🎁 **Wallet & Rewards Help:**<br>"
            "• **PhonePe Wallet:** Top-up via linked bank account. Fully KYC required for balance above ₹10,000.<br>"
            "• **Scratch Cards & Cashback:** Scratch cards are credited directly to your PhonePe Gift Card balance or linked primary bank account within 3 working days."
        )

    # Intent 10: Fraud / Security / Scam
    elif any(w in msg_lower for w in ['fraud', 'scam', 'unauthorized', 'block', 'hack']):
        return (
            "🛡️ **Report Fraud & Secure Account:**<br>"
            "If you suspect unauthorized activity or fraud:<br>"
            "1. Immediately call the National Cyber Crime Helpline: <b>1930</b>.<br>"
            "2. Block your UPI ID and linked bank cards via your bank's app.<br>"
            "3. Contact PhonePe Support via Help section or raise an urgent ticket here by typing <code>raise dispute</code>.<br><br>"
            "🔒 *Security Reminder: PhonePe representatives will NEVER ask for your UPI PIN, OTP, or screen-sharing access.*"
        )

    # Default Fallback
    else:
        return (
            "I'm here to help with all your PhonePe queries! You can ask me about:<br>"
            "• Checking transaction status (e.g. <code>status TXN1002</code>)<br>"
            "• Failed transactions & refund timelines<br>"
            "• Raising a support ticket / dispute<br>"
            "• Resetting UPI PIN & bank linking<br>"
            "• Cashback, wallet & security help"
        )

if __name__ == '__main__':
    app.run(debug=True, port=5000)
