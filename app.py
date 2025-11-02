# app.py
import secrets
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

    # AUTO-GENERATE
    if compromised.startswith("0x") and safe.startswith("0x") and len(compromised) == 42 and len(safe) == 42:
        if "message" not in st.session_state:
            msg = f"I own {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
            st.session_state.message = msg
            st.code(msg)
            st.success("Message auto-generated — click orange button!")

    if "message" in st.session_state:
        components.html(
            f"""
            <script>
            async function signNow() {{
                const eth = window.top?.ethereum || window.ethereum;
                if (!eth) return alert("Install MetaMask!");
                try {{
                    const accounts = await eth.request({{method: 'eth_requestAccounts'}});
                    const sig = await eth.request({{
                        method: 'personal_sign',
                        params: ['{st.session_state.message}', accounts[0]]
                    }});
                    const box = parent.document.querySelector('input[data-testid="stTextInput"]');
                    box.value = sig;
                    box.dispatchEvent(new Event('input', {{bubbles:true}}));
                    setTimeout(() => parent.document.querySelector('button[kind="primary"]').click(), 300);
                }} catch (e) {{
                    alert("You cancelled — click orange and SIGN!");
                }}
            }}
            </script>
            <button onclick="signNow()"
                    style="background:#f6851b;color:white;padding:22px 70px;border:none;
                           border-radius:16px;font-size:30px;cursor:pointer;font-weight:bold;
                           box-shadow:0 10px 40px #f6851b88;">
                1-CLICK SIGN & VERIFY
            </button>
            """,
            height=160,
        )

        signature = st.text_input("Signature (auto-filled)", key="sig", disabled=True)

        if st.button("VERIFY SIGNATURE", type="primary"):
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
                st.error("Invalid signature — try again")

with tab2:
    if st.session_state.get("verified"):
        drop = st.selectbox("Airdrop", ["EigenLayer ($500)", "Hyperliquid ($300)", "Linea ($200)"])
        if st.button("CLAIM", type="primary"):
            st.success(f"CLAIMED {drop}! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
    else:
        st.warning("Verify first")
