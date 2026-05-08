# UnityComms TLS Certificate Fix (Mono / Linux)

## Symptoms

- Unity Editor is in Play mode with UnityComms in scene
- Port 8080 shows no listener (`ss -tlnp | grep 8080` = empty)
- Editor.log shows `Mono.X509PalMono.Import` exception — stack trace ending in `X509Certificate2..ctor`
- ShowRunnerServer (port 8081, WebSocket) starts fine; only UnityComms HTTPS (port 8080) fails

## Root Cause — Mono TLS Stack Doesn't Support Modern PFX

Unity's Mono runtime uses an older TLS stack. Two failure modes:

**Mode 1 — PBES2/AES-256-CBC (default openssl):** `ArgumentException: unsupported HMAC` even with non-empty password.

**Mode 2 — RC2-40-CBC (`-legacy` on OpenSSL 3.x):** `error:0308010C:digital envelope routines:inner_evp_generic_fetch:unsupported`.

**Mode 3 — Empty password:** Mono fails silently.

## Diagnosis

```bash
ssh 10.0.0.91 "grep -E 'ArgumentException|X509Certificate2|unsupported|UnityComms.*Failed' ~/.config/unity3d/Editor.log | tail -10"
ssh 10.0.0.91 "ss -tlnp | grep 8080"
```

## Fix — Generate Mono-Compatible PFX (PBES1/SHA1/3DES)

On PC (10.0.0.91):

```bash
cd /mnt/Data/show_runner
# Use explicit 3DES cipher (PBES1/SHA1) — compatible with Unity Mono AND OpenSSL 3.x
openssl pkcs12 -export \
  -inkey comms_key.pem \
  -in comms_cert.pem \
  -certfile comms_chain.pem \
  -out comms_compat.pfx \
  -passout pass:unitypass \
  -certpbe PBE-SHA1-3DES -keypbe PBE-SHA1-3DES
```

**Never use `-legacy`** — it produces RC2-40-CBC which fails on OpenSSL 3.x with `error:0308010C`.

Verify:
```bash
openssl pkcs12 -info -in comms_compat.pfx -passin pass:unitypass -nokeys 2>&1 | head -6
# Should show: MAC: sha1, pbeWithSHA1And3DES-cbc
```

## Fix — Also use EphemeralKeySet at Runtime

**Even better** — bypass Mono's disk-based import entirely with `EphemeralKeySet`:

```csharp
// In UnityComms.cs — use the PFX path and EphemeralKeySet
_cert = new X509Certificate2("/mnt/Data/show_runner/comms.pfx", "unitypass", X509KeyStorageFlags.EphemeralKeySet);
```

`EphemeralKeySet` keeps the private key purely in-memory, completely bypassing Mono's broken cert loader. The PFX still needs to be in a compatible format (3DES above), but `EphemeralKeySet` means Mono never touches the key storage APIs.

## Restart Play Mode

`Start()` only fires when Play mode is freshly started:
1. Stop in Unity toolbar
2. Save Project (Ctrl+S)
3. Wait for `*** Tundra build success` in Console
4. Press Play
5. Verify: `# OLD: curl -k https://10.0.0.91:8080/api/status (HTTP server deleted - use WebSocket on port 8765)`

## Key Insight

The Editor.log is always the source of truth:
```bash
ssh 10.0.0.91 "tail -50 ~/.config/unity3d/Editor.log | grep -iE 'comms|startserver|https|error|exception'"
```
