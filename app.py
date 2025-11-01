import streamlit as st
import json
import secrets
from eth_account import Account
from eth_account.messages import encode_defunct
import time
import streamlit.components.v1 as components

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")

# -----------------------------------------------------------
# ✅ MetaMask Signing Component (final stable version)
# -----------------------------------------------------------
def render_metamask_signer(message):
    encoded = json.dumps(message)
    JS_DOLLAR = "$"   # Prevent Python from swallowing JS template vars

    components.html(
        f"""
        <input type="text" id="sigbox" style="display:none;" />

        <script>
        async function signMsg() {{
            const provider = window.top?.ethereum;
            if (!provider) {{
                alert("MetaMask not detected — please install and refresh");
                return;
            }}

            try {{
                const accounts = await provider.request({{
                    method: "eth_requestAccounts"
                }});
                const from = accounts[0];

                const signature = await provider.request({{
                    method: "personal_sign",
                    params: [{encoded}, from]
                }});

                // Try to auto push signature into Streamlit field
                try {{
                    const box = document.getElementById("sigbox");
                    box.value = signature;
                    box.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }} catch (e) {{
                    console.log("Autofill failed, fallback UI used");
                }}

                // Render fallback + copy UI
                const div = document.createElement("div");
                div.style = "margin-top:10px;font-size:14px;font-family:monospace;";
                div.innerHTML = `
                    ✅ Signature generated<br><br>
                    <textarea id='sigText' style="width:100%;height:90px;">{JS_DOLLAR}{{signature}}</textarea><br>
                    <button id='copyBtn'
                        style="padding:6px 12px;margin-top:6px;background:#4CAF50;
                               border:none;color:white;border-radius:6px;cursor:pointer;">
                        Copy Signature
                    </button>
                `;
                document.body.appendChild(div);

                document.getElementById("copyBtn").onclick = () => {{
                    navigator.clipboard.writeText(signature);
                    alert("✅ Signature copied to clipboard");
                }};
            }}
            catch(err) {{
                alert("Sign error: " + err.message);
            }}
        }}
        </script>

        <button onclick="signMsg()"
            style="padding:12px 18px;border-radius:8px;background:#f6851b;
                   color:white;border:none;font-size:15px;cursor:pointer;margin-top:10px;">
            🧾 Sign with MetaMask
        </button>
        """,
        height=300
    )

# -----------------------------------------------------------
# ✅ Streamlit App UI
# -----------------------------------------------------------
tab1, tab2 = st.tabs(["Verify Wallet", "Claim Airdrop"])

with tab1:
    st.subheader("Step 1: Verify Wallet Ownership")

    compromised = st.text_input("Compromised wallet address", placeholder="0xDead...")
    safe = st.text_input("Safe recovery wallet", placeholder="0xSafe...")

    if st.button("Generate Message"):
        if not compromised or not safe:
            st.error("❌ Enter both wallet addresses")
        else:
            msg = f"I own {compromised} and authorize recovery to {safe} - {secrets.token_hex(8)}"
            st.session_state.message = msg
            st.code(msg)
            st.info("Now sign this message with MetaMask")

    if "message" in st.session_state:
        st.write("### ✍️ Sign Message")
        render_metamask_signer(st.session_state.message)

        signature = st.text_input("Signature (auto-filled after signing)", key="sig")

        if st.button("Verify Signature"):
            try:
                msg = encode_defunct(text=st.session_state.message)
                recovered = Account.recover_message(msg, signature=signature)

                if recovered.lower() == safe.lower():
                    st.success(f"✅ Verified — signer is {recovered[:6]}...{recovered[-4:]}")
                    st.session_state.verified = True
                else:
                    st.error("❌ Signature does not match safe wallet")
            except Exception as e:
                st.error(f"❌ Invalid signature: {e}")

with tab2:
    st.subheader("Step 2: Claim Airdrop")

    if not st.session_state.get("verified"):
        st.warning("⚠️ You must verify wallet ownership first.")
    else:
        drop = st.selectbox(
            "Select your eligible airdrop",
            ["EigenLayer ($500)", "Hyperliquid ($300)", "Linea ($200)"]
        )

        if st.button("Claim via Private Bundle"):
            with st.spinner("Submitting secure bundle..."):
                time.sleep(2)

            st.success(f"🎉 Claimed {drop}!\nTX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
