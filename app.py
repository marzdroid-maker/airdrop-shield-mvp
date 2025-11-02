# app.py
import secrets
import time
import streamlit as st
import streamlit.components.v1 as components
from eth_account import Account
from eth_account.messages import encode_defunct

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")

tab1, tab2 = st.tabs(["Verify Wallet", "Claim Airdrop"])

with tab1:
    st.subheader("Step 1: Verify Wallet Ownership")
    compromised = st.text_input("Compromised wallet", "0x9538bfa699f9c2058f32439de547a054a9ceeb5c")
    safe = st.text_input("Safe wallet (to receive funds)", "0xec451d6a06741e86e5ff0f9e5cc98d3388480c7a")

    if st.button("Generate Message"):
        msg = f"I own {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
        st.session_state.message = msg
        st.code(msg)
        st.info("Click below to sign with your **SAFE WALLET**:")

    if "message" in st.session_state:
        components.html(
            f"""
            <script>
            async function signAndFill() {{
                const eth = window.top.ethereum || window.ethereum;
                if (!eth) {{
                    alert("MetaMask not found — install the browser extension!");
                    return;
                }}
                try {{
                    const accounts = await eth.request({{method: 'eth_requestAccounts'}});
                    const sig = await eth.request({{
                        method: 'personal_sign',
                        params: ['{st.session_state.message}', accounts[0]]
                    }});
                    const inputs = window.parent.document.querySelectorAll('input[data-testid="stTextInput"]');
                    const sigInput = inputs[inputs.length - 1];
                    if (sigInput) {{
                        sigInput.value = sig;
                        sigInput.dispatchEvent(new Event('input', {{bubbles: true}}));
                        alert("Signature auto-filled!");
                    }} else {{
                        navigator.clipboard.writeText(sig);
                        alert("Signature copied — paste below");
                    }}
                }} catch (e) {{
                    alert("Sign cancelled or failed");
                }}
            }}
            </script>
            <button onclick="signAndFill()"
                    style="background:#f6851b;color:white;padding:16px 32px;border:none;
                           border-radius:12px;font-size:18px;cursor:pointer;">
                Sign with MetaMask
            </button>
            """,
            height=90,
        )

        signature = st.text_input(
            "Signature (auto-filled or paste here)",
            placeholder="0x...",
            key="sig"
        )

        if st.button("Verify Signature"):
            if not signature or len(signature) < 100:
                st.warning("Sign first!")
            else:
                try:
                    recovered = Account.recover_message(
                        encode_defunct(text=st.session_state.message),
                        signature=signature
                    )
                    if recovered.lower() == safe.lower():
                        st.success(f"Verified! Signed by {recovered[:6]}...{recovered[-4:]}")
                        st.session_state.verified = True
                    else:
                        st.error("Wrong wallet signed")
                except:
                    st.error("Invalid signature")

with tab2:
    if not st.session_state.get("verified"):
        st.warning("Verify ownership first")
    else:
        drop = st.selectbox("Airdrop", ["EigenLayer ($500)", "Hyperliquid ($300)", "Linea ($200)"])
        if st.button("Claim via Private Bundle"):
            with st.spinner("Bundling..."):
                time.sleep(2)
            st.success(f"Claimed {drop}! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
