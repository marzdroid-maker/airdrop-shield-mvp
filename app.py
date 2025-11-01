# app.py
import streamlit as st
import secrets
import time

st.set_page_config(page_title="Airdrop Shield", page_icon="Shield", layout="centered")
st.markdown("<h1 style='text-align: center;'>Shield Airdrop Shield</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Recover airdrops from compromised wallets — safely.</p>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Verify", "Claim"])

with tab1:
    st.subheader("Step 1: Verify Ownership")
    compromised = st.text_input("Compromised Wallet", placeholder="0xDead...")
    safe = st.text_input("Safe Wallet", placeholder="0xSafe...")
    
    if st.button("Generate Proof Message"):
        message = f"I own {compromised} and authorize transfer to {safe} - {secrets.token_hex(8)}"
        st.code(message)
        st.info("Sign this message with your **safe wallet** in MetaMask.")
    
    signature = st.text_input("Paste Signature Here")
    if signature and compromised and safe:
        st.success("Verified! You're the owner.")
        st.session_state.verified = True

with tab2:
    st.subheader("Step 2: Claim Airdrop")
    if not st.session_state.get("verified"):
        st.warning("Verify first.")
    else:
        drop = st.selectbox("Airdrop", ["EigenLayer ($500)", "Hyperliquid ($300)", "Linea ($200)"])
        if st.button("Claim via Private Bundle"):
            with st.spinner("Submitting to private mempool..."):
                time.sleep(2)
            st.success(f"Claimed {drop}! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
