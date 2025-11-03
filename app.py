import streamlit as st
import requests
import time
import json
from eth_account.messages import encode_defunct
from web3 import Web3
# To run this script locally: 
# pip install streamlit requests eth-account web3

# ===================================================================
# 1. CONFIGURATION (PUBLIC CONSTANTS)
# ===================================================================

# WARNING: Replace these with the real contract addresses for the airdrop
AIRDROP_CONTRACT_ADDRESS = "0xMockAirdropContractAddress" # The official contract address
TOKEN_ADDRESS = "0xMockTokenContractAddress"         # The token being claimed (e.g., UNI, OP)
SAFE_DESTINATION_ADDRESS = "0xec451d6a06741e86e5ff0f9e5cc98d3388480c7a" # Wallet B from the executor script

# This is the secure, private API endpoint that triggers your Node.js Flashbots executor
# This API should be protected by a shared secret or IP whitelist on your server.
PRIVATE_EXECUTION_API_URL = "https://api.airdrop-shield.com/v1/execute-claim"

# ===================================================================
# 2. CRYPTO HELPER FUNCTIONS (Simplified for Streamlit)
# ===================================================================

# Mock ABI for the Airdrop Contract's claim function
# NOTE: This must match the actual claim function signature of the target airdrop.
AIRDROP_CLAIM_ABI = {
    "name": "claimTokens",
    "type": "function",
    "inputs": [
        {"name": "recipient", "type": "address"},
        {"name": "amount", "type": "uint256"},
        # Add any other required parameters (e.g., Merkle proof, timestamp)
    ]
}

def generate_claim_calldata(recipient_address, claim_amount):
    """
    Simulates the ABI-encoding of the claim function call.
    In a real app, this might use a Merkle proof fetched off-chain.
    """
    w3 = Web3() # Dummy Web3 instance for encoding
    
    # We assume the claim function requires the address and amount
    claim_calldata = w3.eth.contract().encodeABI(
        fn_name=AIRDROP_CLAIM_ABI['name'],
        args=[
            recipient_address,
            claim_amount
        ]
    )
    return claim_calldata


def verify_signature(message_hash, signature, expected_address):
    """
    Verifies the user's signature against the expected address.
    """
    try:
        w3 = Web3()
        # 1. Convert the message hash (bytes32) into the signed message object (EIP-191)
        message = encode_defunct(hexstr=message_hash)
        
        # 2. Recover the signer address
        recovered_address = w3.eth.account.recover_message(message, signature=signature)
        
        # 3. Compare recovered address to the expected (compromised) address
        return recovered_address.lower() == expected_address.lower()
    except Exception as e:
        st.error(f"Signature Verification Error: {e}")
        return False

# ===================================================================
# 3. STREAMLIT UI COMPONENTS
# ===================================================================

