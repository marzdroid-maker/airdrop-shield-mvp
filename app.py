# app.py
import streamlit as st
from eth_account import Account
import secrets
import time

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")

tab1, tab2 = st.tabs(["Verify", "Claim"])

with tab1:
    st.subheader("Step 1: Verify Ownership")
    compromised = st.text_input("Compromised Wallet", placeholder="0xDead...")
    safe = st.text_input("Safe Wallet", placeholder="0xSafe...")

    if st.button("Generate Message"):
        if not compromised or not safe:
            st.error("Enter both wallets")
        else:
            message = f"I own {compromised} and authorize recovery to {safe} - {secrets.token_hex(8)}"
            st.code(message)
            st.info("Open MetaMask → Sign this message with your **safe wallet** → Paste signature below")
            st.session_state.message = message

    if "message" in st.session_state:
        signature = st.text_input("Paste signature here (from MetaMask)", key="sig")
        if st.button("Verify Signature"):
            try:
                recovered = Account.recover_message(
                    st.session_state.message.encode("utf-8"),
                    signature=signature
                )
                if recovered.lower() == safe.lower():
                    st.success(f"Verified! Signed by {recovered[:6]}...{recovered[-4:]}")
                    st.session_state.verified = True
                    st.session_state.compromised = compromised
                    st.session_state.safe = safe
                else:
                    st.error("Signature does not match safe wallet")
            except Exception as e:
                st.error(f"Invalid signature: {e}")

with tab2:
    if not st.session_state.get("verified"):
        st.warning("Verify first.")
    else:
        drop = st.selectbox("Airdrop", ["EigenLayer ($500)", "Hyperliquid ($300)", "Linea ($200)"])
        if st.button("Claim via Private Bundle"):
            with st.spinner("Submitting..."):
                time.sleep(2)
            st.success(f"Claimed {drop}! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
