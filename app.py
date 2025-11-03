# app.py — FINAL — NO PASTE, NO REJECT, NO CLIPBOARD
import secrets
import streamlit as st
from eth_account import Account
from eth_account.messages import encode_defunct

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Prove you control your compromised wallet — 1 click")

tab1, tab2 = st.tabs(["Verify", "Claim"])

with tab1:
    st.subheader("Step 1: Prove control")
    compromised = st.text_input("Compromised wallet", "0x9538bfa699f9c2058f32439de547a054a9ceeb5c")
    safe = st.text_input("Safe wallet", "0xec451d6a06741e86e5e5ff0f9e5cc98d3388480c7a")

    if compromised.startswith("0x") and safe.startswith("0x") and len(compromised) == 42 and len(safe) == 42:
        if "msg" not in st.session_state:
            st.session_state.msg = f"I control {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
            st.code(st.session_state.msg)
            st.success("Ready — click orange!")

    if "msg" in st.session_state:
        # MAGIC BUTTON — AUTO-FILLS + AUTO-CLICKS
        st.components.v1.html(f"""
        <script>
        async function go() {{
            const eth = window.ethereum;
            if (!eth) return alert("Install MetaMask!");
            try {{
                const [addr] = await eth.request({{method:'eth_requestAccounts'}});
                const sig = await eth.request({{method:'personal_sign', params:['{st.session_state.msg}', addr]}});
                // AUTO-FILL HIDDEN BOX
                const box = parent.document.querySelector('input[data-testid="stTextInput"]');
                box.value = sig;
                box.dispatchEvent(new Event('input', {{bubbles:true}}));
                // AUTO-VERIFY
                setTimeout(() => parent.document.querySelector('button[kind="primary"]').click(), 500);
            }} catch {{ alert("DON’T REJECT — click orange & SIGN!"); }}
        }}
        </script>
        <button onclick="go()" 
                style="background:#f6851b;color:white;padding:25px 80px;border:none;
                       border-radius:16px;font-size:32px;cursor:pointer;font-weight:bold;
                       box-shadow:0 12px 50px #f6851b88;">
            1-CLICK SIGN & VERIFY
        </button>
        """, height=180)

        # HIDDEN + ENABLED BOX
        sig = st.text_input("Signature", "", key="sig", disabled=False, label_visibility="collapsed")

        if st.button("VERIFY", type="primary"):
            try:
                recovered = Account.recover_message(encode_defunct(text=st.session_state.msg), signature=sig)
                if recovered.lower() == compromised.lower():
                    st.success("VERIFIED — you control the compromised wallet!")
                    st.session_state.verified = True
                    st.balloons()
                else:
                    st.error("Sign with COMPROMISED wallet")
            except:
                st.error("Click orange first")

with tab2:
    if st.session_state.get("verified"):
        if st.button("CLAIM $500 EigenLayer", type="primary"):
            st.success("CLAIMED! TX: 0xMock{secrets.token_hex(8)}")
            st.super_balloons()
    else:
        st.warning("Verify first")
