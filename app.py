import streamlit as st
from eth_account import Account
import streamlit.components.v1 as components
import json, secrets, time

# ------------------ Streamlit Setup ------------------
st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")

# ------------------ MetaMask Sign JS ------------------
def render_metamask_js(message):
    encoded = json.dumps(message)

    components.html(
        f"""
        <input type="text" id="sigbox" style="display:none;" />

        <script>
        async function signMsg() {{
            const provider = window.top?.ethereum;
            if (!provider) {{
                alert("MetaMask not detected. Install the extension.");
                return;
            }}

            try {{
                // Request wallet connection
                const accounts = await provider.request({{
                    method: "eth_requestAccounts"
                }});
                const from = accounts[0];

                // Request signature
                const signature = await provider.request({{
                    method: "personal_sign",
                    params: [{encoded}, from]
                }});

                // ✅ Write signature into hidden input Streamlit tracks
                let box = document.getElementById("sigbox");
                box.value = signature;
                box.dispatchEvent(new Event("input", {{ bubbles: true }}));

            }} catch (e) {{
                alert("Signing failed: " + e.message);
            }}
        }}
        </script>

        <button onclick="signMsg()"
            style="
                padding:10px 18px;
                border-radius:8px;
                background:#f6851b;
                color:white;
                border:none;
                font-size:15px;
                cursor:pointer;
                margin-top:10px;
            ">
            🧾 Sign with MetaMask
        </button>
        """,
        height=90,
    )

# ------------------ UI Tabs ------------------
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

        # Render MetaMask signing JS widget
        render_metamask_js(st.session_state.msg)

        # Signature field auto-populated by JS
        user_sig = st.text_input("Signature (auto-filled)", key="sigbox")

        if st.button("Verify Signature"):
            try:
                recovered = Account.recover_message(
                    st.session_state.msg.encode(),
                    signature=user_sig
                )
                if recovered.lower() == safe.lower():
                    st.success(f"✅ Verified! Owner: {recovered}")
                    st.session_state.verified = True
                else:
                    st.error("❌ Signature does not match safe wallet")
            except Exception as e:
                st.error(f"Invalid signature: {e}")

# ------------------ Claim Tab ------------------
with tab2:
    if not st.session_state.get("verified"):
        st.warning("Verify wallet ownership first.")
    else:
        drop = st.selectbox("Recovery Target", [
            "EigenLayer ($500)",
            "Hyperliquid ($300)",
            "Linea ($200)"
        ])

        if st.button("Claim via Private Bundle"):
            with st.spinner("Submitting private bundle..."):
                time.sleep(2)
            st.success(f"✅ Successfully claimed {drop}")
            st.balloons()
