# 11 – MUnit Complete Testing Guide

**Project**: Shipment Signal Control Tower  
**Testing Framework**: MUnit 3.3.0  
**Test Suite File**: `src/test/munit/shipment-tracking-test-suite.xml`  

---

## 1. What is MUnit & Why It Is Essential

**MUnit** is MuleSoft's native unit and integration testing framework. It enables Mule developers to:
- Write automated test suites directly in XML or visual Studio canvases.
- Test DataWeave transformation mappings thoroughly before deployment.
- Mock external dependencies (databases, message queues, third-party HTTP endpoints) to create deterministic, isolated test environments.
- Verify error handlers and boundary edge cases.
- Measure application **Code Coverage** to prove production quality to hackathon judges.

---

## 2. Where Test Files Are Located

```text
shipment-tracking-control-tower/
└── src/test/
    ├── munit/
    │   └── shipment-tracking-test-suite.xml    ◄── [Core Test Suite]
    └── resources/
        └── log4j2-test.xml                     ◄── [Test Logging Config]
```

---

## 3. How to Run MUnit Tests in Anypoint Studio

### 3.1 Running the Entire Test Suite
1. In Anypoint Studio **Package Explorer**, expand `src/test/munit`.
2. Right-click on `shipment-tracking-test-suite.xml`.
3. Select **Run As -> MUnit Suite** (or press `Alt + Shift + X, U`).
4. Anypoint Studio opens the dedicated **MUnit** view at the bottom of the screen.

### 3.2 Running a Single MUnit Test
1. Double-click `shipment-tracking-test-suite.xml` to open the visual test canvas.
2. Right-click directly inside any individual `<munit:test>` box (e.g. `test-valid-bluedart-event-normalization`).
3. Select **Run MUnit Test**.

---

## 4. Reading the MUnit View in Studio

When the test run finishes, the **MUnit** view displays an interactive summary:

```text
MUnit View - shipment-tracking-test-suite.xml
  Runs: 9/9    Errors: 0    Failures: 0    [GREEN BAR = 100% SUCCESS]

  ✔ test-valid-bluedart-event-normalization (182ms)
  ✔ test-valid-delhivery-event-normalization (145ms)
  ✔ test-unauthorized-carrier-token-rejection (98ms)
  ✔ test-authorized-carrier-token-success (105ms)
  ✔ test-unknown-carrier-status-normalization (112ms)
  ✔ test-duplicate-event-detection-and-suppression (164ms)
  ✔ test-unknown-shipment-quarantining (195ms)
  ✔ test-risk-evaluation-delayed-sla (120ms)
  ✔ test-notification-milestone-filtering (88ms)
```

- **Green Bar**: All tests passed successfully.
- **Red Bar**: One or more assertions failed or an unexpected exception was thrown. Double-click any failed test to inspect the expected vs actual diff.

---

## 5. Walkthrough of the 9 Implemented Test Scenarios

### Test 1: `test-valid-bluedart-event-normalization`
- **Goal**: Verifies BlueDart JSON payload correctly normalizes into the Canonical Event model.
- **Input**: BlueDart payload with `status_code: "IT"`, `awb_no: "BD-987654321"`.
- **Assertions**:
  - `payload.carrier == 'BLUEDART'`
  - `payload.normalizedStatus == 'IN_TRANSIT'`
  - `payload.trackingNumber == 'BD-987654321'`
  - `payload.eventKey is not null`

### Test 2: `test-valid-delhivery-event-normalization`
- **Goal**: Verifies nested Delhivery JSON format (`Status.statusCode: "OFD"`, `waybill: "DELH-11223344"`).
- **Assertions**:
  - `payload.carrier == 'DELHIVERY'`
  - `payload.normalizedStatus == 'OUT_FOR_DELIVERY'`
  - `payload.trackingNumber == 'DELH-11223344'`

### Test 3: `test-unauthorized-carrier-token-rejection`
- **Goal**: Negative test ensuring unauthorized requests are rejected immediately.
- **Input**: Inbound header `X-Carrier-Token: "INVALID_EXPIRED_KEY_123"`.
- **Assertion**: Expected error attribute `expectedErrorType="APP:UNAUTHORIZED"`.

### Test 4: `test-authorized-carrier-token-success`
- **Goal**: Verifies valid token `delhivery-webhook-secret-key-2026` passes validation smoothly without error.

### Test 5: `test-unknown-carrier-status-normalization`
- **Goal**: Verifies that unmapped or novel carrier status codes (e.g. `CUSTOMS_DELAY_SPECIAL`) fallback gracefully to `UNKNOWN_STATUS` without throwing an exception.

### Test 6: `test-duplicate-event-detection-and-suppression`
- **Goal**: Verifies idempotency deduplication logic.
- **Mock**: Mocks `db:select` to return an existing record for the event key.
- **Assertions**:
  - `payload.status == 'DUPLICATE_ACKNOWLEDGED'`
  - `payload.isDuplicate == true`

