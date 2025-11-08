from flask import Flask, request, jsonify
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
import requests as http_requests
import time
import secrets
import sys

# --- ⚠️ CONFIGURATION (Ensure keys are correct) ⚠️ ---
RPC_URL = "https://sepolia.infura.io/v3/ebd83b4a3f284fecb5be8f0d0a8d0978" 
RELAYER_PRIVATE_KEY = "b436236bb62bea7298ba422d4d7199075c1bbda3d6875cf751d10beb736712c9" 
FEE_WALLET_ADDRESS = "0xAC27cDF7a352646b164261Ce0C043e22b6A0de89" 
# -----------------------------------------------------------

app = Flask(__name__)

# GLOBAL INITIALIZATION
# NOTE: We keep this simple. If this crashes, the server won't start, which is intended.
print("--- Initializing Web3 and Account ---")
try:
    # Initialization relies on the updated keys being valid
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    RELAYER_ACCOUNT = Account.from_key(RELAYER_PRIVATE_KEY)
    RELAYER_ADDRESS = RELAYER_ACCOUNT.address
    print(f"RELAYER ADDRESS: {RELAYER_ADDRESS}")
    # ⚠️ REMOVED: print(f"RPC Status: {'Connected' if w3.is_connected() else 'PENDING/FAIL'}")
    print(f"RPC Status: Initialization Complete (check skipped for speed)")
except Exception as e:
    print(f"FATAL STARTUP ERROR: {e}")
    sys.exit(1) # Exit if initialization fails

# -------------------------------------------------------------------
# HELPER FUNCTION: MOCK EXECUTION (Guaranteed to run fast)
# -------------------------------------------------------------------
def execute_atomic_claim(payload):
    """
    TEMPORARY MOCK: Bypasses all blockchain logic to confirm API success.
    """
    print("LOG: [Execute Mock] Starting mock execution.")
    # Simulate network latency (1 second is fast enough)
    time.sleep(1) 
    
    # Return a mocked TX hash 
    mock_tx_hash = f"0xMockSuccess{secrets.token_hex(28)}"
    print(f"LOG: [Execute Mock] Completed mock, returning {mock_tx_hash}")
    return mock_tx_hash


# -------------------------------------------------------------------
# THE MAIN API ENDPOINT
# -------------------------------------------------------------------
@app.route('/authorize_claim', methods=['POST'])
def handle_claim_request():
    # CRITICAL LOGGING: Confirm the function was entered
    print("\n---------------------------------------------------")
    print("LOG: [API Request] Received request from client.")

    # 1. Check for valid JSON input
    if not request.json:
        print("LOG: [API Request] Rejected: Missing JSON payload (400)")
        return jsonify({"status": "error", "message": "Missing JSON payload"}), 400

    data = request.json
    required_fields = ["signature", "compromised_wallet", "safe_wallet", "claim_message", "contract_addr"]

    if not all(field in data for field in required_fields):
        print("LOG: [API Request] Rejected: Missing required fields (400)")
        return jsonify({"status": "error", "message": "Missing one or more required fields from the client."}), 400
    
    # 2. Server-side Signature Verification (Security Check)
    try:
        print("LOG: [API Request] Performing signature recovery...")
        # If the recovery hangs, it's likely stuck here.
        recovered_address = Account.recover_message(
            encode_defunct(text=data['claim_message']),
            signature=data['signature']
        )
        
        if recovered_address.lower() != data['compromised_wallet'].lower():
            print("LOG: [API Request] Rejected: Signature invalid (401)")
            return jsonify({"status": "error", "message": "Invalid signature. Failed server-side control check."}), 401
        print("LOG: [API Request] Signature verified successfully.")

    except Exception as e:
        print(f"LOG: [API Request] Rejected: Signature verification failed with error: {str(e)} (400)")
        return jsonify({"status": "error", "message": f"Server signature verification failed: {str(e)}"}), 400

    # 3. Execute Transaction
    try:
        tx_hash = execute_atomic_claim(data)

        print("LOG: [API Request] Sending success response (200)")
        return jsonify({
            "status": "success",
            "message": "Recovery authorized and transaction sent.",
            "tx_hash": tx_hash
        }), 200

    except Exception as e:
        print(f"LOG: [API Request] Rejected: Execution failed with error: {str(e)} (500)")
        return jsonify({"status": "error", "message": f"Transaction execution failed: {str(e)}"}), 500

# -------------------------------------------------------------------
# RUN THE SERVER
# -------------------------------------------------------------------
if __name__ == '__main__':
    print("\n--- Starting Flask Server ---")
    print(f"Relayer listening on http://192.168.1.192:5000 (Internal IP)")
    # Running on 0.0.0.0 allows external connections (from your Windows laptop)
    app.run(host='0.0.0.0', port=5000, debug=False)
