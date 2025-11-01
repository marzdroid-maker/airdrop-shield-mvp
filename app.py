# app.py
import json
import secrets
import time

import streamlit as st
import streamlit.components.v1 as components
from eth_account import Account
from eth_account.messages import encode_defunct
from streamlit_javascript import st_javascript


st.set_page_config(page_title="Airdrop Shield", page_icon="Shield", layout="centered")
st.title("Shield Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")


# ---------------- MetaMask Signer (Keeps Your Working Button) ----------------
def render_metamask_signer(message: str):
    """
    Uses your working HTML button.
    Captures signature via postMessage + st_javascript.
    """
    # Your original button (keeps working popup)
    components.html(
        f"""
        <script>
        async function signAndSend() {{
            const provider = window.ethereum || window.top?.ethereum;
            if (!provider) {{
                alert("MetaMask not detected");
                return;
            }}
            try {{
                const accounts = await provider.request({{ method: "eth_requestAccounts" }});
                const from = accounts[0];
                const signature = await provider.request({{
                    method: "personal_sign",
                    params: ['{message}', from]
                }});
                // Send to Streamlit
                window.parent.postMessage({{
                    type: 'METAMASK_SIGNATURE',
                    signature: signature
                }}, '*');
            }} catch (err) {{
                alert("Signing failed: " + (err?.message || err));
            }}
        }}
        </script>

        <button onclick="signAndSend()"
            style="padding:12px 18px; border-radius:8px; background:#f6851b; color:#fff;
                   border:none; font-size:15px; cursor:pointer; margin-top:8px;">
            Sign with MetaMask
        </button>
        """,
        height=70,
    )

    # Capture signature
    result = st_javascript("""
        new Promise((resolve) => {
            const handler = (event) => {
                if (event.data?.type === 'METAMASK_SIGNATURE') {
                    resolve(event.data.signature);
                    window.removeEventListener('message', handler);
                }
            };
            window.addEventListener('message', handler);
            setTimeout(() => resolve(null), 60000);
        });
    """, key=f"sig_{secrets.token_hex(4)}")

    return result


# ---------------- UI ----------------
tab1, tab2 = st.tabs(["Verify Wallet", "Claim Airdrop"])

with tab1:
    st.subheader("Step 1: Verify Wallet Ownership")

    compromised = st.text_input("Compromised wallet", placeholder="0xDead...")
    safe = st.text_input("Safe wallet (to receive funds)", placeholder="0xSafe...")

    if st.button("Generate Message"):
        if not compromised or not safe:
            st.error("Enter both wallet addresses")
        else:
            msg = f"I own {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
            st.session_state.message = msg
            st.code(msg)
            st.info("Now sign with MetaMask:")

    if "message" in st.session_state:
        # Try auto-capture
        auto_sig = render_metamask_signer(st.session_state.message)

        if auto_sig:
            st.text_input("Signature (auto-filled)", value=auto_sig, disabled=True)
            signature = auto_sig
        else:
            signature = st.text_input("Signature (paste if not auto-filled)", placeholder="0x...")

        if st.button("Verify Signature"):
            if not signature or not signature.startswith("0x"):
                st.warning("Please sign first.")
            else:
                try:
                    msg_hash = encode_defunct(text=st.session_state.message)
                    recovered = Account.recover_message(msg_hash, signature=signature)
                    if recovered.lower() == safe.lower():
                        st.success(f"Verified! Signed by {recovered[:6]}...{recovered[-4:]}")
                        st.session_state.verified = True
                    else:
                        st.error("Signature does not match safe wallet.")
                except Exception as e:
                    st.error(f"Invalid: {e}")


with tab2:
    st.subheader("Step 2: Claim Airdrop")
    if not st.session_state.get("verified"):
        st.warning("Verify first.")
    else:
        drop = st.selectbox("Airdrop", ["EigenLayer ($500)", "Hyperliquid ($300)", "Linea ($200)"])
        if st.button("Claim via Private Bundle"):
            with st.spinner("Submitting..."):
                time.sleep(2)
            st.success(f"Claimed {drop}! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
