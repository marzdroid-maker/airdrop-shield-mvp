# app.py — Airdrop Shield — USER-CONTROLLED CLAIMS
import secrets
import streamlit as st
from eth_account import Account
from eth_account.messages import encode_defunct

# Clear cache to avoid stale state
st.cache_data.clear()
st.cache_resource.clear()

# Page config
st.set_page_config(page_title="Airdrop Shield", page_icon="Shield", layout="centered")
st.title("Shield Airdrop Shield")
st.caption("Prove you control your compromised wallet — then execute any claim.")

# Session state
if "verified" not in st.session_state:
    st.session_state.verified = False
if "message" not in st.session_state:
    st.session_state.message = ""

# Tabs
tab1, tab2 = st.tabs(["Verify Ownership", "Execute Claim"])

# ========================================
# TAB 1: VERIFY OWNERSHIP
# ========================================
with tab1:
    st.subheader("Step 1: Prove you control the compromised wallet")

    compromised = st.text_input(
        "Compromised Wallet (sign with this)",
        placeholder="0x..."
    )
    safe = st.text_input(
        "Safe Wallet (receive airdrops)",
        placeholder="0x..."
    )

    # Generate message
    if (compromised.startswith("0x") and len(compromised) == 42 and
        safe.startswith("0x") and len(safe) == 42):
        if not st.session_state.message:
            st.session_state.message = (
                f"I control {compromised} and authorize recovery to {safe} — {secrets.token_hex(8)}"
            )
            st.code(st.session_state.message)
            st.success("Message ready — click to sign with **compromised wallet**")

    if st.session_state.message:
        # 1-CLICK SIGN → SHOW SIGNATURE IN GREEN BOX
        st.components.v1.html(f"""
        <style>
            #sigBox {{
                width:100%; height:130px; padding:16px; font-size:17px;
                background:#000; color:#0f0; border:4px solid #0f0;
                border-radius:12px; font-family:monospace; margin:20px 0;
                resize:none;
            }}
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
                alert("SIGNED! Copy the GREEN BOX below");
            }} catch {{ alert("SIGN — don't reject!"); }}
        }}
        </script>
        <div style="text-align:center; margin:30px 0;">
            <button onclick="go()" 
                    style="background:#f6851b;color:white;padding:28px 100px;border:none;
                           border-radius:20px;font-size:38px;font-weight:bold;cursor:pointer;
                           box-shadow:0 15px 60px #f6851b88;">
                1-CLICK SIGN
            </button>
            <p><b>After signing: Copy GREEN BOX → Paste below → VERIFY</b></p>
        </div>
        """, height=250)

        # Paste field
        sig = st.text_input(
            "Paste Signature Here",
            key="sig",
            placeholder="Ctrl+V from GREEN BOX"
        )

        # Verify
        if st.button("VERIFY", type="primary"):
            if not sig or len(sig) < 100:
                st.error("Paste the full signature from the green box.")
            else:
                try:
                    recovered = Account.recover_message(
                        encode_defunct(text=st.session_state.message),
                        signature=sig
                    )
                    if recovered.lower() == compromised.lower():
                        st.success("VERIFIED — You control the compromised wallet!")
                        st.session_state.verified = True
                        st.balloons()
                    else:
                        st.error("Wrong wallet signed. Use the **COMPROMISED** wallet.")
                except:
                    st.error("Invalid signature. Copy the FULL green text.")

# ========================================
# TAB 2: EXECUTE USER-PROVIDED CLAIM
# ========================================
with tab2:
    if not st.session_state.verified:
        st.warning("Complete verification in the first tab.")
    else:
        st.success("Ownership verified. Ready to execute your claim.")
        st.markdown("---")

        # User chooses input method
        claim_method = st.radio(
            "How will you provide the claim?",
            ["Paste Claim Link", "Enter Contract Address"],
            horizontal=True
        )

        if claim_method == "Paste Claim Link":
            claim_input = st.text_input(
                "Claim Link",
                placeholder="https://claim.eigenlayer.xyz/0xabc..."
            )
            help_text = "Paste the full claim URL from the project."
        else:
            claim_input = st.text_input(
                "Claim Contract Address",
                placeholder="0x..."
            )
            help_text = "Enter the airdrop claim contract address."

        st.caption(help_text)

        # Execute button
        if st.button("EXECUTE CLAIM (Gasless)", type="primary", disabled=not claim_input):
            with st.spinner("Preparing gasless transaction via Biconomy..."):
                st.code(f"{claim_method}: {claim_input}")
                st.success(
                    f"Claim executed!\n\n"
                    f"• From: `{compromised[:8]}...`\n"
                    f"• To: `{safe[:8]}...`\n"
                    f"• TX: `0xBiconomy{secrets.token_hex(8)}`"
                )
                st.balloons()
                st.info(
                    "In production: This triggers a real Biconomy meta-transaction "
                    "to the claim contract or follows the claim link."
                )
