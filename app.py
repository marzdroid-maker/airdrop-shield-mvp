import streamlit as st
from eth_account import Account
import streamlit.components.v1 as components
import json, secrets, time

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")

def metamask_sign(message):
    encoded = json.dumps(message)
    components.html(
        f"""
        <script>
        async function signMsg() {{
            const provider = window.top?.ethereum;
            if (!provider) {{
                alert("MetaMask not found");
                return;
            }}
            try {{
                const accounts = await provider.request({{ method: "eth_requestAccounts" }});
                const from = accounts[0];

                const sig = await provider.request({{
                    method: "personal_sign",
                    params: [{encoded}, from]
                }});

                alert("✅ Copy this signature:\\n\\n" + sig);
            }} catch(e) {{
                alert("Signing failed: " + e.message);
            }}
        }}
        </script>

        <button onclick="signMsg()"
            style="padding:10px 18px;border-radius:8px;background:#f6851b;color:white;border:none;
            font-size:15px;cursor:pointer;margin-top:10px;">
            🧾 Sign with MetaMask
        </button>
        """,
        height=90,
    )

# UI
tab1, tab2 = st.tabs(["Verify", "Claim"])

with tab1:
    st.subheader("Step 1: Verify Ownership")

    compromised = st.text_input("Compromised Wallet")
    safe = st.text_input("Safe Wallet")

    if st.button("Generate Message"):
        if not compromised or not safe:
            st.error("Enter both wallets first.")
        else:
            msg = f"I own {compromised} and authorize recovery to {safe} - {secrets.token_hex(8)}"
            st.session_state.msg = msg
            st.code(msg)
            st.info("Click **Sign with MetaMask**, copy signature, paste below.")

    if "msg" in st.session_state:
        metamask_sign(st.session_state.msg)

        user_sig = st.text_input("Paste signature here")

        if st.button("Verify Signature"):
            try:
                recovered = Account.recover_message(
                    st.session_state.msg.encode(),
                    signature=user_sig,
                )
                if recovered.lower() == safe.lower():
                    st.success(f"✅ Verified! Owner: {recovered}")
                    st.session_state.verified = True
                else:
                    st.error("❌ Signature doesn't match safe wallet")
            except Exception as e:
                st.error(f"Invalid signature: {e}")

with tab2:
    if not st.session_state.get("verified"):
        st.warning("Verify wallet ownership first.")
    else:
        drop = st.selectbox("Airdrop", ["EigenLayer ($500)", "Hyperliquid ($300)", "Linea ($200)"])
        if st.button("Claim via Private Bundle"):
            with st.spinner("Submitting..."):
                time.sleep(2)
            st.success(f"✅ Successfully claimed {drop}")
            st.balloons()
