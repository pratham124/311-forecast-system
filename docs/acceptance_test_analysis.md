# Acceptance Test Coverage Review

---

## **UC-01-AT**

- All flows from UC-01 are covered in the acceptance test suite.  
- There are two acceptance tests that do not correspond to a specific flow in the use case:
  - **AT-07** checks a key safety rule. The system must never partially activate a dataset if something fails. This is not tied to one specific flow and applies to all failure situations. It proves the system keeps the old dataset until validation and storage both succeed, supporting the failed end condition that existing data is preserved. Without this, a partial update could reach production. So this test is justified.
  - **AT-08** verifies that failure notifications are recorded. This maps to the requirement that failures must be logged for monitoring. Even if it could be bundled into other failure tests, keeping it separate makes the monitoring behavior easier to trace and validate on its own. So this test is justified as well.

---

## **UC-02-AT**

- All flows from UC-02 are covered in the acceptance test suite.   
- There are two acceptance tests that do not correspond to a specific flow in the use case:
  - **AT-06** validates the critical safety invariant preventing partial activation. This is an important check to have so its inclusion in the acceptance tests is justified.
  - **AT-07** ensures deduplication policy correctness. This is also an important check as correctness is critical so its inclusion is justified.

---

## **UC-03-AT**

- All flows from UC-03 are covered in the acceptance test suite.   
- There is one acceptance tests that do not correspond to a specific flow in the use case:
 - **AT-08** verifies that forecast updates are atomic and that no partial forecasts become current during failures. This is fundamental to operational reliability, making this test justified to include in our acceptance tests.

---

## **UC-04-AT**

- All flows from UC-04 are covered in the acceptance test suite.   
- There is one acceptance tests that do not correspond to a specific flow in the use case:
 - **AT-08** It ensures weekly forecasts are only activated after successful storage, preventing operational decisions based on incomplete data. This is also a critical check, so it make sense to include this in our tests.

---

## **UC-05-AT**

- All flows from UC-05 are covered in the acceptance test suite. 
- There are three acceptance tests that do not correspond to a specific flow in the use case:
  - **AT-06** ensures the visualization remains interpretable by validating that historical data, forecast, and uncertainty bands are all visible and correctly layered. Without it, the system could technically render all components but produce a misleading or unreadable chart. So this test is justified.
  - **AT-07** verifies that forecast and historical data are aligned on the correct time boundary, as required by the use case. Without it, subtle timestamp misalignment errors could occur while still passing basic rendering checks. So this test is also justified.
  - **AT-08** ensures that each dashboard load produces a consistent and accurate outcome log entry across all success and failure scenarios. It validates observability and traceability, preventing silent failures or mismatches between UI state and logged system behavior. So this test is also justified.

---

## **UC-06-AT**

- All flows from UC-06 are covered in the acceptance test suite.   
- There is one acceptance tests that do not correspond to a specific flow in the use case:
  - **AT-08** ensures that each dashboard load produces a consistent and accurate outcome log entry across all success and failure scenarios. This is also an important test to have so its inclusion is justified.

---

## **UC-07-AT**

- All flows from UC-07 are covered in the acceptance test suite.
- There are two acceptance tests that do not correspond to a specific flow in the use case:
  - **AT-08** ensures that the results filtered for properly match the filters the user set. This is a valid acceptance test to include so that our filters work correctly and do not return false or misleading results. The inclusion of this test case is justified.
  - **AT-09** checks that a data retrieval or visualization error does not show partial results, and always clearly shows the error state to the user. This test is redundant since both of these types of errors are tested in AT-06 and AT-07, so the inclusion of this test is not needed. The test even mentions AT-06 and AT-07. For these reasons, we removed this test from our test suite by prompting ChatGPT to remove it from the test suite.

---

## **UC-08-AT**

- All flows from UC-08 are covered in the acceptance test suite.
- There are three acceptance tests that do not correspond to a specific flow in the use case:
  - **AT-07** ensures that the results filtered for properly match the filters the user set. This is a valid acceptance test to include so that our filters work correctly and do not return false or misleading results. The inclusion of this test case is justified.
  - **AT-10** ensures that the system properly shows an error state in the case where an error occurs when trying to retrieve historical or forecast data. This is important to include to distinguish between no data available and an actual error, so this test is justified.
  - **AT-11** checks some of the previous tests to make sure the ones with missing data show missing data and ones with errors show errors. This is a bit of a redundant test since these conditions are already checked for in AT-05 to AT-10. Additionally, any errors in this test would really point to an error in one of the other tests (AT-05 to AT-10) that are being run, so this test does not provide any additional insight. For these reasons, we removed this test from the test suite by prompting ChatGPT to remove it from the test suite.

---

## **UC-09-AT**

- All flows from UC-09 are covered in the acceptance test suite.
- There are three acceptance tests that do not correspond to a specific flow in the use case:
  - **AT-07** ensures that if weather service data has an error, the system logs the failure and indicates that weather data could not be retrieved. This is an important test to include to distinguish between weather data being unavailable and there being an error, so this test is justified.
  - **AT-10** ensures that when toggling the weather overlay, the system properly renders the correct overlay. This makes sense to include as well since we should expect the overlay to go away once it is toggled off. So this test is also justified.
  - **AT-11** checks some of the previous tests to make sure the ones with missing data show missing data and ones with errors show errors. This is a bit of a redundant test since these conditions are already checked for in AT-06 to AT-09. Additionally, any errors in this test would really point to an error in one of the other tests (AT-06 to AT-09) that are being run, so this test does not provide any additional insight. For these reasons, we removed this test from the test suite by prompting ChatGPT to remove it from the test suite.

