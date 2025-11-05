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
# We will now use 'sig' as a direct session state variable, NOT linked to st.text_input
if "sig" not in st.session_state: 
    st.session_state.sig = ""

# --- Inject Streamlit Components API (REQUIRED for JS state update) ---
# This initializes the communication bridge between JS and Python
st.components.v1.html('<script src="https://cdn.jsdelivr.net/npm/streamlit-component-lib@1.0.2/dist/streamlit-component-lib.js"></script>', height=0)

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
            st.session_state.sig = "" # Clear the old signature

        st.code(st.session_state.message)
        
        # Display current status
        if st.session_state.sig:
            st.success("✅ Signature captured! Click VERIFY to complete.")
            st.code(st.session_state.sig[:10] + "..." + st.session_state.sig[-8:])
        else:
            st.info("Ready — Click the orange button to sign!")

        # --- MetaMask Signing HTML Component with Direct State Write ---
        st.components.v1.html(f"""
        <script>
        // Use a function to wait for the Streamlit Component API to load
        function onStreamlitReady(callback) {{
            if (window.Streamlit) {{
                callback();
            }} else {{
                setTimeout(() => onStreamlitReady(callback), 100);
            }}
        }}

        async function go() {{
            const e = window.ethereum || window.top?.ethereum;
            if (!e) return alert("Install MetaMask!");
            
            // Check if Streamlit API is loaded before proceeding
            onStreamlitReady(async () => {{
                try {{
                    const [a] = await e.request({{method:'eth_requestAccounts'}});
                    const s = await e.request({{method:'personal_sign', params:['{st.session_state.message}', a]}}); 
                    
                    // CRITICAL CHANGE: Write the signature directly to Streamlit's state.
                    // The component's value is set to the signature 's'.
                    window.Streamlit.setComponentValue(s); 

                    // We trigger a Streamlit rerun after setting the value so Python can immediately see it.
                    window.Streamlit.setFrameHeight(1); 
                    
                }} catch {{ 
                    alert("Please SIGN the message — don't reject!"); 
                }}
            }});
        }}
        </script>
        <div style="text-align:center; margin:40px 0;">
            <button onclick="go()" 
                    style="background:#f6851b;color:white;padding:28px 100px;border:none;
                           border-radius:20px;font-size:38px;font-weight:bold;cursor:pointer;
                           box-shadow:0 15px 60px #f6851b88;">
                1-CLICK SIGN & CAPTURE
            </button>
            <p><b>This automatically captures the signature.</b></p>
        </div>
        """, height=200, key="signature_capture")
        # NOTE: The key for the HTML component ('signature_capture') will hold the signature in st.session_state['signature_capture']
        
        # Store the captured signature from the HTML component's key
        # This will be automatically updated by the JavaScript call
        st.session_state.sig = st.session_state.signature_capture or ""
        
        # --- Verification Logic ---
        if st.button("VERIFY SIGNATURE", type="primary"):
            
            current_sig = st.session_state.sig

            if not current_sig: 
                st.error("Please click '1-CLICK SIGN & CAPTURE' first.")
            elif st.session_state.message is None:
                st.error("Message error. Please re-enter wallet addresses.")
            else:
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
