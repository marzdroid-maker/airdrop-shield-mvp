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


# ---------------- MetaMask Signer with Auto-Fill ----------------
def render_metamask_signer(message: str):
    """
    Renders a button that opens MetaMask.
    Returns the signature (or None) via st_javascript + postMessage.
    """
    # Inject button + JS
    components.html(
        f"""
        <script>
        async function signAndSend() {{
            if (!window.ethereum) {{
                alert("MetaMask not detected. Please install the extension.");
                return;
            }}
            try {{
                const accounts = await window.ethereum.request({{ 
                    method: 'eth_requestAccounts' 
                }});
                const signature = await window.ethereum.request({{
                    method: 'personal_sign',
                    params: ['{message}', accounts[0]]
                }});
                // Send signature back to Streamlit
                window.parent.postMessage({{ 
                    type: 'SIGNATURE_FROM_METAMASK', 
                    signature: signature 
                }}, '*');
            }} catch (err) {{
                alert("Signing failed: " + (err.message || err));
            }}
        }}
        </script>

        <button onclick="signAndSend()"
                style="background:#f6851b; color:white; padding:12px 24px; 
                       border:none; border-radius:8px; font-size:16px; 
                       cursor:pointer; margin:10px 0;">
            Sign with MetaMask
        </button>
        """,
        height=80,
    )

    # Listen for signature from JS
    result = st_javascript("""
        new Promise((resolve) => {
            const handler = (event) => {
                if (event.data && event.data.type === 'SIGNATURE_FROM_METAMASK') {
                    resolve(event.data.signature);
                    window.removeEventListener('message', handler);
                }
            };
            window.addEventListener('message', handler);
            // Timeout after 60s
            setTimeout(() => {
                resolve(null);
                window.removeEventListener('message', handler);
            }, 60000);
        });
    """, key=f"sign_{secrets.token_hex(4)}")

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
            st.code(msg, language="text")
            st.info("Click below to sign with MetaMask (your **safe wallet**):")

    if "message" in st.session_state:
        # Auto-capture signature
        auto_sig = render_metamask_signer(st.session_state.message)

        # Show auto-filled or manual input
        if auto_sig:
            st.text_input(
                "Signature (auto-filled from MetaMask)",
                value=auto_sig,
                disabled=True,
                key="auto_sig"
            )
            signature = auto_sig
        else:
            signature = st.text_input(
                "Signature (paste if not auto-filled)",
                placeholder="0x...",
                key="manual_sig"
            )

        if st.button("Verify Signature"):
            if not signature or not signature.startswith("0x"):
                st.warning("Please sign with MetaMask first.")
            else:
                try:
                    msg_hash = encode_defunct(text=st.session_state.message)
                    recovered = Account.recover_message(msg_hash, signature=signature)
                    if recovered.lower() == safe.lower():
                        st.success(f"Verified! Signed by {recovered[:6]}...{recovered[-4:]}")
                        st.session_state.verified = True
                        st.session_state.compromised = compromised
                        st.session_state.safe = safe
                    else:
                        st.error("Signature does not match the safe wallet.")
                except Exception as e:
                    st.error(f"Invalid signature: {e}")


with tab2:
    st.subheader("Step 2: Claim Airdrop")

    if not st.session_state.get("verified"):
        st.warning("Verify wallet ownership first.")
    else:
        drop = st.selectbox(
            "Eligible airdrop",
            ["EigenLayer ($500)", "Hyperliquid ($300)", "Linea ($200)"]
        )

        if st.button("Claim via Private Bundle"):
            with st.spinner("Submitting secure bundle..."):
                time.sleep(2)
            st.success(f"Claimed {drop}! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
