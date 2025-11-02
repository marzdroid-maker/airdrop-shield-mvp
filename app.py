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
    safe = st.text_input("Safe wallet", "0xec451d6a06741e86e5ff0f9e5cc98d3388480c7a")

    if st.button("Generate Message"):
        msg = f"I own {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
        st.session_state.message = msg
        st.code(msg)
        st.success("Message ready!")

    if "message" in st.session_state:
        signer_url = f"signer.html?msg={st.session_state.message.replace(' ', '%20')}"
        components.html(
            f"""
            <script>window.open('{signer_url}', '_blank', 'width=700,height=600');</script>
            <div style="text-align:center;padding:30px;background:#1e1e1e;border-radius:16px;color:white;">
              <h3>✅ New tab opened!</h3>
              <p>→ Click <b>SIGN WITH METAMASK</b></p>
              <p>→ Close tab → <b>Ctrl+V</b> below</p>
            </div>
            """,
            height=200,
        )

        signature = st.text_input("PASTE SIGNATURE (Ctrl+V)", key="sig")

        if st.button("VERIFY SIGNATURE", type="primary"):
            if not signature or len(signature) < 100:
                st.error("Paste signature first!")
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
                    st.error("Invalid signature")

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
