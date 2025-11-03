
# app.py — THE ONE THAT WORKS FOR EVERYONE
import secrets
import streamlit as st
from eth_account import Account
from eth_account.messages import encode_defunct

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Prove you still control your compromised wallet")

tab1, tab2 = st.tabs(["Verify", "Claim"])

with tab1:
    st.subheader("Step 1: Prove you control the compromised wallet")
    compromised = st.text_input("Compromised wallet", "0x9538bfa699f9c2058f32439de547a054a9ceeb5c")
    safe = st.text_input("Safe wallet", "0xec451d6a06741e86e5ff0f9e5cc98d3388480c7a")

    # AUTO-GENERATE
    if compromised.startswith("0x") and safe.startswith("0x") and len(compromised) == 42 and len(safe) == 42:
        if "message" not in st.session_state:
            msg = f"I control {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
            st.session_state.message = msg
            st.code(msg)
            st.success("Ready — click orange!")

    if "message" in st.session_state:
        # MAGIC BUTTON — NO CLIPBOARD, NO PASTE
        st.components.v1.html(f"""
        <script>
        async function magic() {{
            const eth = window.ethereum || (window.top && window.top.ethereum);
            if (!eth) return alert("MetaMask not found — install it!");
            try {{
                const [addr] = await eth.request({{method: 'eth_requestAccounts'}});
                const sig = await eth.request({{method: 'personal_sign', params: ['{st.session_state.message}', addr]}});
                // AUTO-FILL + AUTO-VERIFY
                const box = parent.document.querySelector('input[data-testid="stTextInput"]');
                box.value = addr + '|' + sig;
                box.dispatchEvent(new Event('input', {{bubbles: true}}));
                setTimeout(() => parent.document.querySelector('button[kind="primary"]').click(), 400);
            }} catch {{ alert("DON’T REJECT — click orange & SIGN!"); }}
        }}
        </script>
        <button onclick="magic()" 
                style="background:#f6851b;color:white;padding:22px 70px;border:none;
                       border-radius:16px;font-size:30px;cursor:pointer;font-weight:bold;
                       box-shadow:0 10px 40px #f6851b88;">
            1-CLICK SIGN & VERIFY
        </button>
        """, height=160)

        # HIDDEN FIELD — auto-filled by JS
        signature = st.text_input("Signature", value="", key="sig", disabled=True, label_visibility="collapsed")

        if st.button("VERIFY", type="primary"):
            if '|' not in signature:
                st.error("Click orange button first")
            else:
                addr, sig = signature.split('|', 1)
                try:
                    recovered = Account.recover_message(encode_defunct(text=st.session_state.message), signature=sig)
                    if recovered.lower() == compromised.lower():
                        st.success("VERIFIED — you control the compromised wallet!")
                        st.session_state.verified = True
                        st.balloons()
                    else:
                        st.error("Wrong wallet")
                except:
                    st.error("Invalid")

with tab2:
    if st.session_state.get("verified"):
        if st.button("CLAIM $500 EigenLayer", type="primary"):
            st.success("CLAIMED! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
    else:
        st.warning("Verify first")
