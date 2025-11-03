import secrets
import streamlit as st
from eth_account import Account
from eth_account.messages import encode_defunct

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Prove you still control your compromised wallet")

# Use session state to manage verification status
if "verified" not in st.session_state:
    st.session_state.verified = False

tab1, tab2 = st.tabs(["Verify", "Claim"])

with tab1:
    st.subheader("Step 1: Prove you control the compromised wallet")
    compromised = st.text_input("Compromised wallet", "0x9538bfa699f9c2058f32439de547a054a9ceeb5c")
    safe = st.text_input("Safe wallet", "0xec451d6a06741e86e5ff0f9e5cc98d3388480c7a")

    # Message Generation Logic
    if compromised.startswith("0x") and safe.startswith("0x") and len(compromised) == 42 and len(safe) == 42:
        if "message" not in st.session_state:
            # Generate a new unique message
            msg = f"I control {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
            st.session_state.message = msg
        
        # Always display the message, even after verification (for auditability)
        st.code(st.session_state.message)
        st.info("Ready: Click the button below to sign this message with your Compromised Wallet.")

    if "message" in st.session_state:
        # Re-engineering the JS to DISPLAY the signature instead of relying on navigator.clipboard
        st.components.v1.html(f"""
        <style>
            .sig-btn {{
                background:#f6851b;color:white;padding:22px 70px;border:none;
                border-radius:16px;font-size:30px;cursor:pointer;font-weight:bold;
                box-shadow:0 10px 40px #f6851b88;
            }}
            .sig-output {{
                display: none; /* Initially hidden */
                width: 100%;
                margin-top: 20px;
                padding: 10px;
                border: 2px solid #00ff00;
                border-radius: 8px;
                background-color: #222;
                color: #00ff00;
                font-family: monospace;
                font-size: 16px;
                text-align: center;
                resize: none;
                cursor: text;
            }}
            .sig-status {{
                margin-top: 10px;
                font-size: 18px;
                color: #eee;
            }}
        </style>
        <script>
        function sign() {{
            const statusDiv = document.getElementById('sig-status');
            const outputArea = document.getElementById('sig-output');
            
            // Clear previous state
            outputArea.style.display = 'none';
            outputArea.value = '';
            statusDiv.innerHTML = '<span style="color:yellow;">Checking wallet...</span>';

            // DETECT METAMASK EVERYWHERE
            const eth = window.ethereum || window.top?.ethereum || window.web3?.currentProvider;
            if (!eth) {{
                statusDiv.innerHTML = '<span style="color:red; font-weight:bold;">MetaMask Not Found.</span> Please install it or try refreshing.';
                return;
            }}
            
            statusDiv.innerHTML = '<span style="color:cyan;">Requesting accounts and signature...</span>';

            // Request accounts and sign the message
            eth.request({{method:'eth_requestAccounts'}})
            .then(a =>
                eth.request({{method:'personal_sign', params:['{st.session_state.message}', a[0]]}})
            )
            .then(sig => {{
                // SUCCESS: Display the signature and instructions
                outputArea.value = sig;
                outputArea.style.display = 'block';
                statusDiv.innerHTML = '<span style="color:lime; font-weight:bold;">✅ SIGNED!</span> <br> <span style="font-size:14px; color:#ddd;">Please manually COPY the text above (Ctrl+A, Ctrl+C) and paste it below.</span>';
                outputArea.select(); // Selects the text for easy manual copy
            }})
            .catch(error => {{
                // FAILURE
                const msg = error.code === 4001 ? "Signature Rejected by User." : "Signing Failed (See Console).";
                statusDiv.innerHTML = '<span style="color:red; font-weight:bold;">' + msg + '</span>';
            }});
        }}
        </script>
        <div style="text-align:center;">
            <button onclick="sign()" class="sig-btn">
                1-CLICK SIGN
            </button>
            <textarea id="sig-output" class="sig-output" readonly></textarea>
            <div id="sig-status" class="sig-status">Click orange button to begin.</div>
        </div>
        """, height=250) # Increased height to accommodate the signature textarea

        sig = st.text_input("PASTE SIGNATURE HERE (Ctrl+V)", key="sig", placeholder="0x...")

        if st.button("VERIFY", type="primary"):
            if not sig or len(sig) < 100:
                st.error("Please sign the message and paste the resulting signature above.")
            else:
                try:
                    recovered = Account.recover_message(encode_defunct(text=st.session_state.message), signature=sig)
                    if recovered.lower() == compromised.lower():
                        st.success("VERIFIED — you control the compromised wallet!")
                        st.session_state.verified = True
                        st.balloons()
                    else:
                        st.error("Sign with the **COMPROMISED** wallet (Wallet A)")
                except Exception as e:
                    st.error("Invalid signature: The message or signature is corrupted. Try signing again.")

with tab2:
    if st.session_state.get("verified"):
        st.success("Wallet A ownership verified. Ready for atomic claim execution.")
        st.warning("Replace this mock with the real Ethers.js contract deployment logic.")
        
        if st.button("CLAIM $500 EigenLayer", type="primary"):
            st.success(f"CLAIMED! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
    else:
        st.warning("Verify first")
