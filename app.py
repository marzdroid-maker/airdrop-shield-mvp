# app.py
import secrets
import time
import streamlit as st
import streamlit.components.v1 as components
from eth_account import Account
from eth_account.messages import encode_defunct

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")

# WalletConnect Project ID (FREE at walletconnect.com)
PROJECT_ID = "YOUR_PROJECT_ID"  # Get free at https://cloud.walletconnect.com

# WalletConnect Modal
components.html(
    f"""
    <script src="https://unpkg.com/@walletconnect/modal@2"></script>
    <script>
    const modal = new WalletConnect.Modal({{
        projectId: '{PROJECT_ID}',
        metadata: {{
            name: 'Airdrop Shield',
            description: 'Recover airdrops safely',
            url: window.location.href,
            icons: ['https://avatars.githubusercontent.com/u/37784886']
        }}
    }});

    async function connectAndSign(message) {{
        try {{
            const {{ accounts }} = await modal.connect({{
                requiredNamespaces: {{ eip155: {{ chains: ['eip155:1'], methods: ['personal_sign'] }} }}
            }});
            const sig = await modal.request({{
                chainId: 'eip155:1',
                request: {{ method: 'personal_sign', params: [message, accounts[0]] }}
            }});
            // Auto-fill
            const inputs = parent.document.querySelectorAll('input[data-testid="stTextInput"]');
            const sigInput = inputs[inputs.length - 1];
            if (sigInput) {{
                sigInput.value = sig;
                sigInput.dispatchEvent(new Event('input', {{bubbles: true}}));
                alert("Signed & auto-filled!");
            }}
        }} catch (e) {{
            alert("Cancelled");
        }}
    }}
    </script>
    """,
    height=0,
)

tab1, tab2 = st.tabs(["Verify Wallet", "Claim Airdrop"])

with tab1:
    st.subheader("Step 1: Verify Wallet Ownership")
    compromised = st.text_input("Compromised wallet", "0x9538bfa699f9c2058f32439de547a054a9ceeb5c")
    safe = st.text_input("Safe wallet", "0xec451d6a06741e86e5ff0f9e5cc98d3388480c7a")

    if st.button("Generate Message"):
        msg = f"I own {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
        st.session_state.message = msg
        st.code(msg)
        st.success("Ready! Click below → Connect any wallet → Sign")

    if "message" in st.session_state:
        if st.button("Connect Wallet & Sign", type="primary"):
            components.html(
                f"<script>connectAndSign(`{st.session_state.message}`)</script>",
                height=0,
            )

        signature = st.text_input(
            "Signature (auto-filled)",
            key="sig",
            disabled=True
        )

        if st.button("Verify Signature"):
            if not signature:
                st.warning("Sign first")
            else:
                try:
                    recovered = Account.recover_message(
                        encode_defunct(text=st.session_state.message),
                        signature=signature
                    )
                    if recovered.lower() == safe.lower():
                        st.success(f"VERIFIED! {recovered[:8]}...{recovered[-6:]}")
                        st.session_state.verified = True
                        st.balloons()
                    else:
                        st.error("Wrong wallet")
                except:
                    st.error("Invalid")

with tab2:
    if not st.session_state.get("verified"):
        st.warning("Verify first")
    else:
        drop = st.selectbox("Airdrop", ["EigenLayer ($500)", "Hyperliquid ($300)", "Linea ($200)"])
        if st.button("CLAIM", type="primary"):
            with st.spinner("Submitting..."):
                time.sleep(2)
            st.success(f"CLAIMED {drop}! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
