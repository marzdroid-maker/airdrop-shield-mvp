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
        st.success("✅ Message ready! Click below → Sign → **Ctrl+V**")

    if "message" in st.session_state:
        components.html(
            f"""
            <script>
            async function signAndCopy() {{
                const eth = window.top.ethereum || window.ethereum;
                if (!eth) return alert("Install MetaMask!");
                try {{
                    const accounts = await eth.request({{method: 'eth_requestAccounts'}});
                    const sig = await eth.request({{
                        method: 'personal_sign',
                        params: ['{st.session_state.message}', accounts[0]]
                    }});
                    await navigator.clipboard.writeText(sig);
                    alert("SIGNATURE COPIED!\\n\\nCLICK BOX → Ctrl+V → VERIFY");
                }} catch (e) {{ alert("Cancelled"); }}
            }}
            </script>
            <button onclick="signAndCopy()"
                    style="background:#f6851b;color:white;padding:20px 50px;border:none;
                           border-radius:16px;font-size:24px;cursor:pointer;font-weight:bold;
                           box-shadow:0 4px 20px rgba(246,133,27,0.4);">
                SIGN WITH METAMASK
            </button>
            """,
            height=130,
        )

        signature = st.text_input(
            "PASTE SIGNATURE HERE",
            placeholder="Click here → Ctrl+V",
            key="sig",
            help="After signing, paste with Ctrl+V"
        )

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
        if st.button("CLAIM VIA PRIVATE BUNDLE", type="primary"):
            with st.spinner("Submitting..."):
                time.sleep(2)
            st.success(f"CLAIMED {drop}! TX: 0xMock{secrets.token_hex(8)}")
            st.super_balloons()
