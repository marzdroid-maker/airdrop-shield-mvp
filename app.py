# app.py
import json
import secrets
import time

import streamlit as st
import streamlit.components.v1 as components
from eth_account import Account
from eth_account.messages import encode_defunct


st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")


# ---------------- MetaMask signer (auto-fill, no overlay fallback) ----------------
def render_metamask_signer(message: str):
    """
    Opens MetaMask to sign `message`.
    - Primary path: injects signature into the last st.text_input on the page (our Signature box).
    - Fallback path: copies signature to clipboard and tells user to paste it.
      (This avoids overlays that can render oddly in Streamlit Cloud iframes.)
    """
    encoded = json.dumps(message)

    components.html(
        f"""
        <script>
        async function signMsg() {{
            const provider = window.top?.ethereum;
            if (!provider) {{
                alert("MetaMask not detected — please install the extension.");
                return;
            }}

            try {{
                const accounts = await provider.request({{ method: "eth_requestAccounts" }});
                const from = accounts[0];

                const signature = await provider.request({{
                    method: "personal_sign",
                    params: [{encoded}, from]
                }});

                // Try to auto-fill the Signature text input (last stTextInput on the page)
                let injected = false;
                try {{
                    const inputs = window.parent.document.querySelectorAll("input[data-testid='stTextInput']");
                    const sigInput = inputs[inputs.length - 1];  // our Signature box
                    if (sigInput) {{
                        sigInput.value = signature;
                        sigInput.dispatchEvent(new Event('input', {{ bubbles:true }}));
                        injected = true;
                    }}
                }} catch (e) {{
                    injected = false;
                }}

                if (!injected) {{
                    // Fallback: copy to clipboard and instruct user to paste
                    try {{
                        await navigator.clipboard.writeText(signature);
                        alert("✅ Signature copied to clipboard. Please paste it into the Signature field.");
                    }} catch (e) {{
                        alert("✅ Signature ready. If it wasn't auto-filled, paste it into the Signature field.");
                    }}
                }} else {{
                    alert("✅ Signature captured!");
                }}
            }} catch (err) {{
                alert("❌ Sign error: " + (err?.message || err));
            }}
        }}
        </script>

        <button onclick="signMsg()"
            style="padding:12px 18px; border-radius:8px; background:#f6851b; color:#fff;
                   border:none; font-size:15px; cursor:pointer; margin-top:8px;">
            🧾 Sign with MetaMask
        </button>
        """,
        height=70,
    )


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
            st.info("Now sign this message with MetaMask:")

    if "message" in st.session_state:
        st.write("### ✍️ Sign Message")
        render_metamask_signer(st.session_state.message)

        # Single signature box. JS tries to auto-fill this; otherwise user pastes.
        signature = st.text_input(
            "Signature (auto-filled after signing, or paste if prompted)",
            key="sig",
            placeholder="Will auto-fill after signing or paste here"
        )

        if st.button("Verify Signature"):
            if not signature.strip():
                st.warning("Paste your signature first.")
            else:
                try:
                    msg = encode_defunct(text=st.session_state.message)
                    recovered = Account.recover_message(msg, signature=signature)
                    if recovered.lower() == safe.lower():
                        st.success(f"✅ Verified! Signed by {recovered[:6]}...{recovered[-4:]}")
                        st.session_state.verified = True
                    else:
                        st.error("❌ Signature does not match the safe wallet you entered.")
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
            st.success(f"🎉 Claimed {drop}! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
