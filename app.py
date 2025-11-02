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

    if compromised.startswith("0x") and safe.startswith("0x") and len(compromised) == 42 and len(safe) == 42:
        if "message" not in st.session_state:
            msg = f"I own {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
            st.session_state.message = msg
            st.code(msg)
            st.success("Ready — click orange!")

    if "message" in st.session_state:
        components.html(
            f"""
            <script id="signer">
            async function signNow() {{
                const eth = window.top?.ethereum || window.ethereum;
                if (!eth) return alert("Install MetaMask!");
                try {{
                    const accounts = await eth.request({{method: 'eth_requestAccounts'}});
                    const sig = await eth.request({{
                        method: 'personal_sign',
                        params: ['{st.session_state.message}', accounts[0]]
                    }});
                    await navigator.clipboard.writeText(sig);
                    const script = document.getElementById('signer');
                    const iframe = script.closest('iframe');
                    const box = iframe.parentElement.parentElement.parentElement.querySelector('input[data-testid="stTextInput"]');
                    box.value = sig;
                    box.dispatchEvent(new Event('input', {{bubbles:true}}));
                    setTimeout(() => iframe.parentElement.parentElement.parentElement.querySelector('button[kind="primary"]').click(), 500);
                    alert("SIGNED! Box filled — balloons in 1 sec!");
                }} catch (e) {{
                    alert("DON’T REJECT — click orange & SIGN!");
                }}
            }}
            const script = document.getElementById('signer');
            window.parent.document.body.appendChild(script);
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

        signature = st.text_input("Signature (auto-filled)", "", key="sig", disabled=False)

        if st.button("VERIFY SIGNATURE", type="primary"):
            try:
                recovered = Account.recover_message(encode_defunct(text=st.session_state.message), signature=signature)
                if recovered.lower() == safe.lower():
                    st.success("VERIFIED!")
                    st.session_state.verified = True
                    st.balloons()
                else:
                    st.error("Wrong wallet")
            except:
                st.error("Click orange first")

with tab2:
    if st.session_state.get("verified"):
        if st.button("CLAIM $500", type="primary"):
            st.success("CLAIMED! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
