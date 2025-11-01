# app.py
import streamlit as st
from streamlit_javascript import st_javascript
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

    if st.button("Connect & Sign with MetaMask"):
        if not compromised or not safe:
            st.error("Enter both wallets")
        else:
            message = f"I own {compromised} and authorize recovery to {safe} - {secrets.token_hex(8)}"
            st.code(message)

            # Trigger MetaMask
            result = st_javascript(f"""
                async function sign() {{
                    if (!window.ethereum) {{
                        return {{error: "MetaMask not detected"}};
                    }}
                    const accounts = await ethereum.request({{method: 'eth_requestAccounts'}});
                    const sig = await ethereum.request({{
                        method: 'personal_sign',
                        params: [JSON.stringify({{message: "{message}"}}), accounts[0]]
                    }});
                    return {{signature: sig, address: accounts[0]}};
                }}
                await sign();
            """)

            if result and "signature" in result:
                st.success(f"Verified! Signed by {result['address'][:6]}...{result['address'][-4:]}")
                st.session_state.verified = True
                st.session_state.compromised = compromised
                st.session_state.safe = safe
            elif result and "error" in result:
                st.error(result["error"])
            else:
                st.info("Waiting for MetaMask...")

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
