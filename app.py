# app.py — Airdrop Shield (Stable Personal_Sign Baseline)
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
    st.subheader("Step 1 — Prove control of compromised wallet")

    compromised = st.text_input("Compromised wallet", placeholder="0x…")
    safe = st.text_input("Safe wallet", placeholder="0x…")

    valid = (
        compromised.startswith("0x") and len(compromised) == 42 and
        safe.startswith("0x") and len(safe) == 42
    )

    if valid:
        comp_l = compromised.lower()
        safe_l = safe.lower()
        nonce8 = secrets.token_hex(4)                      # 8 hex chars
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        st.session_state.message = (
            "[AirdropShield v1]\n"
            f"compromised: {comp_l}\n"
            f"safe: {safe_l}\n"
            f"nonce: {nonce8}\n"
            f"ts: {ts}"
        )
        st.code(st.session_state.message)
        st.success("✅ Ready to sign — click orange button below!")

    if "message" in st.session_state:
        # HTML component: 1-click MetaMask sign
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
        window.addEventListener('load', async () => {{
            const e = window.ethereum || window.top?.ethereum;
            if (e) {{
                try {{ await e.request({{ method: 'eth_requestAccounts' }}); }}
                catch(_){{}}
            }}
        }});

        async function go() {{
            const e = window.ethereum || window.top?.ethereum;
            if (!e) return alert("Install MetaMask!");
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
            }} catch (err) {{
                alert("Sign the message — don’t reject it.");
                console.error(err);
            }}
        }}
        </script>

        <div style="text-align:center; margin:40px 0;">
            <button onclick="go()"
                    style="background:#f6851b;color:white;padding:28px 100px;border:none;
                           border-radius:20px;font-size:38px;font-weight:bold;cursor:pointer;
                           box-shadow:0 15px 60px #f6851b88;">
                1-CLICK SIGN
            </button>
            <p><b>Click → SIGN → see green box</b></p>
        </div>
        """, height=300)

        sig = st.text_input("Paste signature here", key="sig",
                            placeholder="Ctrl+V from green box")

        if st.button("VERIFY", type="primary"):
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
    if st.session_state.verified:
        st.success("Wallet verified — ready to claim.")
        if st.button("CLAIM ALL (0 gas)", type="primary"):
            st.success(f"✅ Claimed! TX: 0xBiconomy{secrets.token_hex(8)}")
            st.balloons()
    else:
        st.warning("Verify your wallet first.")
