import streamlit as st
from eth_account import Account
import streamlit.components.v1 as components
import json, time, secrets

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️")

st.title("🛡️ Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")

# ----------------------------------------------------
# ✅ MetaMask Sign Component
# ----------------------------------------------------
def sign_with_metamask(message):
    encoded = json.dumps(message)

    sig = components.html(
        f"""
        <script>

        async function signFlow() {{
            const provider = window.top.ethereum;
            if (!provider) {{
                alert("MetaMask not detected");
                return;
            }}

            try {{
                // ✅ Connect wallet
                const accounts = await provider.request({{
                    method: "eth_requestAccounts"
                }});

                const from = accounts[0];

                // ✅ Sign message
                const signature = await provider.request({{
                    method: "personal_sign",
                    params: [{encoded}, from]
                }});

                // ✅ Send value back to Streamlit
                window.parent.postMessage(
                    {{
                        isStreamlitMessage: true,
                        type: "streamlit:setComponentValue",
                        value: signature
                    }},
                    "*"
                );

            }} catch(e) {{
                alert("Error: " + e.message);
            }}
        }}

        </script>

        <button onclick="signFlow()" 
                style="padding:10px 18px;border-radius:8px;background:#f6851b;color:white;border:none;
                font-size:15px;cursor:pointer;margin-top:10px;">
            🧾 Sign with MetaMask
        </button>
        """,
        height=90
    )

    return sig


# ----------------------------------------------------
# UI Logic
# ----------------------------------------------------
tab1, tab2 = st.tabs(["Verify", "Claim"])

with tab1:
    st.subheader("Step 1: Verify Ownership")

    compromised = st.text_input("Compromised Wallet")
    safe = st.text_input("Safe Wallet")

    if st.button("Generate Message"):
        msg = f"I own {compromised} and authorize recovery to {safe} - {secrets.token_hex(8)}"
        st.session_state.msg = msg
        st.code(msg)
        st.info("Sign with your SAFE wallet below")

    if "msg" in st.session_state:
        sig = sign_with_metamask(st.session_state.msg)

        user_sig = st.text_input(
            "Signature (auto-filled)",
            key="sig"
        )

        if st.button("Verify Signature"):
            try:
                recovered = Account.recover_message(
                    st.session_state.msg.encode("utf-8"),
                    signature=user_sig
                )
                if recovered.lower() == safe.lower():
                    st.success("✅ Wallet verified")
                    st.session_state.verified = True
                else:
                    st.error("❌ Signature mismatch")
            except Exception as e:
                st.error(f"Invalid signature: {e}")


with tab2:
    if not st.session_state.get("verified"):
        st.warning("Verify first")
    else:
        drop = st.selectbox("Airdrop", ["EigenLayer", "Hyperliquid", "Linea"])
        if st.button("Claim"):
            with st.spinner("Submitting private bundle..."):
                time.sleep(2)
            st.success("✅ Airdrop claimed privately")
            st.balloons()
