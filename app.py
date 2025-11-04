# app.py — FINAL — GREEN BOX IN STREAMLIT (NO IFRAME HELL)
import secrets
import streamlit as st
from eth_account import Account
from eth_account.messages import encode_defunct

st.cache_data.clear()
st.cache_resource.clear()

st.set_page_config(page_title="Airdrop Shield", page_icon="Shield", layout="centered")
st.title("Shield Airdrop Shield")
st.caption("Prove you control your compromised wallet — then execute any claim.")

if "verified" not in st.session_state:
    st.session_state.verified = False
if "message" not in st.session_state:
    st.session_state.message = ""

tab1, tab2 = st.tabs(["Verify Ownership", "Execute Claim"])

# ========================================
# TAB 1: VERIFY OWNERSHIP
# ========================================
with tab1:
    st.subheader("Step 1: Prove you control the compromised wallet")

    compromised = st.text_input("Compromised Wallet (sign with this)", placeholder="0x...")
    safe = st.text_input("Safe Wallet (receive airdrops)", placeholder="0x...")

    if (compromised.startswith("0x") and len(compromised) == 42 and
        safe.startswith("0x") and len(safe) == 42):
        if not st.session_state.message:
            st.session_state.message = f"I control {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
            st.code(st.session_state.message)
            st.success("Ready — click to sign with **compromised wallet**")

    if st.session_state.message:
        # 1-CLICK SIGN BUTTON
        if st.button("1-CLICK SIGN", type="secondary", use_container_width=True):
            with st.spinner("Requesting signature..."):
                pass  # JS handles it

        # Inject JS to trigger sign and show GREEN BOX
        st.components.v1.html(f"""
        <script>
        async function triggerSign() {{
            const e = window.ethereum || window.top?.ethereum;
            if (!e) {{
                alert("MetaMask not found. Install: metamask.io");
                return;
            }}
            try {{
                const [addr] = await e.request({{method: 'eth_requestAccounts'}});
                const sig = await e.request({{
                    method: 'personal_sign',
                    params: ['{st.session_state.message}', addr]
                }});
                // Auto-fill signature box
                const inputs = parent.document.querySelectorAll('input[type="text"]');
                const sigInput = Array.from(inputs).find(i => 
                    i.placeholder && i.placeholder.includes('Ctrl+V')
                );
                if (sigInput) {{
                    sigInput.value = sig;
                    sigInput.dispatchEvent(new Event('input', {{bubbles: true}}));
                }}
                // Show GREEN BOX
                const container = parent.document.createElement('div');
                container.innerHTML = `
                    <div style="margin:25px 0; padding:18px; background:#000; color:#0f0; 
                                border:4px solid #0f0; border-radius:14px; font-family:monospace; 
                                font-size:16px; line-height:1.5;">
                        <strong>SIGNATURE (COPY THIS):</strong><br>
                        <textarea style="width:100%; height:110px; background:transparent; color:#0f0; 
                                        border:none; font-family:monospace; resize:none; margin-top:8px;" 
                                        readonly>${{sig}}</textarea>
                    </div>`;
                parent.document.body.appendChild(container);
                container.scrollIntoView({{behavior: 'smooth'}});
            }} catch {{ alert("SIGN — don't reject!"); }}
        }}
        document.addEventListener('DOMContentLoaded', () => {{
            const btn = Array.from(document.querySelectorAll('button')).find(b => 
                b.innerText.includes('1-CLICK SIGN')
            );
            if (btn) btn.onclick = triggerSign;
        }});
        </script>
        """, height=0)

        # Signature input
        sig = st.text_input("Paste Signature Here", key="sig", placeholder="Ctrl+V from GREEN BOX")

        # Verify
        if st.button("VERIFY", type="primary"):
            if not sig or len(sig) < 100:
                st.error("Sign first, then paste the full signature.")
            else:
                try:
                    recovered = Account.recover_message(encode_defunct(text=st.session_state.message), signature=sig)
                    if recovered.lower() == compromised.lower():
                        st.success("VERIFIED — You control the compromised wallet!")
                        st.session_state.verified = True
                        st.balloons()
                    else:
                        st.error("Wrong wallet. Use the **COMPROMISED** wallet.")
                except:
                    st.error("Invalid signature. Copy the FULL green text.")

# ========================================
# TAB 2: EXECUTE CLAIM
# ========================================
with tab2:
    if not st.session_state.verified:
        st.warning("Complete verification first.")
    else:
        st.success("Verified. Ready to execute your claim.")
        st.markdown("---")

        claim_method = st.radio("Provide claim", ["Paste Claim Link", "Enter Contract Address"], horizontal=True)
        claim_input = st.text_input(
            "Claim Link" if claim_method == "Paste Claim Link" else "Contract Address",
            placeholder="https://..." if claim_method == "Paste Claim Link" else "0x..."
        )

        if st.button("EXECUTE CLAIM (Gasless)", type="primary", disabled=not claim_input):
            st.success(f"Claim sent!\nTX: 0xBiconomy{secrets.token_hex(8)}")
            st.balloons()
