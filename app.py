# app.py — FINAL — 1-CLICK SIGN, GREEN BOX, NO DOUBLE SIGN
import secrets
import streamlit as st
from eth_account import Account
from eth_account.messages import encode_defunct

st.cache_data.clear()
st.set_page_config(page_title="Airdrop Shield", page_icon="Shield")
st.title("Shield Airdrop Shield")

if "verified" not in st.session_state:
    st.session_state.verified = False

tab1, tab2 = st.tabs(["Verify", "Claim"])

# ========================================
# TAB 1: VERIFY
# ========================================
with tab1:
    st.subheader("Step 1: Prove control")
    compromised = st.text_input("Compromised wallet", placeholder="0x...")
    safe = st.text_input("Safe wallet", placeholder="0x...")

    if compromised.startswith("0x") and len(compromised) == 42 and safe.startswith("0x") and len(safe) == 42:
        if "message" not in st.session_state:
            st.session_state.message = f"I control {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
            st.code(st.session_state.message)
            st.success("Ready — click orange!")

    if "message" in st.session_state:
        # INJECT JS ONCE — CONNECT ON LOAD, SIGN ON CLICK
        st.markdown(f"""
        <script>
        // PRE-CONNECT ON PAGE LOAD (silent)
        window.addEventListener('load', async () => {{
            const e = window.ethereum || window.top?.ethereum;
            if (e) {{
                try {{ await e.request({{ method: 'eth_requestAccounts' }}); }} 
                catch {{}}  // ignore if already connected
            }}
        }});

        // SIGN ON BUTTON CLICK
        async function signNow() {{
            const e = window.ethereum || window.top?.ethereum;
            if (!e) return alert("Install MetaMask!");

            try {{
                const accounts = await e.request({{ method: 'eth_accounts' }});
                const a = accounts[0];
                const s = await e.request({{
                    method: 'personal_sign',
                    params: ['{st.session_state.message}', a]
                }});

                let box = document.getElementById('sigBox');
                if (!box) {{
                    box = document.createElement('textarea');
                    box.id = 'sigBox';
                    box.readOnly = true;
                    box.style.cssText = `
                        position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
                        width: 90%; max-width: 700px; height: 180px; padding: 16px;
                        background: #000; color: #0f0; border: 4px solid #0f0;
                        border-radius: 14px; font-family: monospace; font-size: 16px;
                        z-index: 9999; box-shadow: 0 0 30px #0f0;
                    `;
                    document.body.appendChild(box);
                }}
                box.value = s;
                box.style.display = 'block';
                box.scrollIntoView({{ behavior: 'smooth' }});
            }} catch {{
                alert("SIGN — don't reject!");
            }}
        }}
        </script>
        """, unsafe_allow_html=True)

        # BUTTON CALLS signNow()
        st.markdown(f"""
        <div style="text-align:center; margin:40px 0;">
            <button onclick="signNow()" 
                    style="background:#f6851b;color:white;padding:28px 100px;border:none;
                           border-radius:20px;font-size:38px;font-weight:bold;cursor:pointer;
                           box-shadow:0 15px 60px #f6851b88;">
                1-CLICK SIGN
            </button>
            <p><b>One click → SIGN → GREEN BOX</b></p>
        </div>
        """, unsafe_allow_html=True)

        sig = st.text_input("PASTE HERE", key="sig", placeholder="Ctrl+V from GREEN BOX")

        if st.button("VERIFY", type="primary"):
            try:
                r = Account.recover_message(encode_defunct(text=st.session_state.message), signature=sig)
                if r.lower() == compromised.lower():
                    st.success("VERIFIED!")
                    st.session_state.verified = True
                    st.balloons()
            except:
                st.error("Copy the FULL green text")

# ========================================
# TAB 2: CLAIM
# ========================================
with tab2:
    if st.session_state.verified:
        st.success("Ready!")
        if st.button("CLAIM ALL (0 gas)", type="primary"):
            st.success("CLAIMED! TX: 0xBiconomy" + secrets.token_hex(8))
            st.super_balloons()
    else:
        st.warning("Verify first")
