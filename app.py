# app.py  —  THE FINAL VERSION  —
import secrets
import streamlit as st
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

    # AUTO-GENERATE
    if compromised.startswith("0x") and safe.startswith("0x") and len(compromised) == 42 and len(safe) == 42:
        if "message" not in st.session_state:
            msg = f"I own {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
            st.session_state.message = msg
            st.code(msg)
            st.success("Ready — click orange!")

    if "message" in st.session_state:
        st.markdown(
            """
            <button onclick="navigator.clipboard.writeText(''); 
                ethereum.request({method:'eth_requestAccounts'}).then(a=> 
                ethereum.request({method:'personal_sign',params:['"""+st.session_state.message+"""',a[0]]}))
                .then(sig=>{navigator.clipboard.writeText(sig);alert('COPIED! Ctrl+V below')})"
                style="background:#f6851b;color:white;padding:22px 70px;border:none;
                       border-radius:16px;font-size:30px;cursor:pointer;font-weight:bold;">
                1-CLICK SIGN & COPY
            </button>
            """,
            unsafe_allow_html=True,
        )

        signature = st.text_input("PASTE HERE (Ctrl+V)", key="sig")

        if st.button("VERIFY SIGNATURE", type="primary"):
            try:
                recovered = Account.recover_message(
                    encode_defunct(text=st.session_state.message),
                    signature=signature
                )
                if recovered.lower() == safe.lower():
                    st.success("VERIFIED!")
                    st.session_state.verified = True
                    st.balloons()
                else:
                    st.error("Wrong wallet")
            except:
                st.error("Paste signature first")

with tab2:
    if st.session_state.get("verified"):
        if st.button("CLAIM $500", type="primary"):
            st.success("CLAIMED! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
