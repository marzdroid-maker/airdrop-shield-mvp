import secrets, json
import streamlit as st
from eth_account import Account
from eth_account.messages import encode_structured_data

st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️")
st.title("🛡️ Airdrop Shield")

if "verified" not in st.session_state:
    st.session_state.verified = False
if "eip712" not in st.session_state:
    st.session_state.eip712 = None

tab1, tab2 = st.tabs(["Verify", "Claim"])

with tab1:
    st.subheader("Step 1: Prove control of compromised wallet")

    compromised = st.text_input("Compromised wallet", placeholder="0x...")
    safe = st.text_input("Safe wallet", placeholder="0x...")

    ready = (
        compromised.startswith("0x") and len(compromised) == 42 and
        safe.startswith("0x") and len(safe) == 42
    )

    if ready:
        nonce = secrets.randbelow(2**32)

        # EIP-712 payload
        eip712 = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                ],
                "Recovery": [
                    {"name": "compromised", "type": "address"},
                    {"name": "safe", "type": "address"},
                    {"name": "nonce", "type": "uint256"},
                ],
            },
            "domain": {
                "name": "AirdropShield",
                "version": "1",
                "chainId": 1,
            },
            "primaryType": "Recovery",
            "message": {
                "compromised": compromised,
                "safe": safe,
                "nonce": nonce,
            },
        }

        st.session_state.eip712 = eip712
        st.code(json.dumps(eip712, indent=2))

        st.components.v1.html(f"""
        <script>
        async function signTyped() {{
            const ethereum = window.ethereum;
            if (!ethereum) return alert("Install MetaMask");

            const accounts = await ethereum.request({{ method: "eth_requestAccounts" }});
            const from = accounts[0];

            const payload = {json.dumps(eip712)};
            try {{
                const sig = await ethereum.request({{
                    method: "eth_signTypedData_v4",
                    params: [from, JSON.stringify(payload)]
                }});
                window.parent.postMessage({{sig}}, "*");
            }} catch(e) {{
                alert("Sign to continue");
            }}
        }}

        window.addEventListener("message", (event) => {{
            const data = event.data;
            if (data.sig) {{
                const input = window.parent.document.querySelector("#signatureInput input");
                input.value = data.sig;
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        }});
        </script>

        <button onclick="signTyped()"
                style="background:#f6851b;color:#fff;padding:18px 60px;
                       border:none;border-radius:16px;font-size:28px;
                       cursor:pointer;box-shadow:0 10px 40px #f6851b88;">
            1-CLICK SIGN (EIP-712)
        </button>
        """, height=120)

        sig_input = st.text_input("Signature", key="signatureInput", placeholder="auto-filled")

        if st.button("VERIFY", type="primary"):
            try:
                recovered = Account.recover_message(
                    encode_structured_data(eip712),
                    signature=sig_input
                )
                if recovered.lower() == compromised.lower():
                    st.success("✅ VERIFIED — You control the compromised wallet")
                    st.session_state.verified = True
                    st.balloons()
                else:
                    st.error("❌ Signature does not match wallet")
            except Exception as e:
                st.error(f"Bad signature: {e}")

with tab2:
    if st.session_state.verified:
        st.success("Wallet verified — safe to claim")
        st.button("🚀 Claim Airdrop (0 gas)", type="primary")
    else:
        st.warning("Verify ownership first")
