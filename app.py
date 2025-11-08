import streamlit as st
import requests
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
import os
import time

# --- ⚠️ CONFIGURATION (Internal IP Target) ---
# THIS IS SET TO YOUR LINUX MACHINE'S IP (192.168.1.192)
RELAYER_IP = "192.168.1.192" 
RELAYER_PORT = 5000
# The URL your Streamlit app will hit
RELAYER_URL = f"http://{RELAYER_IP}:{RELAYER_PORT}/authorize_claim"
# -------------------------


# --- Session State Initialization ---
if "compromised" not in st.session_state:
    st.session_state.compromised = "0x0000000000000000000000000000000000000001"
if "safe" not in st.session_state:
    st.session_state.safe = "0xAC27cDF7a352646b164261Ce0C043e22b6A0de89"
if "signature" not in st.session_state:
    st.session_state.signature = ""
if "verified" not in st.session_state:
    st.session_state.verified = False
if "tx_hash" not in st.session_state:
    st.session_state.tx_hash = None


# --- Helper Functions ---

def generate_and_sign_message(compromised_key):
    """
    1. Generates a message that details the recovery claim.
    2. Signs the message using the private key of the compromised wallet.
    3. Verifies the signature to confirm the private key is correct.
    """
    
    # 1. Generate the Claim Message
    claim_message = (
        f"I, the owner of {st.session_state.compromised}, "
        f"authorize the transfer of all funds to the safe wallet "
        f"{st.session_state.safe} using the Relayer service. "
        f"Timestamp: {int(time.time())}"
    )

    try:
        # Check if the private key format is correct
        if not Web3.is_checksum_address(st.session_state.compromised):
            if st.session_state.compromised.lower() == "0x0000000000000000000000000000000000000001":
                pass
            else:
                raise ValueError("Compromised address is not a valid Ethereum address.")
        
        # 2. Sign the Message
        private_key_bytes = bytes.fromhex(compromised_key.replace('0x', ''))
        account = Account.from_key(private_key_bytes)
        
        # Encode and sign the message
        message_to_sign = encode_defunct(text=claim_message)
        signed_message = account.sign_message(message_to_sign)
        
        st.session_state.signature = signed_message.signature.hex()
        
        # 3. Client-side Verification (sanity check)
        recovered_address = Account.recover_message(
            message_to_sign, 
            signature=st.session_state.signature
        )
        
        if recovered_address.lower() == st.session_state.compromised.lower():
            st.session_state.verified = True
            st.success(f"✅ Message Signed and Verified. Signature: {st.session_state.signature[:10]}...")
            st.session_state.claim_message = claim_message
        else:
            st.session_state.verified = False
            st.error("❌ Signature Verification Failed! Private key is invalid for this wallet address.")

    except ValueError as e:
        st.error(f"❌ Error: Invalid private key or address format. {e}")
        st.session_state.verified = False
    except Exception as e:
        st.error(f"❌ An unexpected error occurred during signing: {e}")
        st.session_state.verified = False


def authorize_claim_handler():
    """
    Sends the signed payload to the Relayer service for transaction execution.
    Includes robust error handling and debug logging.
    """
    if not st.session_state.verified:
        st.error("Please sign the claim message first.")
        return

    # Mock contract address 
    MOCK_CONTRACT_ADDR = "0xMockWrapperContractAddress"

    # Construct the payload
    payload = {
        "signature": st.session_state.signature,
        "compromised_wallet": st.session_state.compromised,
        "safe_wallet": st.session_state.safe,
        "claim_message": st.session_state.claim_message,
        "contract_addr": MOCK_CONTRACT_ADDR
    }

    # ----------------------------------------------------
    # CRITICAL DEBUGGING LOGGING 
    # ----------------------------------------------------
    print("\n==================================================")
    print("DEBUG: Sending Request to Relayer")
    print(f"URL: {RELAYER_URL}")
    print(f"PAYLOAD: {payload}")
    print("==================================================")
    
    try:
        response = requests.post(
            RELAYER_URL, 
            json=payload, 
            timeout=30 
        )
        
        response.raise_for_status() 
        result = response.json()
        
        if result.get("status") == "success":
            st.session_state.tx_hash = result.get("tx_hash")
            st.success(f"🎉 Recovery Authorized! Transaction Sent.")
            st.info(f"Mock Transaction Hash: {st.session_state.tx_hash}")
            st.balloons()
        else:
            st.error(f"❌ Relayer Error: {result.get('message', 'Unknown error.')}")
            print(f"RELAYER APP ERROR: {result.get('message', 'Unknown error.')}")

    except requests.exceptions.ConnectionError as e:
        st.error(f"❌ Connection Error: Could not reach the Relayer server at {RELAYER_URL}. ({e})")
        print(f"FATAL REQUEST ERROR (ConnectionError): {e}")
    
    except requests.exceptions.HTTPError as e:
        try:
            error_details = response.json().get("message", "No details provided.")
        except:
            error_details = f"HTTP Status Code {response.status_code}"
            
        st.error(f"❌ HTTP Error: Failed to process claim. Details: {error_details}")
        print(f"HTTP ERROR: {e}. Details: {error_details}")

    except requests.exceptions.RequestException as e:
        st.error(f"❌ General Request Error: Failed to process claim. {e}")
        print(f"GENERAL REQUEST ERROR: {e}")
        
    except Exception as e:
        st.error(f"❌ An unexpected error occurred on the client side: {e}")
        print(f"UNEXPECTED CLIENT ERROR: {e}")


# --- Streamlit UI ---

st.set_page_config(page_title="Relayer Recovery Client", layout="wide")

st.title("🛡️ Compromised Wallet Recovery Client")
st.markdown("Use this interface to authorize the Relayer to execute an atomic fund recovery transaction.")

st.subheader("1. Setup")

# Input for compromised wallet's private key
compromised_key = st.text_input(
    "Compromised Wallet's Private Key (Keep Secret)",
    type="password",
    help="The private key of the wallet that has been compromised. Used ONLY for signing the authorization message locally."
)

st.text_input(
    "Compromised Wallet Address (Sender)",
    value=st.session_state.compromised,
    key="compromised",
    help="The address associated with the private key above."
)

st.text_input(
    "Safe Wallet Address (Recipient)",
    value=st.session_state.safe,
    key="safe",
    help="The secure address where funds will be transferred."
)

# Button to sign the message
if st.button("Generate & Sign Claim Message", disabled=not compromised_key):
    generate_and_sign_message(compromised_key)

st.divider()
st.subheader("2. Authorize Recovery")

# Show the Relayer status check
st.markdown(f"**Relayer Target:** `http://{RELAYER_IP}:{RELAYER_PORT}/authorize_claim`")

# Button to send the request to the Relayer
if st.button("AUTHORIZE RECOVERY CLAIM", type="primary", disabled=not st.session_state.verified):
    authorize_claim_handler()

# Display results
if st.session_state.tx_hash:
    st.success(f"Final Status: Transaction successfully sent to the network.")
    st.code(f"TX HASH: {st.session_state.tx_hash}", language="markdown")
