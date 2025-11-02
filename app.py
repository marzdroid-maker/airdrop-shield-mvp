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
    compromised = st.text_input("Compromised wallet", value="0x9538bfa699f9c2058f32439de547a054a9ceeb5c")
    safe = st.text_input("Safe wallet", value="0xec451d6a06741e86e5ff0f9e5cc98d3388480c7a")

    if st.button("Generate Message"):
        msg = f"I own {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
        st.session_state.message = msg
        st.code(msg)
        st.success("Ready! Click below → MetaMask → Sign → AUTO-VERIFIED")

    if "message" in st.session_state:
        # ONE-CLICK SIGNER (no iframe, no sandbox)
        components.html(
            f"""
            <script>
            async function oneClickSign() {{
                if (!window.ethereum) return alert("Install MetaMask!");
                try {{
                    const accounts = await ethereum.request({{method: 'eth_requestAccounts'}});
                    const sig = await ethereum.request({{
                        method: 'personal_sign',
                        params: ['{st.session_state.message}', accounts[0]]
                    }});
                    // AUTO-FILL
                    const inputs = parent.document.querySelectorAll('input[data-testid="stTextInput"]');
                    const box = inputs[inputs.length - 1];
                    box.value = sig;
                    box.dispatchEvent(new Event('input', {{bubbles: true}}));
                    parent.document.querySelector('button[kind="primary"]').click(); // Auto-verify
                }} catch (e) {{ alert("Cancelled"); }}
            }}
            </script>
            <button onclick="oneClickSign()"
                    style="background:#f6851b;color:white;padding:20px 60px;border:none;
                           border-radius:16px;font-size:28px;cursor:pointer;font-weight:bold;
                           box-shadow:0 8px 30px rgba(246,133,27,0.5);">
                1-CLICK SIGN & VERIFY
            </button>
            """,
            height=140,
        )

        signature = st.text_input(
            "Signature (auto-filled)",
            key="sig",
            disabled=True
        )

        if st.button("VERIFY SIGNATURE", type="primary", key="verify_btn"):
            if not signature:
                st.warning("Click the orange button above")
            else:
                try:
                    recovered = Account.recover_message(
                        encode_defunct(text=st.session_state.message),
                        signature=signature
                    )
                    if recovered.lower() == safe.lower():
                        st.success(f"VERIFIED! {recovered[:8]}...{recovered[-6:]}")
                        st.session_state.verified = True
                        st.balloons()
                    else:
                        st.error("Wrong wallet")
                except:
                    st.error("Invalid")

with tab2:
    if not st.session_state.get("verified"):
        st.warning("Verify first")
    else:
        drop = st.selectbox("Airdrop", ["EigenLayer ($500)", "Hyperliquid ($300)", "Linea ($200)"])
        if st.button("CLAIM", type="primary"):
            with st.spinner("Submitting..."):
                time.sleep(2)
            st.success(f"CLAIMED {drop}! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
