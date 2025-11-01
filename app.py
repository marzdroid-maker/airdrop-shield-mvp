# app.py
import secrets
import time
import streamlit as st
import streamlit.components.v1 as components
from eth_account import Account
from eth_account.messages import encode_defunct

st.set_page_config(page_title="Airdrop Shield", page_icon="Shield", layout="centered")
st.title("Shield Airdrop Shield")
st.caption("Recover airdrops from compromised wallets — safely.")

# ---------------- MetaMask Signer with Auto-Fill ----------------
def render_metamask_signer(message: str):
    # Unique key to avoid caching
    key = secrets.token_hex(8)

    components.html(
        f"""
        <script>
        async function signAndStore() {{
            if (!window.ethereum) {{
                alert("MetaMask not detected");
                return;
            }}
            try {{
                const accounts = await window.ethereum.request({{ method: 'eth_requestAccounts' }});
                const signature = await window.ethereum.request({{
                    method: 'personal_sign',
                    params: ['{message}', accounts[0]]
                }});
                // Store in sessionStorage + trigger rerun
                sessionStorage.setItem('metamask_sig_{key}', signature);
                // Trigger Streamlit rerun
                window.parent.location.href = window.parent.location.href + '?rerun=1';
            }} catch (err) {{
                alert("Signing failed: " + err.message);
            }}
        }}
        </script>

        <button onclick="signAndStore()"
                style="background:#f6851b; color:white; padding:12px 24px; 
                       border:none; border-radius:8px; font-size:16px; cursor:pointer;">
            Sign with MetaMask
        </button>
        """,
        height=70,
    )

    # Check if signature was stored
    sig = st.session_state.get(f"sig_{key}")
    if sig:
        return sig
    return None


# ---------------- Rerun Detection ----------------
if st.experimental_get_query_params().get("rerun"):
    st.experimental_rerun()


# ---------------- UI ----------------
tab1, tab2 = st.tabs(["Verify Wallet", "Claim Airdrop"])

with tab1:
    st.subheader("Step 1: Verify Wallet Ownership")

    compromised = st.text_input("Compromised wallet", placeholder="0xDead...")
    safe = st.text_input("Safe wallet (to receive funds)", placeholder="0xSafe...")

    if st.button("Generate Message"):
        if not compromised or not safe:
            st.error("Enter both wallets")
        else:
            msg = f"I own {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
            st.session_state.message = msg
            st.session_state.sign_key = secrets.token_hex(8)
            st.code(msg)
            st.info("Click to sign with MetaMask:")

    if "message" in st.session_state and "sign_key" in st.session_state:
        key = st.session_state.sign_key

        # Try to get signature from sessionStorage
        sig_js = f"""
        <script>
        const sig = sessionStorage.getItem('metamask_sig_{key}');
        if (sig) {{
            window.parent.postMessage({{type: 'STORE_SIG', key: '{key}', sig: sig}}, '*');
            sessionStorage.removeItem('metamask_sig_{key}');
        }}
        </script>
        """
        components.html(sig_js, height=0)

        # Capture via postMessage
        sig_result = st_javascript(f"""
            new Promise((resolve) => {{
                const handler = (e) => {{
                    if (e.data.type === 'STORE_SIG' && e.data.key === '{key}') {{
                        resolve(e.data.sig);
                    }}
                }};
                window.addEventListener('message', handler);
                setTimeout(() => resolve(null), 5000);
            }});
        """)

        if sig_result:
            st.session_state[f"sig_{key}"] = sig_result
            st.experimental_rerun()

        # Render button
        auto_sig = render_metamask_signer(st.session_state.message)

        if auto_sig:
            st.text_input("Signature (auto-filled)", value=auto_sig, disabled=True)
            signature = auto_sig
        else:
            signature = st.text_input("Signature (paste if needed)", placeholder="0x...")

        if st.button("Verify Signature"):
            if not signature or not signature.startswith("0x"):
                st.warning("Sign first.")
            else:
                try:
                    msg_hash = encode_defunct(text=st.session_state.message)
                    recovered = Account.recover_message(msg_hash, signature=signature)
                    if recovered.lower() == safe.lower():
                        st.success(f"Verified! {recovered[:6]}...{recovered[-4:]}")
                        st.session_state.verified = True
                    else:
                        st.error("Wrong wallet.")
                except Exception as e:
                    st.error(f"Invalid: {e}")


with tab2:
    st.subheader("Step 2: Claim Airdrop")
    if not st.session_state.get("verified"):
        st.warning("Verify first.")
    else:
        drop = st.selectbox("Airdrop", ["EigenLayer ($500)", "Hyperliquid ($300)", "Linea ($200)"])
        if st.button("Claim via Private Bundle"):
            with st.spinner("Submitting..."):
                time.sleep(2)
            st.success(f"Claimed {drop}! TX: 0xMock{secrets.token_hex(8)}")
            st.balloons()