---

## **UC-10-AT**

- All flows from UC-10 are covered in the acceptance test suite.
- There are two acceptance tests that do not correspond to a specific flow in the use case:
  - **AT-09** ensures that when configuring the threshold for alerts, the behavior changes to reflect the change in threshold. This makes sense to include so we are confident that our alert threshold works as expected, so this test is justified.
  - **AT-10** checks some of the previous tests to make sure that their behavior is what we expect. Again, this test is fairly redundant as it just runs the previous tests and checks if their output is expected. Additionally, any errors in this test would really point to an error in one of the other tests (AT-04 to AT-08) that are being run, so this test does not provide any additional insight. For these reasons, we removed this test from the test suite by prompting ChatGPT to remove it from the test suite.

---

## **UC-11-AT**

- All flows from UC-11 are covered in the acceptance test suite.
- There is one acceptance test that does not correspond to a specific flow in the use case:
  - **AT-09** checks some of the previous tests to make sure that their behavior is what we expect and that notifications are only sent when we intend to. Again, this test is fairly redundant as it just runs the previous tests and checks if their output is expected. Additionally, any errors in this test would really point to an error in one of the other tests (AT-02 to AT-08) that are being run, so this test does not provide any additional insight. For these reasons, we removed this test from the test suite by prompting ChatGPT to remove it from the test suite.

---

## **UC-12-AT**

- All flows from UC-12 are covered in the acceptance test suite.
- There are two acceptance tests that do not correspond to a specific flow in the use case:
  - **AT-12** ensures that if the data retrieval layer fails at least one required data retrieval, the system logs the failure and indicates that the data could not be received because of an error. This is an important test to include to distinguish between data being unavailable and there being an error, so this test is justified.
  - **AT-13** checks some of the previous tests to make sure that their behavior is what we expect and that error states show as errors while missing data shows other available data. Again, this test is fairly redundant as it just runs the previous tests and checks if their output is expected. Additionally, any errors in this test would really point to an error in one of the other tests (AT-08 to AT-12) that are being run, so this test does not provide any additional insight. For these reasons, we removed this test from the test suite by prompting ChatGPT to remove it from the test suite.

---

## **UC-13-AT**

- All flows from UC-13 are covered in the acceptance test suite.
- There is one acceptance test that does not directly correspond to a specific flow in the use case:
  - **AT-11** should not be kept as it's redundant. It doesn't test anything new, it's just re-running AT-08, AT-09, AT-10, and AT-05. If those individual tests pass, the "key behavioral theme" is already verified.

---

## **UC-14-AT**

- All flows from UC-14 are covered in the acceptance test suite.
- There is one acceptance test that does not directly correspond to a specific flow in the use case:
  - **AT-13** should not be kept as it's redundant. It doesn't test anything new, its just re-running AT-09, AT-10, AT-11, and AT-12. If those individual tests pass, the "key behavioral theme" is already verified.

---

## **UC-15-AT**

- All flows from UC-15 are covered in the acceptance test suite.
- There is one acceptance test that does not directly correspond to a specific flow in the use case:
  - **AT-13** should not be kept as it's redundant. It doesn't test anything new, its just re-running AT-09, AT-10, AT-11, and AT-12. If those individual tests pass, the "key behavioral theme" is already verified.

---

## **UC-16-AT**

- All flows from UC-16 are covered in the acceptance test suite.
- There is one acceptance test that does not directly correspond to a specific flow in the use case:
  - **AT-10** checks some of the previous tests to make sure that their behavior is what we expect and that the confidence indicator is only displayed when needed. Again, this test is fairly redundant as it just runs the previous tests and checks if their output is expected. Additionally, any errors in this test would really point to an error in one of the other tests (AT-03 to AT-09) that are being run, so this test does not provide any additional insight. For these reasons, we removed this test from the test suite by prompting ChatGPT to remove it from the test suite.

---

## **UC-17-AT**

- All flows from UC-17 are covered in the acceptance test suite.
- There is one acceptance test that does not directly correspond to a specific flow in the use case:
  - **AT-09** checks some of the previous tests to make sure that their behavior is what we expect and that only public forecast data is displayed. Again, this test is fairly redundant as it just runs the previous tests and checks if their output is expected. Additionally, any errors in this test would really point to an error in one of the other tests (AT-04 to AT-08) that are being run, so this test does not provide any additional insight. For these reasons, we removed this test from the test suite by prompting ChatGPT to remove it from the test suite.

---

## **UC-18-AT**

- All flows from UC-18 are covered in the acceptance test suite.
- There is one acceptance test that does not directly correspond to a specific flow in the use case:
  - **AT-08** checks some of the previous tests to make sure that their behavior is what we expect and that the user can properly see the user guide. Again, this test is fairly redundant as it just runs the previous tests and checks if their output is expected. Additionally, any errors in this test would really point to an error in one of the other tests (AT-02 to AT-07) that are being run, so this test does not provide any additional insight. For these reasons, we removed this test from the test suite by prompting ChatGPT to remove it from the test suite.

---

## **UC-19-AT**

- All flows from UC-19 are covered in the acceptance test suite.
- There is one acceptance test that does not directly correspond to a specific flow in the use case:
  - **AT-12** checks some of the previous tests to make sure that their behavior is what we expect and that the user can submit feedback/bug reports and the results are saved. Again, this test is fairly redundant as it just runs the previous tests and checks if their output is expected. Additionally, any errors in this test would really point to an error in one of the other tests (AT-08 to AT-11) that are being run, so this test does not provide any additional insight. For these reasons, we removed this test from the test suite by prompting ChatGPT to remove it from the test suite.