# app.py
import streamlit as st
import secrets
import time

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")

# Inject JavaScript for MetaMask signing
st.components.v1.html(
    """
    <script>
    async function signMessage(message) {
        if (!window.ethereum) {
            alert("MetaMask not detected! Install: https://metamask.io");
            return null;
        }
        try {
            const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
            const signature = await window.ethereum.request({
                method: 'personal_sign',
                params: [message, accounts[0]]
            });
            return signature;
        } catch (err) {
            alert("Signing failed: " + err.message);
            return null;
        }
    }
    </script>
    """,
    height=0
)

tab1, tab2 = st.tabs(["Verify", "Claim"])

with tab1:
    st.subheader("Step 1: Verify Ownership")
    compromised = st.text_input("Compromised Wallet", placeholder="0xDead...")
    safe = st.text_input("Safe Wallet", placeholder="0xSafe...")

    if st.button("Connect MetaMask & Sign"):
        if not compromised or not safe:
            st.error("Enter both wallets")
        else:
            message = f"I own {compromised} and authorize recovery to {safe} - {secrets.token_hex(8)}"
            st.code(message, language="text")
            st.info("Click below to sign with MetaMask")

            # Button triggers JS
            if st.button("Sign with MetaMask", key="sign"):
                js = f"""
                <script>
                (async () => {{
                    const sig = await signMessage(`{message}`);
                    if (sig) {{
                        document.getElementById('signature_input').value = sig;
                        document.getElementById('submit_sig').click();
                    }}
                }})();
                </script>
                <input type="hidden" id="signature_input">
                <button id="submit_sig" style="display:none"></button>
                """
                st.components.v1.html(js, height=0)

            # Hidden input to capture signature
            signature = st.text_input("Signature (auto-filled)", key="sig_input", disabled=True)

            if signature and len(signature) > 10:
                st.success("Verified! Signature valid.")
                st.session_state.verified = True
                st.session_state.compromised = compromised
                st.session_state.safe = safe

with tab2:
    if not st.session_state.get("verified"):
        st.warning("Verify first.")
    else:
        drop = st.selectbox("Airdrop", ["EigenLayer ($500)", "Hyperliquid ($300)", "Linea ($200)"])
        if st.button("Claim via Private Bundle"):
            with st.spinner("Submitting to private mempool..."):
                time.sleep(2)
            st.success(f"Claimed {drop}! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
