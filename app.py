# app.py
import streamlit as st
import json, secrets, time
from eth_account import Account
from eth_account.messages import encode_defunct
import streamlit.components.v1 as components

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")

# ---------------- MetaMask signer (single-box, cloud-safe) ----------------
def render_metamask_signer(message: str):
    encoded = json.dumps(message)

    components.html(
        f"""
        <script>
        function showFallback(signature) {{
            // Build a lightweight overlay with textarea + copy
            const overlay = document.createElement('div');
            overlay.style = `
                position:fixed; inset:0; background:rgba(0,0,0,0.55);
                display:flex; align-items:center; justify-content:center; z-index:99999;`;
            const card = document.createElement('div');
            card.style = `
                width:min(680px, 92vw); background:#111; color:#fff; border-radius:10px;
                border:1px solid #333; padding:16px; font-family:system-ui, -apple-system, Segoe UI, Roboto;`;
            card.innerHTML = `
                <div style="font-size:16px; margin-bottom:8px;">Signature (copy and paste into the field below)</div>
                <textarea id="sig_fallback" style="width:100%; height:120px; background:#0e0e0e; color:#eee; border:1px solid #333; border-radius:8px; padding:10px;">${{signature}}</textarea>
                <div style="display:flex; gap:10px; margin-top:10px;">
                    <button id="copy_btn" style="padding:8px 14px; background:#4caf50; color:#fff; border:none; border-radius:8px; cursor:pointer;">Copy</button>
                    <button id="close_btn" style="padding:8px 14px; background:#666; color:#fff; border:none; border-radius:8px; cursor:pointer;">Close</button>
                </div>`;
            overlay.appendChild(card);
            document.body.appendChild(overlay);

            document.getElementById('copy_btn').onclick = async () => {{
                try {{
                    const t = document.getElementById('sig_fallback');
                    t.select(); t.setSelectionRange(0, 99999);
                    await navigator.clipboard.writeText(t.value);
                }} catch (e) {{ /* ignore */ }}
                document.body.removeChild(overlay);
                alert("✅ Signature copied. Paste it into the Signature field.");
            }};
            document.getElementById('close_btn').onclick = () => {{
                document.body.removeChild(overlay);
            }};
        }}

        async function signMsg() {{
            const provider = window.top?.ethereum;
            if (!provider) {{ alert("MetaMask not found — install extension."); return; }}

            try {{
                const accounts = await provider.request({{ method: "eth_requestAccounts" }});
                const from = accounts[0];

                const signature = await provider.request({{
                    method: "personal_sign",
                    params: [{encoded}, from]
                }});

                // Find Streamlit text inputs; use the LAST one on the page (the Signature field)
                const inputs = window.parent.document.querySelectorAll("input[data-testid='stTextInput']");
                const sigInput = inputs[inputs.length - 1];

                let injected = false;
                try {{
                    if (sigInput) {{
                        sigInput.value = signature;
                        sigInput.dispatchEvent(new Event('input', {{ bubbles:true }}));
                        injected = true;
                    }}
                }} catch (e) {{
                    injected = false;
                }}

                if (!injected) {{
                    // Streamlit Cloud sandbox might block DOM events — show fallback
                    showFallback(signature);
                }} else {{
                    alert("✅ Signature captured.");
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
        height=90,
    )

# ---------------- UI ----------------
tab1, tab2 = st.tabs(["Verify Wallet", "Claim Airdrop"])

with tab1:
    st.subheader("Step 1: Verify Wallet")

    compromised = st.text_input("Compromised wallet", placeholder="0xDead...")
    safe = st.text_input("Safe wallet", placeholder="0xSafe...")

    if st.button("Generate Message"):
        if not compromised or not safe:
            st.error("Enter both wallet addresses.")
        else:
            msg = f"I own {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
            st.session_state.message = msg
            st.code(msg)
            st.info("Sign this message using MetaMask:")

    if "message" in st.session_state:
        st.write("### ✍️ Sign Message")
        render_metamask_signer(st.session_state.message)

        # Single signature box — JS will auto-fill this (or you can paste)
        signature = st.text_input(
            "Signature (auto-filled after signing)",
            key="sig",
            placeholder="Will auto-fill after signing (or paste here)"
        )

        if st.button("Verify Signature"):
            try:
                msg = encode_defunct(text=st.session_state.message)
                recovered = Account.recover_message(msg, signature=signature)
                if recovered.lower() == (safe or "").lower():
                    st.success(f"✅ Verified! Signed by {recovered[:6]}...{recovered[-4:]}")
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
        drop = st.selectbox("Eligible airdrop", ["EigenLayer ($500)", "Hyperliquid ($300)", "Linea ($200)"])
        if st.button("Claim via Private Bundle"):
            with st.spinner("Submitting secure bundle..."):
                time.sleep(2)
            st.success(f"🎉 Claimed {drop}! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
