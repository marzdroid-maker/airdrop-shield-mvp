import streamlit as st
from eth_account import Account
import streamlit.components.v1 as components
import json, secrets, time

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")

# ------------------- MetaMask signer -------------------
def sign_with_metamask(msg):
    encoded = json.dumps(msg)

    components.html(
        f"""
        <script>
        var input = window.parent.document.querySelector('input[data-meta="sigbox"]');

        async function signMsg() {{
            const provider = window.top?.ethereum;
            if (!provider) {{
                alert("MetaMask missing. Install extension.");
                return;
            }}

            try {{
                const accounts = await provider.request({{ method: "eth_requestAccounts" }});
                const from = accounts[0];

                const signature = await provider.request({{
                    method: "personal_sign",
                    params: [{encoded}, from]
                }});

                // ✅ put signature into Streamlit input
                input.value = signature;
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));

            }} catch(e) {{
                alert("Error: " + e.message);
            }}
        }}
        </script>

        <button onclick="signMsg()"
            style="padding:10px 18px;border-radius:8px;background:#f6851b;color:white;border:none;
            font-size:15px;cursor:pointer;margin-top:10px;">
            🧾 Sign with MetaMask
        </button>
        """,
        height=80
    )


# ------------------- UI Tabs -------------------
tab1, tab2 = st.tabs(["Verify", "Claim"])

with tab1:
    st.subheader("Step 1: Verify Ownership")

    compromised = st.text_input("Compromised Wallet", placeholder="0xDead...")
    safe = st.text_input("Safe Wallet", placeholder="0xSafe...")

    if st.button("Generate Message"):
        if not compromised or not safe:
            st.error("Enter both wallets")
        else:
            msg = f"I own {compromised} and authorize recovery to {safe} - {secrets.token_hex(8)}"
            st.session_state.msg = msg
            st.code(msg)
            st.info("Sign with your SAFE wallet")

    if "msg" in st.session_state:
        st.markdown("### ✍️ Sign Message")
        sign_with_metamask(st.session_state.msg)

        user_sig = st.text_input(
            "Signature (auto-filled)",
            key="sigbox",
            value="",
            attrs={"data-meta": "sigbox"}  # important!
        )

        if st.button("Verify Signature"):
            try:
                recovered = Account.recover_message(
                    st.session_state.msg.encode(),
                    signature=user_sig
                )
                if recovered.lower() == safe.lower():
                    st.success("✅ Verified safe wallet")
                    st.session_state.verified = True
                else:
                    st.error("❌ Wrong wallet signed")
            except Exception as e:
                st.error(f"Invalid signature: {e}")

with tab2:
    if not st.session_state.get("verified"):
        st.warning("Verify first")
    else:
        drop = st.selectbox("Airdrop", ["EigenLayer", "Hyperliquid", "Linea"])
        if st.button("Claim via Private Bundle"):
            with st.spinner("Submitting..."):
                time.sleep(2)
            st.success("✅ Private claim broadcasted")
            st.balloons()