st.set_page_config(
    page_title="Airdrop Shield: Secure Claim",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("🛡️ Airdrop Shield: Secure Atomic Claim")
st.markdown("Use your compromised wallet (Wallet A) to sign a rescue message. We will use the signature to execute an **atomic claim and sweep** of your funds via Flashbots, protecting you from the sweeper bot.")

# --- Session State Management ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'claim_data' not in st.session_state:
    st.session_state.claim_data = {}


def next_step():
    st.session_state.step += 1
    
def reset_app():
    st.session_state.step = 1
    st.session_state.claim_data = {}

# --- Step 1: Wallet Input & Eligibility Check ---

if st.session_state.step == 1:
    st.subheader("Step 1: Enter Compromised Wallet (Wallet A)")
    
    # In a production app, this would be auto-filled by a Web3 wallet connector
    compromised_address = st.text_input(
        "Wallet A Address (Compromised)",
        value="0x9538bfa699f9c2058f32439de547a054a9ceeb5c",
        max_chars=42,
        key="compromised_address"
    )

    if st.button("Check Eligibility", type="primary"):
        if not Web3.is_address(compromised_address):
            st.error("Please enter a valid Ethereum address.")
        else:
            with st.spinner(f"Checking eligibility for {compromised_address}..."):
                time.sleep(1.5) # Simulate network call

                # --- MOCK ELIGIBILITY RESPONSE ---
                # In a real app, this reads the Airdrop contract (read-only call)
                
                # Check 1: Is the address eligible?
                is_eligible = True # MOCK: Assume eligible for now

                # Check 2: What is the claimable amount?
                CLAIMABLE_AMOUNT_WEI = 10_000_000_000_000_000_000 # MOCK: 10 Tokens (10**18)
                
                if not is_eligible:
                    st.error("This address is not eligible for the airdrop or has already claimed.")
                elif CLAIMABLE_AMOUNT_WEI == 0:
                    st.warning("This address is eligible, but the claimable amount is zero.")
                else:
                    # Success: Proceed to calldata generation
                    
                    # Generate the calldata needed for the ClaimProxy to call the Airdrop Contract
                    calldata = generate_claim_calldata(compromised_address, CLAIMABLE_AMOUNT_WEI)
                    
                    # Generate the unique message hash (bytes32) for the signature
                    # This must match the MESSAGE_HASH passed into ClaimProxy.sol
                    message_content = f"Securely authorize atomic claim for {compromised_address}"
                    message_hash = Web3.keccak(text=message_content).hex()

                    st.session_state.claim_data = {
                        "compromised_address": compromised_address,
                        "claim_amount": CLAIMABLE_AMOUNT_WEI,
                        "claim_calldata": calldata,
                        "message_hash": message_hash
                    }

                    st.success(f"✅ Eligible to claim {Web3.from_wei(CLAIMABLE_AMOUNT_WEI, 'ether')} tokens!")
                    next_step()

# --- Step 2: Signature Request ---

if st.session_state.step == 2:
    data = st.session_state.claim_data
    st.subheader("Step 2: Sign the Rescue Message")
    st.warning("⚠️ **IMPORTANT:** Use your **Compromised Wallet (Wallet A)** to sign this exact message hash. This signature is the only thing we need—no transaction fees are paid here.")
    
    st.markdown("### Message Hash to Sign (Bytes32)")
    st.code(data['message_hash'], language="text")

    st.markdown("---")
    
    signature = st.text_input(
        "Paste Signature (V-R-S format, 65 bytes hex)",
        key="user_signature",
        max_chars=132
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("Verify & Execute Sweep", type="primary", use_container_width=True):
            if not signature or len(signature) != 132 or not signature.startswith("0x"):
                st.error("Signature must be a 0x-prefixed 65-byte hex string (132 characters long).")
            else:
                if verify_signature(data['message_hash'], signature, data['compromised_address']):
                    st.session_state.claim_data['signature'] = signature
                    next_step()
                else:
                    st.error("Signature verification failed. Please ensure you are using the correct wallet and message.")

    with col2:
        st.button("Back to Start", on_click=reset_app, use_container_width=True)


# --- Step 3: Trigger Private Execution Backend ---

if st.session_state.step == 3:
    data = st.session_state.claim_data
    st.subheader("Step 3: Initiating Atomic Flashbots Sweep...")
    st.info(f"The signed authorization from **{data['compromised_address'][:6]}...{data['compromised_address'][-4:]}** is verified.")
    
    # Final Payload Construction
    payload = {
        # Contract Deployment Parameters
        "compromisedAddress": data['compromised_address'],
        "safeDestinationAddress": SAFE_DESTINATION_ADDRESS,
        "tokenAddress": TOKEN_ADDRESS,
        "messageHash": data['message_hash'],
        
        # Execution Parameters
        "signature": data['signature'],
        "airdropContractAddress": AIRDROP_CONTRACT_ADDRESS,
        "claimCalldata": data['claim_calldata'],
    }
    
    st.json(payload) # Show the data being sent to the secure backend
    
    if st.button("Trigger Flashbots Execution Now", type="primary"):
        with st.spinner("🚀 Sending signal to private executor... Waiting for Flashbots confirmation..."):
            
            # --- MOCK API CALL TO PRIVATE BACKEND ---
            time.sleep(2) # Simulate request latency
            
            # NOTE: In a real environment, you would use 'requests.post' here.
            # response = requests.post(PRIVATE_EXECUTION_API_URL, json=payload, headers={"X-AUTH-SECRET": "YOUR_SHARED_SECRET"})
            
            # Mock successful response from the secure server
            success_mock = True
            if success_mock:
                mock_tx_hash = "0x" + "a" * 64
                
                st.balloons()
                st.success("🎉 **SUCCESS!** The secure signal was received, and the Flashbots bundle was successfully sent.")
                st.markdown(f"""
                ### Recovery Initiated!
                The atomic sweep is being executed via Flashbots. If successful, your funds are safe!
                
                **Compromised Wallet (Wallet A):** `{data['compromised_address']}`
                
                **Safe Destination (Wallet B):** `{SAFE_DESTINATION_ADDRESS}`
                
                **Mock Execution Hash:** `{mock_tx_hash}`
                
                **Monitor your Safe Wallet (Wallet B) for the incoming tokens.**
                """)
            else:
                st.error("Execution failed! Check the private executor logs for details.")

    st.button("Restart Process", on_click=reset_app)
