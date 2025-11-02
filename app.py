import secrets
import streamlit as st
from eth_account import Account
from eth_account.messages import encode_defunct

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Prove you still control your compromised wallet — safely move airdrops.")

tab1, tab2 = st.tabs(["Verify", "Claim"])

with tab1:
    st.subheader("Step 1: Prove you control the compromised wallet")
    compromised = st.text_input("Compromised wallet", "0x9538bfa699f9c2058f32439de547a054a9ceeb5c")
    safe = st.text_input("Safe wallet (receive airdrops)", "0xec451d6a06741e86e5ff0f9e5cc98d3388480c7a")

    if compromised.startswith("0x") and safe.startswith("0x") and len(compromised) == 42 and len(safe) == 42:
        if "message" not in st.session_state:
            msg = f"I control {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
            st.session_state.message = msg
            st.code(msg)
            st.success("Message ready — click orange!")

    if "message" in st.session_state:
        st.components.v1.html(
            f"""
            <script>
            function sign() {{
                if (!window.ethereum) return alert("Install MetaMask");
                ethereum.request({{method:'eth_requestAccounts'}}).then(a=>
                    ethereum.request({{method:'personal_sign',params:['{st.session_state.message}',a[0]]}})
                ).then(sig=>{{
                    navigator.clipboard.writeText(sig);
                    alert("SIGNED & COPIED! Ctrl+V → Verify");
                }}).catch(() => alert("DON’T REJECT"));
            }}
            </script>
            <button onclick="sign()" style="background:#f6851b;color:white;padding:22px 70px;border:none;
                    border-radius:16px;font-size:30px;cursor:pointer;font-weight:bold;">
                1-CLICK SIGN & COPY
            </button>
            """,
            height=160,
        )

        sig = st.text_input("PASTE HERE (Ctrl+V)", key="sig")

        if st.button("VERIFY", type="primary"):
            if not sig or len(sig) < 100:
                st.error("Click orange → SIGN → Ctrl+V")
            else:
                try:
                    recovered = Account.recover_message(
                        encode_defunct(text=st.session_state.message),
                        signature=sig
                    )
                    if recovered.lower() == compromised.lower():
                        st.success(f"VERIFIED! You control {compromised[:8]}...!")
                        st.session_state.verified = True
                        st.balloons()
                    else:
                        st.error("Sign with the **COMPROMISED** wallet")
                except:
                    st.error("Invalid signature")

with tab2:
    if st.session_state.get("verified"):
        if st.button("CLAIM $500 EigenLayer", type="primary"):
            st.success("CLAIMED! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
    else:
        st.warning("Verify first")
