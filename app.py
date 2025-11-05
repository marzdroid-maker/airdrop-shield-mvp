import secrets
import streamlit as st
from eth_account import Account
from eth_account.messages import encode_defunct

# Clear cache is generally not recommended in production as it impacts performance,
# but it's fine for rapid testing of state changes.
# st.cache_data.clear() # Keeping commented out for better performance if deployed
st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️")
st.title("🛡️ Airdrop Shield")

# --- Initialize State ---
if "verified" not in st.session_state:
    st.session_state.verified = False
if "compromised_wallet" not in st.session_state:
    st.session_state.compromised_wallet = None
if "safe_wallet" not in st.session_state:
    st.session_state.safe_wallet = None
if "message" not in st.session_state:
    st.session_state.message = None

# --- Tabs ---
tab1, tab2 = st.tabs(["Verify", "Claim"])

with tab1:
    st.subheader("Step 1: Prove Control")
    # Use different keys for the input boxes to prevent issues with session state
    compromised_input = st.text_input("Compromised wallet (to claim from)", 
                                      value=st.session_state.compromised_wallet or "", 
                                      key="compromised_input", 
                                      placeholder="0x...")
    safe_input = st.text_input("Safe wallet (to send to)", 
                               value=st.session_state.safe_wallet or "", 
                               key="safe_input", 
                               placeholder="0x...")

    # Check for valid address format and generate message
    if compromised_input.startswith("0x") and len(compromised_input) == 42 and \
       safe_input.startswith("0x") and len(safe_input) == 42:

        # Only generate a new message if the wallets have changed or no message exists
        if st.session_state.compromised_wallet != compromised_input or \
           st.session_state.safe_wallet != safe_input or \
           st.session_state.message is None:
            # Generate a new unique message for signing
            st.session_state.message = f"I control {compromised_input} and authorize recovery to {safe_input} — {secrets.token_hex(8)}"
            # Reset verification status if wallets change
            st.session_state.verified = False
            st.session_state.compromised_wallet = None
            st.session_state.safe_wallet = None

        st.code(st.session_state.message)
        st.success("Ready — Click the orange button to sign!")

        # --- MetaMask Signing HTML Component ---
        st.components.v1.html(f"""
        <style>
            /* CSS for the signature box */
            #sigBox {{
                /* ... your existing CSS ... */
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
                // IMPORTANT: Use the session message
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
            else:
                try:
                    # Recover the signing address from the message and signature
                    recovered_address = Account.recover_message(
                        encode_defunct(text=st.session_state.message), 
                        signature=sig
                    )
                    
                    # Check if the recovered address matches the compromised wallet
                    if recovered_address.lower() == compromised_input.lower():
                        st.success("🎉 VERIFIED! You now control the Claim tab.")
                        
                        # PERSIST critical data to session state
                        st.session_state.verified = True
                        st.session_state.compromised_wallet = compromised_input
                        st.session_state.safe_wallet = safe_input
                        
                        st.balloons()
                    else:
                        st.error("Signature does not match the Compromised Wallet address.")
                        st.session_state.verified = False
                        st.session_state.compromised_wallet = None
                        st.session_state.safe_wallet = None
                except Exception as e:
                    st.error(f"Verification failed. Check the signature is complete. Error: {e}")
                    st.session_state.verified = False
                    st.session_state.compromised_wallet = None
                    st.session_state.safe_wallet = None
    else:
        st.warning("Enter valid Compromised and Safe wallet addresses (0x...) to start.")


with tab2:
    st.subheader("Step 2: Claim Funds")
    
    if st.session_state.verified:
        st.success(f"✅ Verified! Funds will be claimed from **{st.session_state.compromised_wallet}** and sent to **{st.session_state.safe_wallet}**.")
        
        # Display the signature for use in the smart contract (off-chain execution)
        st.info("Your signed message (proof of control) for the smart contract:")
        st.code(st.session_state.message)
        st.code(st.session_state.sig) # sig is the key used for the signature input

        # This button will trigger the actual smart contract call (e.g., via web3.py)
        if st.button("CLAIM ALL AIRDROPS (0 Gas Meta-Transaction)", type="primary"):
            # In a real app, this is where you'd call your smart contract
            # passing: compromised_wallet, safe_wallet, message, and signature
            
            # Placeholder for smart contract interaction
            tx_hash = "0x" + secrets.token_hex(32) # Mock transaction hash
            st.success(f"CLAIM INITIATED! Transaction is pending on the atomic claim contract.")
            st.code(f"TX Hash: {tx_hash}")
            st.super_balloons()
    else:
        st.warning("⚠️ Go to the **Verify** tab first and successfully verify your compromised wallet.")
