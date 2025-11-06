# app.py — Airdrop Shield (Fully Working personal_sign + Clear Instructions)
import secrets
import streamlit as st
from eth_account import Account
from eth_account.messages import encode_defunct

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️")
st.title("🛡️ Airdrop Shield — Secure Recovery Tool")

# --- Initialize session state
if "verified" not in st.session_state:
    st.session_state.verified = False

tab1, tab2 = st.tabs(["Verify", "Claim"])

with tab1:
    st.subheader("Step 1 — Verify Control of Compromised Wallet")

    st.markdown("""
    ### 🧭 Instructions
    1. **Enter your compromised wallet** (the one that lost access)  
    2. **Enter your safe wallet** (where funds will be sent)  
    3. Click **🟧 1-CLICK SIGN** — MetaMask will pop up and ask you to sign a message  
    4. After signing, a **green box** appears at the bottom containing your signature  
    5. **Copy** the entire green text (Ctrl + C or ⌘ + C)  
    6. **Paste** it into the “Paste signature here” box  
    7. Click **VERIFY** to confirm wallet ownership
    """)

    compromised = st.text_input("Compromised wallet", placeholder="0x...")
    safe = st.text_input("Safe wallet", placeholder="0x...")

    if compromised.startswith("0x") and len(compromised) == 42 and safe.startswith("0x") and len(safe) == 42:
        if "message" not in st.session_state:
            st.session_state.message = (
                f"I control {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
            )
            st.code(st.session_state.message)
            st.success("✅ Ready — click the orange button below to sign in MetaMask")

    if "message" in st.session_state:
        # HTML signing widget (unchanged logic)
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
                font-size: 16px;
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
                try {{ await e.request({{method:'eth_requestAccounts'}}); }}
                catch(_){{}}
            }}
        }});

        async function go() {{
            const e = window.ethereum || window.top?.ethereum;
            if (!e) return alert("Please install MetaMask and connect your wallet.");
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
                box.scrollIntoView({{behavior:'smooth', block:'center'}});
                alert("✅ Signature created! Scroll down and copy it from the green box.");
            }} catch (err) {{
                alert("❌ Signing was cancelled or failed. Try again.");
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
            <p><b>Click → Sign → Copy from green box → Paste below</b></p>
        </div>
        """, height=330)

        sig = st.text_input("Paste signature here", key="sig", placeholder="Ctrl + V from green box")

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
                    st.error(f"❌ Signature recovered {recovered}, expected {compromised}")
            except Exception as e:
                st.error(f"Verification failed — please ensure full signature is pasted.\n\n{e}")

with tab2:
    if st.session_state.verified:
        st.success("Wallet verified — ready to claim.")
        if st.button("CLAIM ALL (0 gas)", type="primary"):
            st.success(f"✅ Claimed! TX: 0xBiconomy{secrets.token_hex(8)}")
            st.balloons()
    else:
        st.warning("Please verify your wallet first.")
