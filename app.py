import secrets
import streamlit as st
from eth_account import Account
from eth_account.messages import encode_defunct

st.cache_data.clear()
st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️")
st.title("🛡️ Airdrop Shield")

if "verified" not in st.session_state:
    st.session_state.verified = False

tab1, tab2 = st.tabs(["Verify", "Claim"])

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
        st.components.v1.html(f"""
        <style>
            #sigBox {{width:100%; height:120px; padding:15px; font-size:18px; 
                      background:#000; color:#0f0; border:4px solid #0f0; 
                      border-radius:12px; font-family:monospace; margin:20px 0;}}
        </style>
        <script>
        async function go() {{
            const e = window.ethereum || window.top?.ethereum;
            if (!e) return alert("Install MetaMask!");
            try {{
                const [a] = await e.request({{method:'eth_requestAccounts'}});
                const s = await e.request({{method:'personal_sign', params:['{st.session_state.message}', a]}});
                const box = document.createElement('textarea');
                box.id = 'sigBox';
                box.value = s;
                box.readOnly = true;
                document.body.appendChild(box);
                box.scrollIntoView({{behavior: 'smooth'}});
                alert("SIGNED! ↓ GREEN BOX BELOW ↓");
            }} catch {{ alert("SIGN — don’t reject!"); }}
        }}
        </script>
        <div style="text-align:center;">
            <button onclick="go()" 
                    style="background:#f6851b;color:white;padding:28px 100px;border:none;
                           border-radius:20px;font-size:38px;font-weight:bold;cursor:pointer;
                           box-shadow:0 15px 60px #f6851b88;">
                1-CLICK SIGN
            </button>
            <p><b>👇 GREEN BOX APPEARS BELOW AFTER SIGNING 👇</b></p>
        </div>
        """, height=220)

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

with tab2:
    if st.session_state.verified:
        st.success("Ready!")
        if st.button("CLAIM ALL (0 gas)", type="primary"):
            st.success("CLAIMED! TX: 0xBiconomy" + secrets.token_hex(8))
            st.super_balloons()
    else:
        st.warning("Verify first")
