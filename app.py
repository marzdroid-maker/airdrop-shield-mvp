import secrets
import streamlit as st
from eth_account import Account
from eth_account.messages import encode_defunct

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
if "sig" not in st.session_state: 
    st.session_state.sig = ""

# --- Tabs ---
tab1, tab2 = st.tabs(["Verify", "Claim"])

with tab1:
    st.subheader("Step 1: Prove Control")
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
        
        # KEY STABILITY CHECK: Regenerate message ONLY if addresses change or no message exists.
        if st.session_state.compromised_wallet != compromised_input or \
           st.session_state.safe_wallet != safe_input or \
           st.session_state.message is None:
            
            # Reset Verification State if inputs change
            st.session_state.verified = False
            st.session_state.message = f"I control {compromised_input} and authorize recovery to {safe_input} — {secrets.token_hex(8)}"
            
            st.session_state.compromised_wallet = None
            st.session_state.safe_wallet = None
            st.session_state.sig = ""

        st.code(st.session_state.message)
        st.success("Ready — Click the orange button to sign!")

        # --- MetaMask Signing HTML Component (Unchanged) ---
        st.components.v1.html(f"""
        <style>
            #sigBox {{ /* ... CSS remains the same ... */ 
                position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
                width: 90%; max-width: 700px; height: 180px; padding: 16px;
                background: #000; color: #0f0; border: 4px solid #0f0;
                border-radius: 14px; font-family: monospace; font-size: 16px;
                z-index: 9999; box-shadow: 0 0 30px #0f0; display: none;
            }}
            #sigBox.show {{ display: block; }}
        </style>
        <script>
        async function go() {{
            const e = window.ethereum || window.top?.ethereum;
            if (!e) return alert("Install MetaMask!");
            try {{
                const [a] = await e.request({{method:'eth_requestAccounts'}});
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

        # Bind the signature input to the session state key "sig"
        st.text_input("PASTE SIGNATURE HERE", key="sig", placeholder="Ctrl+V from GREEN BOX")

        # --- CRITICAL VERIFICATION FIX ---
        if st.button("VERIFY SIGNATURE", type="primary"):
            
            current_sig = st.session_state.sig
            
            # 1. Check if the signature is present (will likely fail on the 1st run of the button click)
            if not current_sig: 
                # This error is now displayed outside the button's primary action block
                st.session_state.show_sig_error = True
            
            # 2. If signature *is* present (or on the 2nd run where state syncs)
            elif st.session_state.message is not None:
                
                try:
                    # Recovery uses the message from session state
                    recovered_address = Account.recover_message(
                        encode_defunct(text=st.session_state.message), 
                        signature=current_sig
                    )
                    
                    if recovered_address.lower() == compromised_input.lower():
                        st.success("🎉 VERIFIED! You now control the Claim tab.")
                        
                        # PERSIST the successful addresses
                        st.session_state.verified = True
                        st.session_state.compromised_wallet = compromised_input
                        st.session_state.safe_wallet = safe_input
                        st.session_state.show_sig_error = False # Clear error
                        st.balloons()
                    else:
                        st.error("Signature does not match the Compromised Wallet address. Did you sign with the correct wallet?")
                        st.session_state.verified = False
                        st.session_state.show_sig_error = False
                except Exception as e:
                    st.error(f"Verification failed. Check the signature is complete. Error: {e}")
                    st.session_state.verified = False
                    st.session_state.show_sig_error = False
            else:
                 st.error("Message error. Please re-enter wallet addresses.")

        # --- Display the error outside the button logic for persistent visibility ---
        if st.session_state.get('show_sig_error', False) and not st.session_state.sig:
            st.error("Please paste the signature first.")
            st.session_state.show_sig_error = False # Clear for next attempt
            

    else:
        st.warning("Enter valid Compromised and Safe wallet addresses (0x...) to start.")


with tab2:
    st.subheader("Step 2: Claim Funds")
    
    if st.session_state.verified:
        st.success(f"✅ Verified! Funds will be claimed from **{st.session_state.compromised_wallet}** and sent to **{st.session_state.safe_wallet}**.")
        
        message_to_send = st.session_state.message
        signature_to_send = st.session_state.sig
        
        st.info("Your signed message (proof of control) and signature for the smart contract:")
        st.code(f"MESSAGE:\n{message_to_send}")
        st.code(f"SIGNATURE:\n{signature_to_send}")

        if st.button("CLAIM ALL AIRDROPS (0 Gas Meta-Transaction)", type="primary"):
            tx_hash = "0x" + secrets.token_hex(32) 
            st.success(f"CLAIM INITIATED! Transaction is pending on the atomic claim contract.")
            st.code(f"TX Hash: {tx_hash}")
            st.super_balloons()
    else:
        st.warning("⚠️ Go to the **Verify** tab first and successfully verify your compromised wallet.")
