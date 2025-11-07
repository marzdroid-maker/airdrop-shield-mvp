# app.py — Airdrop Shield (with Safe Wallet Re-Verification on Claim)
import secrets
import streamlit as st
import requests  # <-- NEW: Required for API call to the Relayer
from eth_account import Account
from eth_account.messages import encode_defunct

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️")

# --- Custom styling
st.markdown("""
<style>
h1 {
    white-space: nowrap;
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    margin-bottom: 0.3rem !important;
}
div[data-baseweb="tab"] > button {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    padding: 0.4rem 1.4rem !important;
}
div[data-baseweb="tab-list"] {
    justify-content: center !important;
    border-bottom: 2px solid #e3e3e3 !important;
    margin-bottom: 0.5rem !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Airdrop Shield — Secure Recovery Tool")

# --- Session state
if "verified" not in st.session_state:
    st.session_state.verified = False
if "compromised" not in st.session_state:
    st.session_state.compromised = ""
if "safe" not in st.session_state:
    st.session_state.safe = ""
# Ensure signature is saved for the API call
if "sig" not in st.session_state:
    st.session_state.sig = ""

tab1, tab2 = st.tabs(["Verify", "Claim"])

# -------------------------------------------------------------------
# VERIFY TAB
# -------------------------------------------------------------------
with tab1:
    st.subheader("Step 1 — Verify Control of Compromised Wallet")

    st.markdown("""
    ### 🧭 Instructions
    1. **Enter your compromised wallet** (the one that lost access)  
    2. **Enter your safe wallet** (where funds will be sent) then **hit Enter to apply** 3. Click **🟧 1-CLICK SIGN** — MetaMask will pop up and ask you to sign a message  
    4. After signing, a **green box** appears at the bottom containing your signature  
    5. **Copy** the entire green text (Ctrl + C or ⌘ + C)  
    6. **Paste** it into the “Paste signature here” field  
    7. Click **VERIFY** to confirm wallet ownership  
    8. Once verified, go to the **Claim** tab to initiate recovery
    """)

    compromised = st.text_input("Compromised wallet", placeholder="0x...")
    safe = st.text_input("Safe wallet", placeholder="0x...")

    valid = (
        compromised.startswith("0x") and len(compromised) == 42 and
        safe.startswith("0x") and len(safe) == 42
    )

    if valid:
        st.session_state.compromised = compromised
        st.session_state.safe = safe

        if "message" not in st.session_state:
            st.session_state.message = (
                f"I control {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
            )
            st.code(st.session_state.message)
            st.success("✅ Ready — click the orange button below to sign in MetaMask")

    if "message" in st.session_state:
        st.components.v1.html(f"""
        <style>
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
        window.addEventListener('load', async () => {{
            const e = window.ethereum || window.top?.ethereum;
            if (e) {{
                try {{ await e.request({{method:'eth_requestAccounts'}}); }}
                catch(_){{}}
            }}
        }});

        async function go() {{
            const e = window.ethereum || window.top?.ethereum;
            if (!e) return alert("Please install MetaMask and connect your wallet.");
            try {{
                const [a] = await e.request({{ method:'eth_requestAccounts' }});
                const s = await e.request({{
                    method:'personal_sign',
                    params:['{st.session_state.message}', a]
                }});
                let box = document.getElementById('sigBox');
                if (!box) {{
                    box = document.createElement('textarea');
                    box.id = 'sigBox';
                    box.readOnly = true;
                    document.body.appendChild(box);
                }}
                box.value = s;
                box.classList.add('show');
                box.scrollIntoView({{behavior:'smooth', block:'center'}});
                alert("✅ Signature created! Scroll down and copy it from the green box.");
            }} catch (err) {{
                alert("❌ Signing was cancelled or failed. Try again.");
                console.error(err);
            }}
        }}
        </script>

        <div style="text-align:center; margin:40px 0;">
            <button onclick="go()" 
                    style="background:#f6851b;color:white;padding:26px 100px;border:none;
                            border-radius:20px;font-size:36px;font-weight:bold;cursor:pointer;
                            box-shadow:0 15px 60px #f6851b88;">
                1-CLICK SIGN
            </button>
            <p><b>Click → Sign → Copy from green box → Paste below</b></p>
        </div>
        """, height=330)

        sig = st.text_input("Paste signature here", key="sig", placeholder="Ctrl + V from green box")
        
        # Save signature to session state when input changes
        if sig and st.session_state.sig != sig:
            st.session_state.sig = sig

        if st.button("VERIFY", type="primary"):
            try:
                recovered = Account.recover_message(
                    encode_defunct(text=st.session_state.message),
                    signature=sig
                )
                if recovered.lower() == compromised.lower():
                    st.success("✅ Verified — you control the compromised wallet!")
                    st.session_state.verified = True
                    st.balloons()
                else:
                    st.error(f"❌ Signature recovered {recovered}, expected {compromised}")
            except Exception as e:
                st.error(f"Verification failed — please ensure full signature is pasted.\n\n{e}")

# -------------------------------------------------------------------
# CLAIM TAB (UPDATED FOR API CALL)
# -------------------------------------------------------------------
with tab2:
    st.subheader("Step 2 — Define and Authorize Recovery")

    if not st.session_state.verified:
        st.warning("Please verify ownership in the **Verify** tab first.")
    else:
        # Display verified details with truncation for cleanliness
        comp_disp = f"{st.session_state.compromised[:6]}...{st.session_state.compromised[-4:]}"
        safe_disp = f"{st.session_state.safe[:6]}...{st.session_state.safe[-4:]}"
        
        st.markdown(f"""
        ✅ **Compromised Wallet:** `{comp_disp}`  
        🟢 **Safe Wallet (from verification):** `{safe_disp}`  
        """)
        
        st.markdown("### 🧬 Define the Airdrop/Asset to Claim")

        contract_addr = st.text_input(
            "Target Contract Address (The contract that holds the claimable assets)",
            placeholder="0x..."
        )
        
        network = st.selectbox(
            "Network where the contract is located",
            ["Ethereum Mainnet", "Arbitrum", "Polygon", "Optimism", "Base", "Other..."]
        )
        
        claim_data = st.text_area(
            "Specific Claim Data (e.g., Merkle Proof, claim index, or 'All Tokens')",
            value="All Claimable Tokens via Recovery Function",
            height=100
        )
        
        st.markdown("---")

        st.markdown("### 🔐 Re-Confirm Safe Wallet & Authorize")

        confirm_safe = st.text_input(
            "Re-enter your safe wallet for final confirmation", 
            placeholder="0x..."
        )

        if st.button("AUTHORIZE RECOVERY CLAIM (0 gas)", type="primary"):
            
            # 1. Validation Checks
            if confirm_safe.lower() != st.session_state.safe.lower():
                st.error("❌ Safe wallet mismatch — please double-check the re-entered address.")
            
            elif not (contract_addr.startswith("0x") and len(contract_addr) == 42):
                st.error("❌ Invalid contract address format. Please ensure it is a valid 0x address.")
            
            # 2. API Call to Relayer Backend
            else:
                # --- API Configuration ---
                # NOTE: Change this URL to your public server when deployed.
                RELAYER_API_ENDPOINT = "http://192.168.1.192:5000/authorize_claim" 

                payload = {
                    # Data captured in Verify tab:
                    "signature": st.session_state.sig, 
                    "compromised_wallet": st.session_state.compromised,
                    "claim_message": st.session_state.message, 
                    # Data captured in Claim tab:
                    "safe_wallet": confirm_safe,
                    "contract_addr": contract_addr,
                    "network": network,
                    "claim_data": claim_data
                }

                st.info("⏳ Sending authorization request to Relayer service...")
                
                try:
                    # Use json= parameter for requests to automatically set Content-Type: application/json
                    response = requests.post(
                        RELAYER_API_ENDPOINT, 
                        json=payload, 
                        timeout=20 # Set a reasonable timeout
                    )
                    
                    # Handle Success (Relayer returns 200 and the TX hash)
                    if response.status_code == 200:
                        tx_hash = response.json().get('tx_hash', 'N/A')
                        st.success(f"✅ **Recovery Authorized and Sent!**")
                        st.markdown(f"**Transaction Hash:** `{tx_hash}`")
                        st.balloons()
                    
                    # Handle Failure (Relayer returns non-200 with an error message)
                    else:
                        error_data = response.json()
                        error_msg = error_data.get('message', 'Relayer server returned an error.')
                        st.error(f"❌ Claim Failed: {error_msg} (Status: {response.status_code})")
                        st.code(error_data)

                # Handle Connection Errors
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Connection Error: Could not reach the Relayer server at `{RELAYER_API_ENDPOINT}`. Is the backend running? ({e})")
