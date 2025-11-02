import secrets
import streamlit as st
from eth_account import Account
from eth_account.messages import encode_defunct

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")

# Use session state to manage verification status
if "verified" not in st.session_state:
    st.session_state.verified = False
if "message" not in st.session_state:
    st.session_state.message = None

tab1, tab2 = st.tabs(["Verify Wallet", "Claim Airdrop"])

with tab1:
    st.subheader("Step 1: Verify Wallet Ownership")
    compromised = st.text_input("Compromised wallet (Wallet A)", "0x9538bfa699f9c2058f32439de547a054a9ceeb5c")
    safe = st.text_input("Safe wallet (Wallet B)", "0xec451d6a06741e86e5ff0f9e5cc98d3388480c7a")

    # AUTO-GENERATE MESSAGE
    if compromised.startswith("0x") and safe.startswith("0x") and len(compromised) == 42 and len(safe) == 42:
        if st.session_state.message is None or not st.session_state.verified:
            # Generate new message only if not yet verified
            msg = f"I own {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
            st.session_state.message = msg
            st.code(msg)
            st.info("Message ready: Sign this exact text with your Compromised Wallet (A).")

    if st.session_state.message:
        # MAGIC BUTTON (Iframe component for Metamask interaction)
        st.components.v1.html(
            f"""
            <script>
            function signMessage() {{
                const statusDiv = document.getElementById('status');
                const signatureInput = document.getElementById('signature-output');

                if (!window.ethereum) {{
                    // UPDATED ERROR MESSAGE FOR CLARITY
                    statusDiv.innerHTML = '<span style="color:red; font-weight:bold;">METAMASK NOT DETECTED.</span> Please ensure the browser extension is active and injected.';
                    return;
                }}
                
                statusDiv.innerHTML = '<span style="color:yellow;">Requesting signature...</span>';

                ethereum.request({{method: 'eth_requestAccounts'}})
                .then(accounts => 
                    ethereum.request({{
                        method: 'personal_sign',
                        params: ['{st.session_state.message}', accounts[0]]
                    }})
                ).then(sig => {{
                    signatureInput.value = sig;
                    signatureInput.style.display = 'block';
                    statusDiv.innerHTML = '<span style="color:lime; font-weight:bold;">SIGNED! Copy the text above 👆</span>';
                    signatureInput.select(); // Select the text for easy copy on desktop

                }}).catch(error => {{
                    signatureInput.value = '';
                    signatureInput.style.display = 'none';
                    statusDiv.innerHTML = '<span style="color:red; font-weight:bold;">SIGNATURE REJECTED. Try again.</span>';
                    console.error("Signing error:", error);
                }});
            }}
            </script>
            <div style="text-align:center;">
                <input type="text" id="signature-output" readonly placeholder="Signature will appear here"
                       style="display:none; width:90%; padding:8px; margin-bottom:10px; border: 2px solid #f6851b; border-radius:8px; font-family:monospace; color:#333; background:#fff; text-align:center;">
                <button onclick="signMessage()" 
                        style="background:#f6851b; color:white; padding:18px 40px; border:none;
                                border-radius:12px; font-size:24px; cursor:pointer; font-weight:bold;
                                box-shadow:0 6px 20px #f6851b88; transition: all 0.2s;">
                    SIGN MESSAGE (Compromised Wallet A)
                </button>
                <div id="status" style="margin-top:10px; font-size:16px;"></div>
            </div>
            """,
            height=200,
        )

        signature = st.text_input("PASTE SIGNATURE HERE (Ctrl+V)", key="sig", placeholder="0x...")

        if st.button("VERIFY SIGNATURE", type="primary"):
            if not signature or len(signature) < 100:
                st.error("Please sign the message and paste the resulting signature above.")
            else:
                try:
                    recovered = Account.recover_message(
                        encode_defunct(text=st.session_state.message),
                        signature=signature
                    )
                    # The message states that Wallet A authorizes recovery to Wallet B.
                    # We MUST verify that Wallet A (the compromised address) signed the message.
                    if recovered.lower() == compromised.lower():
                        st.success("VERIFIED! 🎉 Compromised Wallet A is the signatory.")
                        st.session_state.verified = True
                        st.balloons()
                    else:
                        st.error(f"Wrong wallet signed the message. Expected: {compromised.lower()}. Recovered: {recovered.lower()}")
                except Exception as e:
                    st.error("Invalid signature — please check the signature and try signing again.")

with tab2:
    if st.session_state.get("verified"):
        st.success("Wallet A ownership is verified! Ready for atomic claim execution.")
        st.warning("The button below is currently a mock. The real implementation must use the Ethers.js and ClaimProxy.sol logic.")
        
        # This is where you would replace the mock button with the actual Ethers.js call
        # to the ClaimProxy contract, potentially integrating with the rescue_claim_vault.html logic
        if st.button("MOCK CLAIM (Replace with Ethers.js Contract Call)", type="primary"):
            st.success(f"MOCK CLAIMED! In the real app, this would execute the atomic sweep to Wallet B. TX: 0xMock{secrets.token_hex(8)}")
            st.super_balloons()
    else:
        st.warning("Please verify ownership of Wallet A in the 'Verify Wallet' tab first.")