### Test 7: `test-unknown-shipment-quarantining`
- **Goal**: Verifies unmanifested tracking numbers are quarantined to `pending_tracking_events`.
- **Mocks**:
  - Duplicate check returns empty array `[]`.
  - Master shipment lookup returns empty array `[]`.
  - Mocks `db:insert` on pending table.
- **Assertions**:
  - `payload.status == 'QUARANTINED_PENDING_REGISTRATION'`
  - `payload.isPendingUnknown == true`

### Test 8: `test-risk-evaluation-delayed-sla`
- **Goal**: Verifies that when current time exceeds `promised_delivery_time`, the risk engine classifies the parcel as `DELAYED`.
- **Assertions**:
  - `vars.riskAssessment.riskLevel == 'DELAYED'`
  - `vars.riskAssessment.reasonCode == 'PROMISED_SLA_BREACHED'`

### Test 9: `test-notification-milestone-filtering`
- **Goal**: Verifies routine in-transit scans do NOT trigger customer notification spam.
- **Assertion**: `vars.notificationPayload is null`.

---

## 6. How to Mock Processors in MUnit

MUnit allows mocking any message processor using `<munit-tools:mock-when>`:

```xml
<munit-tools:mock-when processor="db:select" doc:name="Mock Database Query">
    <munit-tools:with-attributes>
        <munit-tools:with-attribute whereValue="subflow-get-by-key" attributeName="doc:id" />
    </munit-tools:with-attributes>
    <munit-tools:then-return>
        <munit-tools:variables>
            <munit-tools:variable key="existingEvent" value="#[[{ id: 1 }]]" />
        </munit-tools:variables>
    </munit-tools:then-return>
</munit-tools:mock-when>
```

---

## 7. How to View Code Coverage Report in Studio

1. In Anypoint Studio, click **Window -> Show View -> Other...**.
2. Select **MUnit -> MUnit Coverage**.
3. Re-run your MUnit suite.
4. The **Coverage** pane lists percentage coverage by file and overall application coverage.
5. Double-click any flow to see a visual heatmap showing which processors were exercised (green) vs unexercised (red).

---

## 8. CLI vs Studio Testing & Enterprise Repository Explanation

> [!IMPORTANT]
> **Why Running MUnit in Anypoint Studio is Recommended Over Maven CLI**:  
> When running `mvn test` from the command line, Maven attempts to download the Mule EE runtime distribution BOM (`mule-runtime-impl-bom:pom:4.4.0`) from the MuleSoft Enterprise repository, which requires official MuleSoft Enterprise customer credentials in `~/.m2/settings.xml`.  
> In contrast, running inside **Anypoint Studio** uses the **bundled local Mule runtime container** (`C:\AnypointStudio\plugins\org.mule.tooling.server.*`), allowing complete MUnit test execution with zero external credentials required!

---

## 9. MUnit Troubleshooting & Resolved Errors

### Issue 1: `Script 'munit-tools:equalTo(...)' has errors: Unable to resolve reference of: munit`
- **Cause**: In MUnit XML, `munit-tools` is an XML namespace prefix. When used inside a DataWeave expression (`#[...]`), DataWeave interprets `munit-tools` as the variable `munit` minus `tools`. The actual DataWeave module name is `MunitTools::equalTo()`.
- **Resolution**: Use the cleaner and faster `<munit-tools:assert-equals actual="#[vars.carrier]" expected="#['DELHIVERY']" />` or `<munit-tools:assert-equals actual="#[vars.notificationPayload]" expected="#[null]" />`.

### Issue 2: `'application/json' requires a Stream Compatible content but found LinkedHashMap`
- **Cause**: Defining `<munit:payload value='#[{ ... }]' mediaType="application/json" />` produces an in-memory `LinkedHashMap` but flags it as `application/json`. DataWeave loggers and database input-parameters attempt to parse it with the JSON stream reader and throw a type mismatch.
- **Resolution**:
  1. In MUnit tests, set `mediaType="application/java"` when injecting in-memory test maps.
  2. In `shipment-processing.xml`, initialize flow variables using `<set-variable variableName="canonicalEvent" value="#[%dw 2.0 output application/java --- payload]" />`.
  3. In `database-operations.xml`, ensure database input parameters declare `%dw 2.0 output application/java`.

### Issue 3: Mock not intercepting processor (`whereValue` mismatch)
- **Cause**: In `<munit-tools:mock-when>`, the `whereValue` must match the `doc:id` of the exact inner processor (e.g., `doc:id="db-get-by-key"`), not the outer `sub-flow` id (`subflow-get-event-by-key`).
- **Resolution**: Verify the target processor's `doc:id` in the XML flow definition and match it exactly.
