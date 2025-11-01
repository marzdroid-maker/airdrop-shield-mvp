import streamlit as st
import json, secrets, time
from eth_account import Account
from eth_account.messages import encode_defunct
import streamlit.components.v1 as components

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")


# ---------------- MetaMask Signing Component ----------------
def render_metamask_signer(message: str):
    encoded = json.dumps(message)

    components.html(
        f"""
        <script>
        function showFallback(signature) {{
            const overlay = document.createElement('div');
            overlay.style = `
                position:fixed; inset:0;
                background:rgba(0,0,0,0.6);
                display:flex; align-items:center; justify-content:center;
                z-index:999999;
            `;

            const box = document.createElement('div');
            box.style = `
                width:90%; max-width:500px;
                background:#1c1c1c; color:#fff;
                padding:18px; border-radius:10px;
                font-family:system-ui, sans-serif;
                border:1px solid #333;
            `;

            box.innerHTML = `
                <div style="font-size:16px; margin-bottom:8px;">
                    ✅ Signature ready — copy & paste below
                </div>

                <textarea id="sigFB"
                    style="width:100%; height:120px; border-radius:8px;
                        background:#0e0e0e; color:#eee; padding:10px;
                        border:1px solid #444; resize:none;">${{signature}}</textarea>

                <div style="display:flex; gap:10px; margin-top:10px; justify-content:flex-end;">
                    <button id="copyFB"
                        style="padding:8px 14px; background:#4caf50; border:none;
                               border-radius:6px; cursor:pointer; color:white;">Copy</button>
                    <button id="closeFB"
                        style="padding:8px 14px; background:#666; border:none;
                               border-radius:6px; cursor:pointer; color:white;">Close</button>
                </div>
            `;

            overlay.appendChild(box);
            document.body.appendChild(overlay);

            document.getElementById("copyFB").onclick = async () => {{
                const ta = document.getElementById("sigFB");
                ta.select(); ta.setSelectionRange(0, 999999);
                try {{ await navigator.clipboard.writeText(ta.value); }} catch (e) {{}}
                document.body.removeChild(overlay);
                alert("✅ Signature copied — paste into the field.");
            }};

            document.getElementById("closeFB").onclick = () => {{
                document.body.removeChild(overlay);
            }};
        }}

        async function signMsg() {{
            const provider = window.top?.ethereum;
            if (!provider) {{
                alert("MetaMask not detected. Install extension first.");
                return;
            }}

            try {{
                const accounts = await provider.request({{ method: "eth_requestAccounts" }});
                const from = accounts[0];

                const signature = await provider.request({{
                    method: "personal_sign",
                    params: [{encoded}, from]
                }});

                // Find Streamlit text inputs. The last one is our signature box.
                const inputs = window.parent.document.querySelectorAll("input[data-testid='stTextInput']");
                const input = inputs[inputs.length - 1];

                let ok = false;
                try {{
                    if (input) {{
                        input.value = signature;
                        input.dispatchEvent(new Event('input', {{ bubbles:true }}));
                        ok = true;
                    }}
                }} catch (e) {{
                    ok = false;
                }}

                if (!ok) showFallback(signature);
                else alert("✅ Signature captured.");

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
            st.info("Now sign this message in MetaMask ↓")

    if "message" in st.session_state:
        st.write("### ✍️ Sign Message")
        render_metamask_signer(st.session_state.message)

        signature = st.text_input(
            "Signature (auto-filled or paste if popup appeared)",
            key="sig",
            placeholder="Will auto-fill after signing"
        )

        if st.button("Verify Signature"):
            try:
                msg = encode_defunct(text=st.session_state.message)
                recovered = Account.recover_message(msg, signature=signature)

                if recovered.lower() == safe.lower():
                    st.success(f"✅ Verified! Signed by {recovered[:6]}...{recovered[-4:]}")
                    st.session_state.verified = True
                else:
                    st.error("❌ Signature does not match safe wallet")
            except Exception as e:
                st.error(f"Invalid signature: {e}")


with tab2:
    st.subheader("Step 2: Claim Airdrop")

    if not st.session_state.get("verified"):
        st.warning("Verify wallet ownership first")
    else:
        drop = st.selectbox("Eligible airdrop", ["EigenLayer ($500)", "Hyperliquid ($300)", "Linea ($200)"])

        if st.button("Claim via Private Bundle"):
            with st.spinner("Submitting secure bundle..."):
                time.sleep(2)
            st.success(f"🎉 Claimed {drop}! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
