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

    compromised = st.text_input("Compromised wallet", placeholder="0xDead...")
    safe = st.text_input("Safe wallet (to receive funds)", placeholder="0xSafe...")

    if st.button("Generate Message"):
        if not compromised or not safe:
            st.error("Enter both wallets")
        else:
            msg = f"I own {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
            st.session_state.message = msg
            st.session_state.sig_key = f"sig_{secrets.token_hex(8)}"
            st.code(msg)
            st.info("Click below to sign with MetaMask:")

    if "message" in st.session_state:
        # Render button + auto-fill
        components.html(
            f"""
            <script>
            async function signAndFill() {{
                if (!window.ethereum) {{
                    alert("Install MetaMask!");
                    return;
                }}
                try {{
                    const accounts = await window.ethereum.request({{method: 'eth_requestAccounts'}});
                    const sig = await window.ethereum.request({{
                        method: 'personal_sign',
                        params: ['{st.session_state.message}', accounts[0]]
                    }});
                    // Auto-fill the last text input
                    const inputs = parent.document.querySelectorAll('input[data-testid="stTextInput"]');
                    const sigInput = inputs[inputs.length - 1];
                    if (sigInput) {{
                        sigInput.value = sig;
                        sigInput.dispatchEvent(new Event('input', {{bubbles: true}}));
                        alert("✅ Signature auto-filled!");
                    }} else {{
                        navigator.clipboard.writeText(sig);
                        alert("✅ Signature copied! Paste below.");
                    }}
                }} catch (e) {{
                    alert("Error: " + e.message);
                }}
            }}
            </script>
            <button onclick="signAndFill()"
                    style="background:#f6851b;color:white;padding:14px 28px;border:none;
                           border-radius:12px;font-size:18px;cursor:pointer;">
                🧾 Sign with MetaMask
            </button>
            """,
            height=80,
        )

        # Signature box
        signature = st.text_input(
            "Signature (auto-filled or paste here)",
            placeholder="0x...",
            key="user_sig"
        )

        if st.button("Verify Signature"):
            if not signature or len(signature) < 100:
                st.warning("Sign first.")
            else:
                try:
                    msg_hash = encode_defunct(text=st.session_state.message)
                    recovered = Account.recover_message(msg_hash, signature=signature)
                    if recovered.lower() == safe.lower():
                        st.success(f"✅ Verified! Signed by {recovered[:6]}...{recovered[-4:]}")
                        st.session_state.verified = True
                    else:
                        st.error("Wrong wallet signed.")
                except Exception as e:
                    st.error("Invalid signature.")

with tab2:
    st.subheader("Step 2: Claim Airdrop")
    if not st.session_state.get("verified"):
        st.warning("Verify first.")
    else:
        drop = st.selectbox("Airdrop", ["EigenLayer ($500)", "Hyperliquid ($300)", "Linea ($200)"])
        if st.button("Claim via Private Bundle"):
            with st.spinner("Submitting..."):
                time.sleep(2)
            st.success(f"🎉 Claimed {drop}! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
