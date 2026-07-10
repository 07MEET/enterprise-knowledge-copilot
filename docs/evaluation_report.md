# RAG Pipeline Evaluation Report

Generated on: 2026-07-09 02:26:20

## Overall Metrics Summary

- **Average Faithfulness (Groundedness)**: 0.00%
- **Average Context Recall**: 0.00%
- **Average Answer Relevance**: 0.00%
- **Average Latency**: 3.86 seconds
- **Refusal Accuracy**: 100.00%
- **Total Evaluated Cases**: 3

## Detailed Case Audits

### Case 1: What is the policy for rollover vacation days?
- **Answer**: I don't have enough information from the provided documents.
- **Ground Truth**: Employees can roll over up to 5 vacation days to the next calendar year, which must be used by March 31st.
- **Latency**: 4.08s | **System Confidence**: 0.00
- **Metrics**:
  - **Faithfulness**: 0.00% (Lack of context for complaint resolution process)
  - **Context Recall**: 0.00% (No mention of vacation policy)
  - **Answer Relevance**: 0.00% (Insufficient context or information)

---

### Case 2: How do I report a security incident?
- **Answer**: To report a security incident, you should follow the procedure outlined in the company's Sexual-Harassment-Policy.pdf document.

Firstly, if you are the person who is the cause of distress, you will be informed about what your actions, words, or behavior is doing and conveyed that such behavior is not appreciated. This can be done informally through a conversation with someone within the company, preferably your Superior or HR Representative.

If you are the one who has been affected by the incident, you may make a complaint in writing to the Internal Committee within three months from the date of the incident. The complaint can also be routed through the women representatives at respective locations. The Internal Complaints Committee will render reasonable assistance to women for making complaints in writing.

It is essential to believe in the reality of the complaint lodged, empathize with the complainant, and handle complaints in a confidential manner within 30 working days. The committee may further extend the time limit if satisfied that there were circumstances that prevented the woman from filing a complaint within the specified timeline.

Additionally, all incidents along with their resolution need to be reported to the Head-HR who will then provide a short report to the Internal Complaints Committee and the matter will be closed.
- **Ground Truth**: Security incidents must be reported immediately to security@company.com or via the internal Incident Portal within 24 hours.
- **Latency**: 6.32s | **System Confidence**: 0.50
- **Metrics**:
  - **Faithfulness**: 0.00% (Incorrect procedure for reporting security incident)
  - **Context Recall**: 0.00% (No mention of workplace harassment)
  - **Answer Relevance**: 0.00% (Answer is unrelated to security incident reporting)

---

### Case 3: What is the standard policy rollback threshold?
- **Answer**: I don't have enough information from the provided documents.
- **Ground Truth**: There is no information regarding a policy rollback threshold. The system must refuse to answer.
- **Latency**: 1.18s | **System Confidence**: 0.00
- **Metrics**:
  - **Faithfulness**: 0.00% (Insufficient context for answer generation)
  - **Context Recall**: 0.00% (No policy rollback threshold mentioned)
  - **Answer Relevance**: 0.00% (Insufficient context provided)

---
