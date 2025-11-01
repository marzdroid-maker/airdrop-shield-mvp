# app.py
import streamlit as st
from eth_account import Account
import secrets
import time
import json
import streamlit.components.v1 as components

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")

# ----------------------------------------------------
# ✅ MetaMask Sign Component (calls personal_sign)
# ----------------------------------------------------
def metamask_sign(message):
    encoded = json.dumps(message)

    component = components.html(
        f"""
        <script>
        async function signMessage() {{
            if (typeof window.ethereum === 'undefined') {{
                window.parent.postMessage({{"signature": null, "error": "MetaMask not detected"}}, "*");
                return;
            }}

            try {{
                const accounts = await window.ethereum.request({{
                    method: 'eth_requestAccounts'
                }});
                const from = accounts[0];

                const sig = await window.ethereum.request({{
                    method: 'personal_sign',
                    params: [{encoded}, from]
                }});

                window.parent.postMessage({{"signature": sig}}, "*");
            }} catch (err) {{
                window.parent.postMessage({{"signature": null, "error": err.message}}, "*");
            }}
        }}

        window.addEventListener("message", (event) => {{
            const data = event.data;
            if (!data) return;
            if (data.type === "streamlit:render") return;

            if (data.signature !== undefined) {{
                const out = {{
                    "isStreamlitMessage": true,
                    "type": "streamlit:setComponentValue",
                    "value": data.signature
                }};
                window.parent.postMessage(out, "*");
            }}
        }});
        </script>

        <button onclick="signMessage()" 
        style="padding:10px 18px;border-radius:8px;background:#f6851b;color:white;border:none;font-size:15px;cursor:pointer;">
            🧾 Sign with MetaMask
        </button>
        """,
        height=80,
    )
    return component

# ----------------------------------------------------
# ✅ Tabs
# ----------------------------------------------------
tab1, tab2 = st.tabs(["Verify", "Claim"])

# ----------------------------------------------------
# ✅ Verify Tab
# ----------------------------------------------------
with tab1:
    st.subheader("Step 1: Verify Ownership")
    compromised = st.text_input("Compromised Wallet", placeholder="0xDead...")
    safe = st.text_input("Safe Wallet", placeholder="0xSafe...")

    if st.button("Generate Message"):
        if not compromised or not safe:
            st.error("Enter both wallets")
        else:
            msg = f"I own {compromised} and authorize recovery to {safe} - {secrets.token_hex(8)}"
            st.session_state.message = msg
            st.code(msg)
            st.info("Click below to sign this with your **safe wallet**")

    if "message" in st.session_state:
        st.markdown("### ✍️ Sign Message")
        signature = metamask_sign(st.session_state.message)

        user_sig = st.text_input("Signature (auto-filled after signing)", key="sig")

        if st.button("Verify Signature"):
            try:
                recovered = Account.recover_message(
                    st.session_state.message.encode("utf-8"),
                    signature=user_sig
                )
                if recovered.lower() == safe.lower():
                    st.success(f"✅ Verified! Signed by {recovered[:6]}...{recovered[-4:]}")
                    st.session_state.verified = True
                    st.session_state.compromised = compromised
                    st.session_state.safe = safe
                else:
                    st.error("❌ Signature does not match safe wallet")
            except Exception as e:
                st.error(f"Invalid signature: {e}")

# ----------------------------------------------------
# ✅ Claim Tab
# ----------------------------------------------------
with tab2:
    if not st.session_state.get("verified"):
        st.warning("Verify first.")
    else:
        drop = st.selectbox("Airdrop", ["EigenLayer ($500)", "Hyperliquid ($300)", "Linea ($200)"])

        if st.button("Claim via Private Bundle"):
            with st.spinner("Submitting..."):
                time.sleep(2)
            st.success(f"🎉 Claimed {drop}! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
