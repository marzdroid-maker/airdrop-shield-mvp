# app.py — Airdrop Shield (Stable personal_sign version with clear instructions)
import secrets
from datetime import datetime, timezone
import streamlit as st
from eth_account import Account
from eth_account.messages import encode_defunct

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️")
st.title("🛡️ Airdrop Shield — Secure Off-Chain Proof")

if "verified" not in st.session_state:
    st.session_state.verified = False

tab1, tab2 = st.tabs(["Verify", "Claim"])

with tab1:
    st.subheader("Step 1 — Prove you control the compromised wallet")

    st.markdown("""
    **How it works**

    1️⃣ Enter both wallet addresses below  
    2️⃣ Click **1-CLICK SIGN** — MetaMask will open and ask you to sign a short message  
    3️⃣ After signing, a **green box** will appear with your signature text  
    4️⃣ **Copy everything** from that box (Ctrl + C)  
    5️⃣ Paste it into the field labeled **Paste signature here**  
    6️⃣ Click **VERIFY** to confirm wallet ownership
    """)

    compromised = st.text_input("Compromised wallet", placeholder="0x…")
    safe = st.text_input("Safe wallet", placeholder="0x…")

    valid = (
        compromised.startswith("0x") and len(compromised) == 42 and
        safe.startswith("0x") and len(safe) == 42
    )

    if valid:
        comp_l = compromised.lower()
        safe_l = safe.lower()
        nonce8 = secrets.token_hex(4)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        st.session_state.message = (
            "[AirdropShield v1]\n"
            f"compromised: {comp_l}\n"
            f"safe: {safe_l}\n"
            f"nonce: {nonce8}\n"
            f"ts: {ts}"
        )

        st.code(st.session_state.message, language="text")
        st.success("✅ Ready — click the orange button below to sign with MetaMask")

    if "message" in st.session_state:
        st.components.v1.html(f"""
        <style>
            #sigBox {{
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                width: 90%;
                max-width: 700px;
                height: 180px;
                padding: 16px;
                background: #000;
                color: #0f0;
                border: 4px solid #0f0;
                border-radius: 14px;
                font-family: monospace;
                font-size: 15px;
                z-index: 9999;
                box-shadow: 0 0 30px #0f0;
                display: none;
            }}
            #sigBox.show {{ display: block; }}
        </style>

        <script>
        // auto-connect on load
        window.addEventListener('load', async () => {{
            const e = window.ethereum || window.top?.ethereum;
            if (e) {{
                try {{ await e.request({{ method: 'eth_requestAccounts' }}); }}
                catch(_){{}}
            }}
        }});

        async function go() {{
            const e = window.ethereum || window.top?.ethereum;
            if (!e) return alert("Please install MetaMask in this browser profile.");
            try {{
                const [a] = await e.request({{ method:'eth_requestAccounts' }});
                const s = await e.request({{
                    method:'personal_sign',
                    params:['{st.session_state.message}', a]
                }});
                let box = document.getElementById('sigBox');
                if (!box) {{
                    box = document.createElement('textarea');
                    box.id = 'sigBox';
                    box.readOnly = true;
                    document.body.appendChild(box);
                }}
                box.value = s;
                box.classList.add('show');
                box.scrollIntoView({{behavior:'smooth',block:'center'}});
                alert("✅ Signature created! Scroll down, copy the green text, and paste it into the field.");
            }} catch (err) {{
                alert("❌ Signing was cancelled or failed. Please retry.");
                console.error(err);
            }}
        }}
        </script>

        <div style="text-align:center; margin:40px 0;">
            <button onclick="go()"
                    style="background:#f6851b;color:white;padding:26px 100px;border:none;
                           border-radius:20px;font-size:36px;font-weight:bold;cursor:pointer;
                           box-shadow:0 15px 60px #f6851b88;">
                1-CLICK SIGN
            </button>
            <p><b>Click → Sign in MetaMask → Copy from green box → Paste below</b></p>
        </div>
        """, height=320)

        sig = st.text_input("Paste signature here", key="sig",
                            placeholder="Ctrl + V from green box")

        if st.button("VERIFY SIGNATURE", type="primary"):
            try:
                recovered = Account.recover_message(
                    encode_defunct(text=st.session_state.message),
                    signature=sig
                )
                if recovered.lower() == compromised.lower():
                    st.success("✅ Verified — you control the compromised wallet!")
                    st.session_state.verified = True
                    st.balloons()
                else:
                    st.error(f"❌ Recovered {recovered}, expected {compromised}")
            except Exception as e:
                st.error(f"Verification failed: {e}")

with tab2:
    st.subheader("Step 2 — Claim (simulated)")
    if st.session_state.verified:
        st.success("Wallet verified — safe to claim.")
        if st.button("CLAIM ALL (0 gas)", type="primary"):
            st.success(f"✅ Claim simulated — TX: 0xBiconomy{secrets.token_hex(8)}")
            st.balloons()
    else:
        st.warning("Please verify ownership first.")
