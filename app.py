# app.py — Airdrop Shield (EIP-712, auto-fill signature, auto-verify)
import json
import secrets
import streamlit as st
from eth_account import Account
from eth_account.messages import encode_structured_data

# --- Page setup
st.set_page_config(page_title="Airdrop Shield", page_icon="🛡️", layout="centered")
st.title("🛡️ Airdrop Shield — Front End (EIP-712)")

# Clear cached data during dev to avoid stale state
# (comment this out in production if you want persistence)
st.cache_data.clear()

# --- Session state defaults
if "verified" not in st.session_state:
    st.session_state.verified = False
if "eip712" not in st.session_state:
    st.session_state.eip712 = None
if "sig" not in st.session_state:
    st.session_state.sig = ""
if "nonce" not in st.session_state:
    st.session_state.nonce = None
if "signed_from" not in st.session_state:
    st.session_state.signed_from = None

# --- Layout
tab_verify, tab_claim = st.tabs(["Verify", "Claim"])

with tab_verify:
    st.subheader("Step 1 — Prove control of the *compromised* wallet (EIP-712)")
    st.write("Enter the compromised wallet and the safe destination wallet. Then click **1-CLICK SIGN (EIP-712)** to sign a typed payload with your wallet. The signature will auto-fill and auto-verify.")

    col1, col2 = st.columns(2)
    with col1:
        compromised = st.text_input("Compromised wallet (address)", placeholder="0x...", key="compromised_input")
    with col2:
        safe = st.text_input("Safe wallet (address)", placeholder="0x...", key="safe_input")

    # Validate simple address format (basic)
    ready = (
        isinstance(compromised, str) and compromised.startswith("0x") and len(compromised) == 42 and
        isinstance(safe, str) and safe.startswith("0x") and len(safe) == 42
    )

    if ready:
        # Generate a fresh nonce each time addresses change
        # Use a 32-bit nonce (sufficient) to avoid replay
        st.session_state.nonce = secrets.randbelow(2**32)

        # Build EIP-712 typed data payload
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
                # Use chainId that matches your target chain; default 1 (mainnet)
                "chainId": 1,
            },
            "primaryType": "Recovery",
            "message": {
                "compromised": compromised,
                "safe": safe,
                "nonce": int(st.session_state.nonce),
            },
        }

        # Save to session so verify stage can use it
        st.session_state.eip712 = eip712

        # Show payload for transparency (user can inspect)
        st.caption("EIP-712 payload (what you'll sign)")
        st.code(json.dumps(eip712, indent=2), language="json")

        # Insert the signing HTML component
        # It will:
        #  - try to use injected provider (window.ethereum || window.top?.ethereum)
        #  - request accounts
        #  - call eth_signTypedData_v4 with the typed payload
        #  - set/create a visible green text area in the page with the signature (so user can copy)
        #  - also place signature directly into a Streamlit text input by touching parent DOM and dispatching 'input' event
        component_html = f"""
        <div style="text-align:center; margin-top:18px;">
          <button id="signBtn" style="
              background:#f6851b;color:#fff;padding:20px 80px;border:none;
              border-radius:18px;font-size:26px;font-weight:700;cursor:pointer;
              box-shadow:0 14px 50px rgba(246,133,27,0.24);
              ">
            1-CLICK SIGN (EIP-712)
          </button>
        </div>

        <style>
        /* Green signed box that appears when signature captured */
        #sigBox {{
            position: fixed;
            bottom: 22px;
            left: 50%;
            transform: translateX(-50%);
            width: 92%;
            max-width: 900px;
            height: 160px;
            padding: 16px;
            background: #04120a;
            color: #b7ffb7;
            border: 3px solid #28a745;
            border-radius: 12px;
            font-family: monospace;
            font-size: 14px;
            z-index: 999999;
            display: none;
            box-shadow: 0 8px 40px rgba(40,167,69,0.14);
        }}
        #sigBox.show {{ display:block; }}
        </style>

        <script>
        // Provide robust detection for provider injected into iframe or top frame
        function getProvider() {{
            return window.ethereum || window.top?.ethereum || null;
        }}

        async function signTyped() {{
            const ethereum = getProvider();
            if (!ethereum) {{
                alert("MetaMask (or an injected Ethereum provider) was not detected in this browser context. Open the app in the same browser/profile as your wallet extension.");
                return;
            }}

            try {{
                const accs = await ethereum.request({{ method: 'eth_requestAccounts' }});
                if (!accs || accs.length === 0) {{
                    alert("No accounts found. Ensure your wallet is unlocked.");
                    return;
                }}
                const from = accs[0];

                // Payload from Streamlit (injected directly in HTML)
                const payload = {json.dumps(eip712)};

                // eth_signTypedData_v4 expects a JSON-stringified typed data object
                const sig = await ethereum.request({{
                    method: 'eth_signTypedData_v4',
                    params: [from, JSON.stringify(payload)]
                }});

                // Show signature in a green box on the page for easy copy/visual verify
                let box = document.getElementById('sigBox');
                if (!box) {{
                    box = document.createElement('textarea');
                    box.id = 'sigBox';
                    box.readOnly = true;
                    document.body.appendChild(box);
                }}
                box.value = sig;
                box.classList.add('show');
                box.scrollIntoView({{behavior: 'smooth', block: 'center'}});

                // Attempt to set the Streamlit text input directly in the parent DOM
                // NOTE: Streamlit inputs are nested; we try to find the signature input by id.
                // We'll look for an input inside an element with data-key "sig_input"
                try {{
                    // 1) new Streamlit versions: a text_input is an input element under an element with data-key
                    var parent = window.parent.document;
                    var possible = parent.querySelectorAll('div[data-key="sig_input"] input, input[id*="sig_input"]');
                    if (possible && possible.length > 0) {{
                        possible[0].value = sig;
                        possible[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }} else {{
                        // fallback: try to find any input with placeholder "auto-filled signature"
                        var fallback = parent.querySelectorAll('input[placeholder="auto-filled signature"]');
                        if (fallback && fallback.length > 0) {{
                            fallback[0].value = sig;
                            fallback[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                        }}
                    }}
                }} catch(e) {{
                    // If cross-frame DOM touch fails, we still post message to parent
                    window.parent.postMessage({{ type: 'EIP712_SIG', sig: sig, from: from }}, "*");
                }}

                // Also post message regardless — parent listener will pick it up
                window.parent.postMessage({{ type: 'EIP712_SIG', sig: sig, from: from }}, "*");

            }} catch (err) {{
                console.error("Signing error:", err);
                alert("Signing failed or was rejected.");
            }}
        }}

        // Hook sign button
        document.getElementById('signBtn').addEventListener('click', signTyped);

        </script>
        """

        # Insert component (height small since signature box is fixed-position)
        st.components.v1.html(component_html, height=140)

        # A visible Streamlit input to receive the signature (this will be automatically filled)
        # The data-key used inside HTML fallback above is "sig_input" — we set that key on this widget.
        sig_widget = st.text_input("Signature (auto-filled)", key="sig_input", placeholder="auto-filled signature")

        # If the postMessage from iframe (or DOM touch) sets the signature, handle the message
        # We also accept manual paste into the signature box.
        # To capture postMessage events, we need a tiny HTML listener outside the iframe.
        # We'll embed a second HTML snippet that listens for messages and if it sees our signature
        # message it will set an invisible Streamlit input via the same data-key.
        listener_html = """
        <script>
        window.addEventListener("message", (event) => {
            try {
                const d = event.data || {};
                if (d && d.type === 'EIP712_SIG' && d.sig) {
                    // Find the Streamlit input element and set it
                    try {
                        var parent = window.document;
                        var possible = parent.querySelectorAll('div[data-key="sig_input"] input, input[placeholder="auto-filled signature"]');
                        if (possible && possible.length > 0) {
                            possible[0].value = d.sig;
                            possible[0].dispatchEvent(new Event('input', { bubbles: true }));
                        }
                    } catch(e) {
                        // ignore
                    }
                }
            } catch(e) {
                // ignore
            }
        }, false);
        </script>
        """
        # Add a tiny invisible HTML box to page to register a message listener in the parent frame
        st.components.v1.html(listener_html, height=0)

        # If Streamlit text_input updated (either by user paste or by automatic fill), verify it.
        current_sig = st.session_state.get("sig_input", "")
        if current_sig:
            # Perform verification attempt
            try:
                # encode_structured_data expects the typed object exactly as used for signing
                encoded = encode_structured_data(text=json.dumps(st.session_state.eip712))
                recovered = Account.recover_message(encoded, signature=current_sig)
                st.session_state.signed_from = recovered
                # compare with compromised address (case-insensitive)
                if recovered.lower() == compromised.lower():
                    if not st.session_state.verified:
                        st.success("✅ VERIFIED — signature matches compromised wallet")
                        st.session_state.verified = True
                        st.balloons()
                    st.write(f"Signed from: `{recovered}`")
                else:
                    # signature exists but doesn't match
                    st.error(f"❌ Signature recovered address `{recovered}` does NOT match compromised wallet `{compromised}`")
                    st.session_state.verified = False
            except Exception as e:
                # Could be bad signature format or encoding mismatch
                st.warning("Signature present but verification failed (waiting for a proper EIP-712 signature).")
                # show error detail collapsed for debugging
                with st.expander("Debug info"):
                    st.write("Exception verifying signature:")
                    st.write(str(e))
    else:
        # Not ready — show helpful hint
        st.info("Enter both valid 0x... addresses to enable signing (compromised & safe).")

with tab_claim:
    st.subheader("Step 2 — Claim (UI stub)")
    if st.session_state.verified:
        st.success("Ready — proof verified. You can now request the claim relay.")
        st.write("This is a UI stub. In production the signed proof would be sent to a backend relay which calls the Shield smart contract to perform the atomic claim.")
        if st.button("CLAIM (relay) — simulate", type="primary"):
            # This is a local simulation only: generate a fake tx id
            fake_tx = "0x" + secrets.token_hex(16)
            st.success(f"Claim submitted (simulated). TX: {fake_tx}")
    else:
        st.warning("You must verify the compromised wallet first on the Verify tab.")

# Small footer & developer hints
st.markdown("---")
st.caption("Dev notes: Uses EIP-712 typed signatures (eth_signTypedData_v4). If your browser wallet isn't detected, open the app in the same browser/profile as the wallet extension. For WalletConnect/Phone-based signing, add a WalletConnect flow instead.")
