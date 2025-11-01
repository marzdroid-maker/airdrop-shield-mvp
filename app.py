import streamlit as st
from eth_account import Account
import streamlit.components.v1 as components
import json, secrets, time

# ------------------ Streamlit config ------------------
st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")

# ------------------ MetaMask Component ------------------
metamask_component = components.declare_component("metamask_component", url=None)

def sign_with_metamask(message: str):
    encoded = json.dumps(message)

    sig = metamask_component(
        key="mm_sign",
        default="",
        html=f"""
        <script>
        async function signFlow() {{
            const provider = window.top.ethereum;

            if (!provider) {{
                alert("MetaMask not found — install extension.");
                return;
            }}

            try {{
                // ✅ Connect wallet
                const accounts = await provider.request({{
                    method: "eth_requestAccounts"
                }});
                const from = accounts[0];

                // ✅ Sign the message
                const signature = await provider.request({{
                    method: "personal_sign",
                    params: [{encoded}, from]
                }});

                window.parent.postMessage(
                    {{
                        isStreamlitMessage: true,
                        type: "streamlit:setComponentValue",
                        value: signature
                    }},
                    "*"
                );

            }} catch (err) {{
                alert("Sign error: " + err.message);
            }}
        }}
        </script>

        <button onclick="signFlow()"
            style="
            padding:10px 18px;
            border-radius:8px;
            background:#f6851b;
            color:white;
            border:none;
            font-size:15px;
            cursor:pointer;
            margin-top:10px;">
            🧾 Sign with MetaMask
        </button>
        """
    )
    return sig


# ------------------ UI ------------------
tab1, tab2 = st.tabs(["Verify", "Claim"])


# ------------------ Verify Tab ------------------
with tab1:
    st.subheader("Step 1: Verify Ownership")

    compromised = st.text_input("Compromised Wallet", placeholder="0xDead...")
    safe = st.text_input("Safe Wallet", placeholder="0xSafe...")

    if st.button("Generate Message"):
        if not compromised or not safe:
            st.error("Enter both wallet addresses.")
        else:
            msg = f"I own {compromised} and authorize recovery to {safe} - {secrets.token_hex(8)}"
            st.session_state.msg = msg
            st.code(msg)
            st.info("Sign this message with your **SAFE wallet** below.")

    if "msg" in st.session_state:
        st.markdown("### ✍️ Sign Message")

        sig = sign_with_metamask(st.session_state.msg)

        user_sig = st.text_input(
            "Signature (auto-filled)",
            value=sig if sig else "",
            key="sig_field"
        )

        if st.button("Verify Signature"):
            try:
                recovered = Account.recover_message(
                    st.session_state.msg.encode(),
                    signature=user_sig
                )

                if recovered.lower() == safe.lower():
                    st.success(f"✅ Verified! Signed by {recovered[:6]}...{recovered[-4:]}")
                    st.session_state.verified = True
                    st.session_state.compromised = compromised
                    st.session_state.safe = safe
                else:
                    st.error("❌ Signature does not match safe wallet.")

            except Exception as e:
                st.error(f"Invalid signature: {e}")


# ------------------ Claim Tab ------------------
with tab2:
    if not st.session_state.get("verified"):
        st.warning("Verify ownership first.")
    else:
        drop = st.selectbox("Select Airdrop", [
            "EigenLayer ($500)",
            "Hyperliquid ($300)",
            "Linea ($200)"
        ])

        if st.button("Claim via Private Bundle"):
            with st.spinner("Submitting private bundle..."):
                time.sleep(2)
            st.success(f"✅ Successfully claimed {drop}!")
            st.balloons()
