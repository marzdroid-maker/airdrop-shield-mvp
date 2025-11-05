import secrets
import streamlit as st
from eth_account import Account
from eth_account.messages import encode_defunct

# st.cache_data.clear() # Keeping this commented out for better performance
st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️")
st.title("🛡️ Airdrop Shield")

# --- Initialize State ---
if "verified" not in st.session_state:
    st.session_state.verified = False
if "message" not in st.session_state:
    st.session_state.message = None
if "compromised_wallet" not in st.session_state:
    st.session_state.compromised_wallet = None
if "safe_wallet" not in st.session_state:
    st.session_state.safe_wallet = None

# --- Tabs ---
tab1, tab2 = st.tabs(["Verify", "Claim"])

with tab1:
    st.subheader("Step 1: Prove Control")
    # Use the session state values to populate the inputs if they exist
    compromised_input = st.text_input("Compromised wallet (to claim from)", 
                                      value=st.session_state.compromised_wallet or "", 
                                      key="compromised_input", 
                                      placeholder="0x...")
    safe_input = st.text_input("Safe wallet (to send to)", 
                               value=st.session_state.safe_wallet or "", 
                               key="safe_input", 
                               placeholder="0x...")

    # Validate addresses and GENERATE/STABILIZE the message
    if compromised_input.startswith("0x") and len(compromised_input) == 42 and \
       safe_input.startswith("0x") and len(safe_input) == 42:
        
        # KEY STABILITY CHECK: Regenerate the message ONLY if the addresses change 
        # OR if the message hasn't been created yet. This prevents re-signing 
        # with a new nonce if the user simply interacts with the page.
        if st.session_state.compromised_wallet != compromised_input or \
           st.session_state.safe_wallet != safe_input or \
           st.session_state.message is None:
            
            # --- Reset Verification State ---
            st.session_state.verified = False
            # Generate a new unique message for signing
            # NOTE: We use the current input values for the message
            st.session_state.message = f"I control {compromised_input} and authorize recovery to {safe_input} — {secrets.token_hex(8)}"
            
            # Reset persisted wallets to force re-verification if inputs change
            st.session_state.compromised_wallet = None
            st.session_state.safe_wallet = None
            
            # Also reset the signature input field to force a fresh paste
            if 'sig' in st.session_state:
                 st.session_state.sig = ""


        st.code(st.session_state.message)
        st.success("Ready — Click the orange button to sign!")

        # --- MetaMask Signing HTML Component ---
        # The key here is passing the current st.session_state.message into the JS
        st.components.v1.html(f"""
        <style>
            /* CSS for the signature box */
            #sigBox {{
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                width: 90%;
                max-width: 700px;
                height: 180px;
                padding: 16px;
                background: #000;
                color: #0f0;
                border: 4px solid #0f0;
                border-radius: 14px;
                font-family: monospace;
                font-size: 16px;
                z-index: 9999;
                box-shadow: 0 0 30px #0f0;
                display: none;
            }}
            #sigBox.show {{ display: block; }}
        </style>
        <script>
        // JavaScript for MetaMask interaction
        async function go() {{
            const e = window.ethereum || window.top?.ethereum;
            if (!e) return alert("Install MetaMask!");
            try {{
                const [a] = await e.request({{method:'eth_requestAccounts'}});
                // PASSING THE STABLE MESSAGE
                const s = await e.request({{method:'personal_sign', params:['{st.session_state.message}', a]}}); 
                let box = document.getElementById('sigBox');
                if (!box) {{
                    box = document.createElement('textarea');
                    box.id = 'sigBox';
                    box.readOnly = true;
                    document.body.appendChild(box);
                }}
                box.value = s;
                box.classList.add('show');
                box.scrollIntoView({{behavior: 'smooth', block: 'center'}});
            }} catch {{ alert("Please SIGN the message — don't reject!"); }}
        }}
        </script>
        <div style="text-align:center; margin:40px 0;">
            <button onclick="go()" 
                    style="background:#f6851b;color:white;padding:28px 100px;border:none;
                           border-radius:20px;font-size:38px;font-weight:bold;cursor:pointer;
                           box-shadow:0 15px 60px #f6851b88;">
                1-CLICK SIGN
            </button>
            <p><b>Green box will pop up at the bottom after signing</b></p>
        </div>
        """, height=300)

        sig = st.text_input("PASTE SIGNATURE HERE", key="sig", placeholder="Ctrl+V from GREEN BOX")

        if st.button("VERIFY SIGNATURE", type="primary"):
            if not sig:
                st.error("Please paste the signature first.")
            elif st.session_state.message is None:
                st.error("Message has not been generated. Please check wallet inputs.")
            else:
                try:
                    # Recovery uses the message from session state
                    recovered_address = Account.recover_message(
                        encode_defunct(text=st.session_state.message), 
                        signature=sig
                    )
                    
                    # Comparison uses the current input values
                    if recovered_address.lower() == compromised_input.lower():
                        st.success("🎉 VERIFIED! You now control the Claim tab.")
                        
                        # PERSIST the successful addresses and signature
                        st.session_state.verified = True
                        st.session_state.compromised_wallet = compromised_input
                        st.session_state.safe_wallet = safe_input
                        st.balloons()
                    else:
                        st.error("Signature does not match the Compromised Wallet address. Did you sign with the correct wallet?")
                        st.session_state.verified = False
                except Exception as e:
                    st.error(f"Verification failed. Check the signature is complete. Error: {e}")
                    st.session_state.verified = False
    else:
        st.warning("Enter valid Compromised and Safe wallet addresses (0x...) to start.")


with tab2:
    st.subheader("Step 2: Claim Funds")
    
    if st.session_state.verified:
        st.success(f"✅ Verified! Funds will be claimed from **{st.session_state.compromised_wallet}** and sent to **{st.session_state.safe_wallet}**.")
        
        # Retrieve the message and signature from session state for display
        message_to_send = st.session_state.message
        signature_to_send = st.session_state.sig
        
        st.info("Your signed message (proof of control) and signature for the smart contract:")
        st.code(f"MESSAGE:\n{message_to_send}")
        st.code(f"SIGNATURE:\n{signature_to_send}")

        if st.button("CLAIM ALL AIRDROPS (0 Gas Meta-Transaction)", type="primary"):
            # This is where you would call your smart contract
            tx_hash = "0x" + secrets.token_hex(32) # Mock transaction hash
            st.success(f"CLAIM INITIATED! Transaction is pending on the atomic claim contract.")
            st.code(f"TX Hash: {tx_hash}")
            st.super_balloons()
    else:
        st.warning("⚠️ Go to the **Verify** tab first and successfully verify your compromised wallet.")
