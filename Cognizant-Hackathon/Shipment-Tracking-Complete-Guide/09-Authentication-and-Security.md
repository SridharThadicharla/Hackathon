# 09 – Authentication & Security Complete Guide

**Project**: Shipment Signal Control Tower  
**Security Focus**: Inbound Webhook Authentication, Secure Configuration Properties, and API Policies  

---

## 1. Security Architecture Overview

Securing logistics webhooks requires a multi-layered defense model:
1. **Inbound Webhook Authentication**: Verifying courier identity via pre-shared secret tokens (`X-Carrier-Token`).
2. **Secure Property Management**: Encrypting sensitive database passwords and carrier tokens at rest.
3. **API Manager Governance**: Applying rate limiting, spike control, and IP whitelisting policies.
4. **Distributed Auditing & Tracing**: Propagating `X-Correlation-ID` on all inbound and outbound transactions.

```text
[Carrier Webhook Request]
         │
         ▼
[API Gateway: IP Whitelist & Rate Limiting Policy]
         │
         ▼
[HTTP Ingress Listener: Correlation ID Injection]
         │
         ▼
[subflow-validate-carrier-auth] ──► Token Mismatch ──► HTTP 401 Unauthorized
         │ (Token Verified)
         ▼
[DataWeave Normalization & Processing]
```

---

## 2. Inbound Webhook Authentication Implementation

### 2.1 The Security Subflow
The subflow `subflow-validate-carrier-auth` is implemented in `src/main/mule/webhook-api.xml`:

```xml
<sub-flow name="subflow-validate-carrier-auth">
    <!-- Extract token from Inbound Header or Query Parameter -->
    <set-variable variableName="inboundToken" 
        value="#[attributes.headers['x-carrier-token'] default attributes.headers['X-Carrier-Token'] default attributes.queryParams['x-carrier-token'] default attributes.queryParams['X-Carrier-Token'] default '']" />

    <choice doc:name="Check Token Match">
        <when expression="#[(upper(trim(vars.carrier)) == 'BLUEDART' and vars.inboundToken == p('carrier.bluedart.token')) or (upper(trim(vars.carrier)) == 'DELHIVERY' and vars.inboundToken == p('carrier.delhivery.token'))]">
            <logger level="DEBUG" message="#['[Security] Authenticated webhook for carrier: ' ++ vars.carrier]" />
        </when>
        <otherwise>
            <logger level="WARN" message="#['[Security] Unauthorized access attempt for carrier: ' ++ (vars.carrier default 'UNKNOWN') ++ ' | Token: ' ++ (if (isEmpty(vars.inboundToken)) 'MISSING' else 'INVALID')]" />
            <raise-error type="APP:UNAUTHORIZED" description="Invalid or missing X-Carrier-Token header for carrier webhook." />
        </otherwise>
    </choice>
</sub-flow>
```

### 2.2 Configured Carrier Tokens (`config/mule-dev.yaml`)
```yaml
carrier:
  bluedart:
    token: "bluedart-webhook-secret-key-2026"
  delhivery:
    token: "delhivery-webhook-secret-key-2026"
```

### 2.3 Error Response on Authentication Failure
When an invalid or missing token is submitted, the global error handler intercepts `APP:UNAUTHORIZED` and returns:
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Missing or invalid carrier authentication credentials.",
    "details": "Provide valid X-Carrier-Token header."
  },
  "timestamp": "2026-10-11T06:15:00Z",
  "correlationId": "c85d8984-9df2-43bb-a53f-a3cf6ad35501"
}
```
HTTP Status: `401 Unauthorized`.

---

## 3. Secure Configuration Properties (Production)

In production and CloudHub deployments, sensitive credentials must never be committed to source code in plaintext.

### 3.1 Mule Secure Configuration Properties Module
MuleSoft provides the `mule-secure-configuration-property-module` which encrypts YAML values using AES or Blowfish algorithms:

```yaml
db:
  password: "![a7B4q8...encrypted_ciphertext...==]"
carrier:
  bluedart:
    token: "![9kL2p1...encrypted_ciphertext...==]"
```

### 3.2 Secure Property Decryption Key Injection
At runtime, the encryption key is passed via JVM arguments or Anypoint Runtime Manager environment properties:
```bash
# Running locally via Maven / Command Line:
java -jar app.jar -M-Dmule.encryption.key=MySecretKey2026

# In Anypoint Studio Run Configuration:
-M-Dmule.encryption.key=MySecretKey2026
```

---

## 4. Anypoint API Manager Recommended Policies

When managed via Anypoint API Manager, the following three automated policies are recommended:

### Policy 1: Rate Limiting / SLA-Based Throttling
- **Window**: 1 Minute
- **Quota**: 1,000 requests / minute per carrier client ID.
- **Purpose**: Protects database connection pools against carrier push floods during network reconnection bursts.

### Policy 2: IP Whitelisting
- **Configuration**: Whitelist carrier egress IP ranges (e.g. BlueDart CIDR blocks: `103.24.120.0/24`).
- **Purpose**: Rejects unauthorized third-party traffic at the gateway perimeter before it reaches the Mule application runtime.

### Policy 3: HMAC-SHA256 Payload Signature Verification
For couriers that support cryptographic signature verification (such as FedEx or advanced logistics webhooks):
1. Carrier generates an HMAC-SHA256 signature using the request body and shared secret:
   `X-Signature: hex(hmac_sha256(secret, rawPayload))`
2. In MuleSoft, DataWeave's `dw::Crypto::HMACBinary` computes the expected hash and compares using constant-time equality to prevent timing attacks.
