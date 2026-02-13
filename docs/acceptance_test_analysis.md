# Acceptance Test Coverage Review

---

## **UC-01-AT**

- Yes, all flows from UC-01 are covered.  
- AT-07 and AT-08 are edge-case tests, but they are important and should stay.

**AT-07** checks a key safety rule. The system must never partially activate a dataset if something fails. This is not tied to one specific flow and applies to all failure situations. It proves the system keeps the old dataset until validation and storage both succeed, supporting the failed end condition that existing data is preserved. Without this, a partial update could reach production.

**AT-08** verifies that failure notifications are recorded. This maps to the requirement that failures must be logged for monitoring. Even if it could be bundled into other failure tests, keeping it separate makes the monitoring behavior easier to trace and validate on its own.

---

## **UC-02-AT**

- Yes, all flows from UC-02 are covered.  
- AT-06 and AT-07 are valid edge cases and should be retained.

**AT-06** validates the critical safety invariant preventing partial activation.  
**AT-07** ensures deduplication policy correctness.  
Both are essential for maintaining data integrity.

---

## **UC-03-AT**

- Yes, all flows from UC-03 are covered.  
- AT-08 is valid and should be kept.

**AT-08** verifies that forecast updates are atomic and that no partial forecasts become current during failures. This is fundamental to operational reliability.

---

## **UC-04-AT**

- Yes, all flows from UC-04 are covered.  
- AT-08 is a critical safety invariant test and should be kept.

It ensures weekly forecasts are only activated after successful storage, preventing operational decisions based on incomplete data.

---

## **UC-05-AT**

- Yes, all flows from UC-05 are covered.

---

## **UC-06-AT**

- Yes, all flows from UC-06 are covered.  
- AT-06, AT-07, and AT-08 are valid edge cases and should remain.

**AT-06** checks visualization quality. Proper layer ordering and visibility prevent misleading charts where uncertainty bands hide the forecast or historical data disappears.

**AT-07** ensures temporal alignment is correct. Managers rely on knowing exactly when forecasts begin, so incorrect timing would lead to poor planning decisions.

**AT-08** verifies that logging works across all scenarios, which is important for monitoring, debugging, and operational transparency.

---

## **UC-07-AT**

- All flows from UC-07 are covered in the acceptance test suite.
- There are two acceptance tests that do not correspond to a specific flow in the use case:
  - **AT-08** ensures that the results filtered for properly match the filters the user set. This is a valid acceptance test to include so that our filters work correctly and do not return false or misleading results. The inclusion of this test case is justified.
  - **AT-09** checks that a data retrieval or visualization error does not show partial results, and always clearly shows the error state to the user. This test is redundant since both of these types of errors are tested in AT-06 and AT-07, so the inclusion of this test is not needed. The test even mentions AT-06 and AT-07. For these reasons, we removed this test from our test suite.

---

## **UC-08-AT**

- All flows from UC-08 are covered in the acceptance test suite.
- There are three acceptance tests that do not correspond to a specific flow in the use case:
  - **AT-07** ensures that the results filtered for properly match the filters the user set. This is a valid acceptance test to include so that our filters work correctly and do not return false or misleading results. The inclusion of this test case is justified.
  - **AT-10** ensures that the system properly shows an error state in the case where an error occurs when trying to retrieve historical or forecast data. This is important to include to distinguish between no data available and an actual error, so this test is justified.
  - **AT-11** checks some of the previous tests to make sure the ones with missing data show missing data and ones with errors show errors. This is a bit of a redundant test since these conditions are already checked for in AT-05 to AT-10. Additionally, any errors in this test would really point to an error in one of the other tests (AT-05 to AT-10) that are being run, so this test does not provide any additional insight. For these reasons, we removed this test from the test suite.

---

## **UC-09-AT**

- All flows from UC-09 are covered in the acceptance test suite.
- There are three acceptance tests that do not correspond to a specific flow in the use case:
  - **AT-07** ensures that if weather service data has an error, the system logs the failure and indicates that weather data could not be retrieved. This is an important test to include to distinguish between weather data being unavailable and there being an error, so this test is justified.
  - **AT-10** ensures that when toggling the weather overlay, the system properly renders the correct overlay. This makes sense to include as well since we should expect the overlay to go away once it is toggled off. So this test is also justified.
  - **AT-11** checks some of the previous tests to make sure the ones with missing data show missing data and ones with errors show errors. This is a bit of a redundant test since these conditions are already checked for in AT-06 to AT-09. Additionally, any errors in this test would really point to an error in one of the other tests (AT-06 to AT-09) that are being run, so this test does not provide any additional insight. For these reasons, we removed this test from the test suite.

---

## **UC-10-AT**

- All flows from UC-10 are covered in the acceptance test suite.
- There are two acceptance tests that do not correspond to a specific flow in the use case:
  - **AT-09** ensures that when configuring the threshold for alerts, the behavior changes to reflect the change in threshold. This makes sense to include so we are confident that our alert threshold works as expected, so this test is justified.
  - **AT-10** checks some of the previous tests to make sure that their behavior is what we expect. Again, this test is fairly redundant as it just runs the previous tests and checks if their output is expected. Additionally, any errors in this test would really point to an error in one of the other tests (AT-04 to AT-08) that are being run, so this test does not provide any additional insight. For these reasons, we removed this test from the test suite.

---

## **UC-11-AT**

- All flows from UC-11 are covered in the acceptance test suite.
- There is one acceptance test that does not correspond to a specific flow in the use case:
  - **AT-09** checks some of the previous tests to make sure that their behavior is what we expect and that notifications are only sent when we intend to. Again, this test is fairly redundant as it just runs the previous tests and checks if their output is expected. Additionally, any errors in this test would really point to an error in one of the other tests (AT-02 to AT-08) that are being run, so this test does not provide any additional insight. For these reasons, we removed this test from the test suite.

---

## **UC-12-AT**

- All flows from UC-12 are covered in the acceptance test suite.
- There are two acceptance tests that do not correspond to a specific flow in the use case:
  - **AT-12** ensures that if the data retrieval layer fails at least one required data retrieval, the system logs the failure and indicates that the data could not be received because of an error. This is an important test to include to distinguish between data being unavailable and there being an error, so this test is justified.
  - **AT-13** checks some of the previous tests to make sure that their behavior is what we expect and that error states show as errors while missing data shows other available data. Again, this test is fairly redundant as it just runs the previous tests and checks if their output is expected. Additionally, any errors in this test would really point to an error in one of the other tests (AT-08 to AT-12) that are being run, so this test does not provide any additional insight. For these reasons, we removed this test from the test suite.