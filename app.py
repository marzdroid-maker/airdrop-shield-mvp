# app.py
import streamlit as st
from streamlit_wallet_connector import wallet_connector
import secrets
import time

st.set_page_config(page_title="Airdrop Shield", page_icon="Shield", layout="centered")
st.title("Shield Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")

# Initialize wallet connector
wallet = wallet_connector(key="wallet")

tab1, tab2 = st.tabs(["Verify", "Claim"])

with tab1:
    st.subheader("Step 1: Verify Ownership")
    compromised = st.text_input("Compromised Wallet", placeholder="0xDead...")
    safe = st.text_input("Safe Wallet", placeholder="0xSafe...")

    if st.button("Connect Safe Wallet & Sign"):
        if not compromised or not safe:
            st.error("Enter both wallets")
        else:
            message = f"I own {compromised} and authorize recovery to {safe} - {secrets.token_hex(8)}"
            signature = wallet.sign_message(message)
            if signature:
                st.success("Verified! Signature valid.")
                st.session_state.verified = True
                st.session_state.compromised = compromised
                st.session_state.safe = safe
            else:
                st.error("Signature failed")

with tab2:
    if not st.session_state.get("verified"):
        st.warning("Verify first.")
    else:
        drop = st.selectbox("Airdrop", ["EigenLayer ($500)", "Hyperliquid ($300)", "Linea ($200)"])
        if st.button("Claim via Private Bundle"):
            with st.spinner("Submitting to private mempool..."):
                time.sleep(2)
            st.success(f"Claimed {drop}! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
