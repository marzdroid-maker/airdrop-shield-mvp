import streamlit as st
import json
import secrets
import time
from eth_account import Account
from eth_account.messages import encode_defunct
import streamlit.components.v1 as components

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")

# ----------------------------------------------------------------
# ✅ MetaMask component — single signature field auto-populated
# ----------------------------------------------------------------
def render_metamask_signer(message):
    encoded = json.dumps(message)
    components.html(
        f"""
        <script>
        async function signMsg() {{
            const provider = window.top?.ethereum;
            if (!provider) {{
                alert("MetaMask not found — install it first.");
                return;
            }}

            try {{
                const accounts = await provider.request({{ method: "eth_requestAccounts" }});
                const from = accounts[0];

                const signature = await provider.request({{
                    method: "personal_sign",
                    params: [{encoded}, from]
                }});

                // Push signature into Streamlit input
                const input = window.parent.document.querySelector("input[data-sig='1']");
                if (input) {{
                    input.value = signature;
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}

                alert("✅ Signature captured!");
            }} 
            catch(err) {{
                alert("❌ Sign error: " + err.message);
            }}
        }}
        </script>

        <button onclick="signMsg()"
            style="padding:12px 18px;
                   border-radius:8px;
                   background:#f6851b;
                   color:white;
                   border:none;
                   font-size:15px;
                   cursor:pointer;
                   margin-top:10px;">
            🧾 Sign with MetaMask
        </button>
        """,
        height=80
    )

# ----------------------------------------------------------------
# ✅ Tabs
# ----------------------------------------------------------------
tab1, tab2 = st.tabs(["Verify Wallet", "Claim Airdrop"])

# ----------------------------------------------------------------
# ✅ Verification Step
# ----------------------------------------------------------------
with tab1:
    st.subheader("Step 1: Verify Wallet")

    compromised = st.text_input("Compromised wallet", placeholder="0xDead...")
    safe = st.text_input("Safe wallet", placeholder="0xSafe...")

    if st.button("Generate Message"):
        if not compromised or not safe:
            st.error("❌ Enter both wallet addresses")
        else:
            msg = f"I own {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
            st.session_state.message = msg
            st.code(msg)
            st.info("Now sign this message in MetaMask ↓")

    # If message exists, show signing box
    if "message" in st.session_state:
        st.write("### ✍️ Sign Message")
        render_metamask_signer(st.session_state.message)

        signature = st.text_input(
            "Signature (auto-filled)",
            key="sig",
            placeholder="Will auto-fill after signing",
            attrs={"data-sig": "1"}   # ← JS will target this
        )

        if st.button("Verify Signature") and signature:
            try:
                msg = encode_defunct(text=st.session_state.message)
                recovered = Account.recover_message(msg, signature=signature)

                if recovered.lower() == safe.lower():
                    st.success(f"✅ Verified! Signed by {recovered[:6]}...{recovered[-4:]}")
                    st.session_state.verified = True
                else:
                    st.error("❌ Signature does not match safe wallet.")
            except Exception as e:
                st.error(f"❌ Invalid signature: {e}")

# ----------------------------------------------------------------
# ✅ Airdrop Claim Step
# ----------------------------------------------------------------
with tab2:
    st.subheader("Step 2: Claim Airdrop")

    if not st.session_state.get("verified"):
        st.warning("⚠️ Verify wallet ownership first.")
    else:
        drop = st.selectbox("Choose your airdrop", ["EigenLayer ($500)", "Hyperliquid ($300)", "Linea ($200)"])

        if st.button("Claim via Private Bundle"):
            with st.spinner("Submitting secure bundle..."):
                time.sleep(2)
            st.success(f"🎉 Claimed {drop}! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
