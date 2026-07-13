# RAG Pipeline Evaluation Report

Generated on: 2026-07-11 00:52:25

## Overall Metrics Summary

- **Average Faithfulness (Groundedness)**: 50.00%
- **Average Context Recall**: 95.00%
- **Average Answer Relevance**: 90.00%
- **Average Latency**: 5.44 seconds
- **Refusal Accuracy**: 100.00%
- **Total Evaluated Cases**: 20

## Detailed Case Audits

### Case 1: What is the timeline for filing a complaint under the Sexual Harassment Policy?
- **Answer**: The timeline for filing a complaint under the Sexual Harassment Policy at Supreet Chemicals Limited is as follows: [1]

* The aggrieved woman may make, in writing, a complaint of sexual harassment at the workplace to the Internal Committee within a period of three months from the date of incident and in case of a series of incidents, within a period of three months from the date of the last incident [2]. [2]
* This time limit may further be extended for 3 months if the complaints committee is satisfied that there were circumstances that prevented the woman from filing a complaint within the specified timeline [2]. [2]

It's worth noting that the company has defined processes for remediation and corrective action in case of any confirmed incidents, ensuring justice, accountability, and support for affected individuals [3]. [3] However, no specific timeline is provided for filing an informal grievance.

In terms of the procedures for addressing a complaint, the following timelines are mentioned:

* The Chairperson after studying the report & discussion with the Committee members shall submit her recommendation to the Head-HR within 10 days of completing the inquiry [4]. [4]
* The implementation of the recommendation of Internal Complaint Committee by HeadHR should be done within 30 days of receipt of such recommendation [4]. [4]

It's also worth noting that the company has a policy on prevention of sexual harassment at the workplace since 1992, and the revised policy in 2013 incorporates the recent legislation of Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013 [2]. [5]
- **Ground Truth**: A complaint must be made in writing to the Internal Committee within three months from the date of the incident (or the last incident in case of a series of incidents).
- **Latency**: 7.10s | **System Confidence**: 0.78
- **Metrics**:
  - **Faithfulness**: 100.00% (Matches retrieved context)
  - **Context Recall**: 100.00% (Context contains necessary facts)
  - **Answer Relevance**: 100.00% (Directly addresses user question)

---

### Case 2: Who is the Chief Financial Officer (CFO) of Supreet Chemicals Limited?
- **Answer**: The Chief Financial Officer (CFO) of Supreet Chemicals Limited is Dineshchandra Manubhai Patel [1].

[1]
[2]
[3]
- **Ground Truth**: Dineshchandra Manubhai Patel is the Chief Financial Officer (CFO) of Supreet Chemicals Limited.
- **Latency**: 1.60s | **System Confidence**: 1.00
- **Metrics**:
  - **Faithfulness**: 0.00% (Invented information not supported by context)
  - **Context Recall**: 100.00% (Key facts present in context)
  - **Answer Relevance**: 100.00% (Directly answers user question)

---

### Case 3: What happens to the surplus arising out of CSR projects under the CSR Policy?
- **Answer**: The surplus arising out of CSR projects under the CSR Policy is treated in a specific manner. According to the policy, any surplus arising out of CSR activities shall not form part of the business profit of the Company [1] [1]. Instead, it will be ploughed back into the same project or transferred to the Unspent CSR Account and spent in pursuance of CSR policy and annual action plan of the Company [1] [1].

The surplus amount can also be transferred to a Fund specified in Schedule VII, within such period and with such terms and conditions as may be prescribed under Section 135 of the Act read with relevant rules applicable [1] [1]. This ensures that the surplus is utilized effectively and in line with the objectives of the CSR Policy.

It's worth noting that the policy also outlines the responsibilities of the CSR Team, which includes monitoring CSR projects to establish their effectiveness and appraising them to the CSR Committee [2] [2]. The Board of the Company shall also satisfy itself that the CSR funds disbursed have been utilized for the purposes and in the manner as approved by it [3] [3].

Overall, the policy aims to ensure that any surplus arising out of CSR activities is utilized in a responsible and effective manner, aligning with the objectives of the CSR Policy.
- **Ground Truth**: Any surplus arising out of the CSR activities shall not form part of the business profit of the Company and shall be ploughed back into the same project or transferred to the Unspent CSR Account.
- **Latency**: 7.37s | **System Confidence**: 0.62
- **Metrics**:
  - **Faithfulness**: 0.00% (Invented details not supported by context)
  - **Context Recall**: 100.00% (Key facts present in context)
  - **Answer Relevance**: 100.00% (Directly addresses user question)

---

### Case 4: Who can make a Protected Disclosure under the Whistle Blower Policy?
- **Answer**: Under the Whistle Blower Policy of Supreet Chemicals Limited, all Employees and directors of the Company are eligible to make Protected Disclosures [1]. This means that any employee or director who has a concern about unethical or improper activity within the company can report it under this policy [1].

Key details regarding eligibility for making a Protected Disclosure include: [2]

*  All Employees [2]
*  Directors of the Company (past or present) [3]
*  The requirement to disclose in good faith and provide factual information

It is essential to note that anonymous disclosures will not be entertained, as the Whistleblower must disclose their identity in the covering letter forwarding such Protected Disclosure [2].
- **Ground Truth**: Any employee or director of the Company who makes a Protected Disclosure under the Whistle Blower Policy.
- **Latency**: 4.54s | **System Confidence**: 0.86
- **Metrics**:
  - **Faithfulness**: 100.00% (No contradictions found)
  - **Context Recall**: 100.00% (Context mentions key facts about Whistleblower Policy)
  - **Answer Relevance**: 100.00% (Directly answers user question)

---

### Case 5: What financial parameters are considered for declaring dividends under the Dividend Distribution Policy?
- **Answer**: The financial parameters considered for declaring dividends under the Dividend Distribution Policy are as follows: [1]

**Internal Parameters:** [2]

* Profits earned and available for distribution during the financial year [2]
* Accumulated reserves including retained earnings [2]
* Net profit earned during the financial year as per the consolidated financial statements [2]
* Cash flows [2]
* Debt repayment schedules, if any [2]
* Fund requirement for contingencies and unforeseen events with financial implications [2]
* Expansion/diversification of business by the Company [2]
* Restrictive covenants under the financing documents [2]
* Any other relevant factors and material events [2]

**External Parameters:** [2]

* Regulatory changes – Introduction of new regulatory requirements or material changes in existing C taxation or regulatory requirements, which significantly affect the business in which the Company is engaged [3] [3]
* Technological changes which necessitate significant new investments in any of the businesses in which the Company is engaged [3] [3]
* Other factors like statutory and contractual restrictions [4] [4]

**Additional Parameters:** [5]

* In case of being prohibited to recommend/declare dividend by any regulatory body [6] [6]
* If it is deemed prudent to conserve capital for any proposed or ongoing or planned business expansion or other factors [6] [6]

It's worth noting that the Company has issued only one class of shares, and parameters for dividend payments in respect of any other class of shares will be as per the respective terms of issue and in accordance with the Applicable Laws [5].
- **Ground Truth**: Key financial parameters include standalone profits of the Company, cash flow status, capital requirements, and debt-to-equity ratios.
- **Latency**: 7.42s | **System Confidence**: 0.53
- **Metrics**:
  - **Faithfulness**: 100.00% (Matches retrieved context)
  - **Context Recall**: 0.00% (Missing key facts)
  - **Answer Relevance**: 100.00% (Directly answers question)

---

### Case 6: What is the threshold for a transaction to be considered a material related party transaction?
- **Answer**: The threshold for a transaction to be considered a material related party transaction is ten percent of the annual consolidated turnover of the company as per the last audited financial statements of the company [1]. [1]

This threshold applies to transactions with a related party, and when taken together with previous transactions during a financial year, they must exceed this percentage to be considered material [1]. [1]
- **Ground Truth**: A transaction with a related party is considered material if the transaction to be entered into individually or taken together with previous transactions during a financial year, exceeds ten percent of the annual consolidated turnover of the Company as per the last audited financial statements.
- **Latency**: 3.94s | **System Confidence**: 1.00
- **Metrics**:
  - **Faithfulness**: 0.00% (Invented details not supported by context)
  - **Context Recall**: 100.00% (Key facts present in context)
  - **Answer Relevance**: 100.00% (Directly addresses the question)

---

### Case 7: How long are disclosures hosted on the website of Supreet Chemicals Limited under the Archival Policy?
- **Answer**: Disclosures hosted on the website of Supreet Chemicals Limited under the Archival Policy are available for a period of 5 years, after which they are archived for an additional year before being destroyed as prescribed under the Companies Act, 2013 and regulations [1].

This means that any disclosures made by the Company to the Stock Exchange will be hosted on its website for at least 6 years from the date of disclosure [2].

Here is a summary of how long disclosures are hosted:

*  Disclosures are hosted on the website for a period of 5 years.
*  After 5 years, the information is archived for an additional year.
*  The archived information is then destroyed as prescribed under the Companies Act, 2013 and regulations.

This policy ensures that the Company complies with the Regulations and provides transparency to its stakeholders by hosting disclosures on its website for a specified period.
- **Ground Truth**: All disclosures hosted on the website under the listing regulations shall be hosted for a minimum period of 5 years.
- **Latency**: 7.89s | **System Confidence**: 0.29
- **Metrics**:
  - **Faithfulness**: 0.00% (Invented time frame beyond context)
  - **Context Recall**: 100.00% (Context mentions archival policy requirements)
  - **Answer Relevance**: 100.00% (Directly addresses the question)

---

### Case 8: What are the two main categories of document preservation under the policy?
- **Answer**: The two main categories of document preservation under the policy are: [1]

* Documents whose preservation shall be permanent in nature (as classified by the company) [2]
+ Documents that need to be preserved and retained permanently; [3]
+ Documents that need to be preserved and retained for a period of 8 years as specified under the Companies Act, 2013 or Regulations [3].
* Documents with preservation period of not less than eight years after completion of the relevant transactions (as per Regulation 9 of Securities and Exchange Board of India (Listing Obligations and Disclosure Requirements) Regulations, 2015) [3]
+ Documents that need to be preserved and retained for a period of 8 years as specified under the Companies Act, 2013 or Regulations; [3]
+ Documents that need to be preserved and retained for such period as prescribed under any statute or regulation as applicable to the Company; [4]
+ Where there is no such requirement as per applicable law, then for such period as the document pertains to a matter which is "Current" [4].

[3]
- **Ground Truth**: The two main categories are (a) documents whose preservation shall be permanent in nature and (b) documents whose preservation shall be for not less than eight years.
- **Latency**: 5.46s | **System Confidence**: 1.00
- **Metrics**:
  - **Faithfulness**: 0.00% (Invented categories not supported by context)
  - **Context Recall**: 100.00% (Context matches Ground Truth Answer)
  - **Answer Relevance**: 100.00% (Directly addresses the question's topic)

---

### Case 9: Who are the authorized persons to determine the materiality of an event under the Materiality Policy?
- **Answer**: The authorized persons to determine the materiality of an event under the Materiality Policy are: [1]

1. Chief Financial Officer [1] [1]
2. Company Secretary [1] [1]

These individuals have been designated by the Board of Directors as the authorized persons for determining materiality and disclosure, in accordance with Regulation 30(5) of the Listing Regulations [2].

Additionally, the Managing Director and Whole-time Director may determine materiality in the absence of the Chief Financial Officer and Company Secretary, respectively [3]. However, this is subject to the approval of the Board of Directors [4].

It's worth noting that the Board of Directors has also authorized the Committee to review and evaluate Related Party Transactions that have not been approved under the Policy prior to their consummation [5].
- **Ground Truth**: The Managing Director, Whole-time Directors, Chief Financial Officer, and Company Secretary are authorized to determine the materiality of an event.
- **Latency**: 4.81s | **System Confidence**: 0.86
- **Metrics**:
  - **Faithfulness**: 0.00% (Invented details about the Managing Director and Whole-time Director)
  - **Context Recall**: 100.00% (All key facts present in retrieved context.)
  - **Answer Relevance**: 100.00% (Directly answers question)

---

### Case 10: What is the company's commitment regarding energy conservation under the Environmental Policy?
- **Answer**: **Supreet Chemicals Limited's Commitment to Energy Conservation** [1]

The company's Environmental Policy reflects its commitment to responsible operations by emphasizing continuous evaluation of environmental impacts, pollution prevention, resource efficiency, and transparent performance monitoring [2] [2]. The policy also highlights the importance of energy conservation, with a focus on minimizing energy consumption and promoting the use of renewable energy sources [3].

**Initiatives for Energy Conservation** [3]

Supreet Chemicals has initiated several initiatives to strengthen its commitment to energy conservation, including: [2]

*  Regular training sessions and awareness campaigns to foster a culture of proactive energy-saving practices [3] [4]
*  Transitioning from manual handling to conveyor-based operations in coal sourcing and process efficiency, resulting in improved efficiency and reduced environmental impact [3] [5]
*  Optimizing coal quality for heating processes and prioritizing efficient energy consumption [4] [6]

**Energy Efficiency and Renewable Energy** [7]

The company is actively working towards improving energy efficiency and increasing the share of renewable energy in its overall consumption mix [1]. This includes:

*  Structured monitoring and continuous improvement to minimize environmental impact [7]
*  Recognizing major usage concentrations in production processes, utilities, and auxiliary operations [8]
*  Promoting the use of renewable energy sources to reduce carbon footprint [7] [9]

**Environmental Stewardship Approach**

The company's Environmental Management System (EMS) reflects its commitment to environmental stewardship by ensuring: [5]

*  Responsible use of natural resources [5]
*  Prevention of pollution and environmental degradation [5]
*  Minimization of emissions, waste, and resource consumption [5]
*  Protection of surrounding ecosystems and communities [5] [6]

**Conclusion**

Supreet Chemicals Limited is committed to conducting its operations in an environmentally responsible manner and integrating sustainability into every aspect of its business [1]. The company's Environmental Policy and initiatives for energy conservation demonstrate its dedication to minimizing environmental impact and promoting sustainable practices [2].
- **Ground Truth**: The company commits to reducing specific energy consumption, improving operational efficiency, and increasing the share of renewable energy in its overall energy mix.
- **Latency**: 10.03s | **System Confidence**: 0.87
- **Metrics**:
  - **Faithfulness**: 100.00% (Fully supported by the retrieved context)
  - **Context Recall**: 100.00% (Key facts mentioned)
  - **Answer Relevance**: 100.00% (Directly addresses the question)

---

### Case 11: What is the policy on conflict of interest for board members?
- **Answer**: The policy on conflict of interest for board members at Supreet Chemicals Limited is outlined in the Code-of-Conduct-for-the-Board-of-Directors-and-the-Senior-Management-Personnel.pdf document [1].

Key points from the documents include:

* The Board of Directors and Senior Management Personnel shall not enter into any transaction that may have a conflict with the interests of the Company, nor engage any relative or other person/entity for circumventing personal interest involved [2] [2].
* The Executive Director(s) and Senior Management Personnel shall not take up outside employment [3] [2].
* In case there is likely to be a conflict of interest, the individual should make full disclosure of all facts and circumstances to the Board of Directors or nominated Committee/Officer and obtain prior written approval [4] [4].
* Supreet Chemicals Limited has implemented a formal framework to identify, disclose, and manage conflicts of interest, ensuring that business decisions are made objectively in the best interest of the organization [1] [1].

Definitions relevant to conflict of interest include:

* "Conflict of Interest" means where the interests or benefits of one person/entity conflicts with the interests or benefits of the Company [5] [5].
* The Board/Directors shall mean the Board of Directors of Supreet Chemicals Limited (SCL) [6] [1].
* Executive Directors/Whole time Directors shall mean and include the Company's Managing Director and Directors who are in whole-time employment of SCL [6] [2].

The role and functions of board members include balancing conflicting interests of stakeholders, determining remuneration levels, and moderating situations of conflict between management and shareholder interests [7, 8].

In case of a potential conflict of interest, the individual should make full disclosure to the Board or nominated Committee/Officer and obtain prior written approval [4].
- **Ground Truth**: Board members must avoid situations where their personal interest conflicts with the interest of the Company, and disclose any relationships or transactions to the Board.
- **Latency**: 7.37s | **System Confidence**: 0.75
- **Metrics**:
  - **Faithfulness**: 100.00% (Fully matches retrieved context)
  - **Context Recall**: 100.00% (Key facts present in context)
  - **Answer Relevance**: 100.00% (Directly addresses user question)

---

### Case 12: Who acts as the Chief Investor Relations Officer under the Fair Disclosure Code?
- **Answer**: The Chief Investor Relations Officer (CIRO) under the Fair Disclosure Code is the Compliance Officer of the Company, who is responsible for dealing with the dissemination of information and disclosure of unpublished price sensitive information [1].

[1] [2] [3]
- **Ground Truth**: The Compliance Officer / Company Secretary acts as the Chief Investor Relations Officer (CIRO) to deal with dissemination of information and disclosure of UPSI.
- **Latency**: 3.78s | **System Confidence**: 0.50
- **Metrics**:
  - **Faithfulness**: 0.00% (Invented CIRO role not supported by context)
  - **Context Recall**: 100.00% (Key facts present in context)
  - **Answer Relevance**: 0.00% (Off-topic response)

---

### Case 13: What is the role of the Risk Management Committee?
- **Answer**: The role of the Risk Management Committee is multifaceted and crucial in ensuring the overall risk management framework of an organization. The committee's primary objectives include:

* Identifying risks impacting the company's business and documenting their process of risk identification, risk minimization, and risk optimization as part of a risk management policy or strategy [1] [1].
* Affirming and disclosing critical risk management frameworks across the company to its members, which are overseen once every six months by the Board [1] [1].
* Reviewing and monitoring the effectiveness of mitigation measures through regular internal reviews, compliance checks, audits, and monitoring of safety and environmental performance indicators [2] [2].

The committee plays a key role in addressing operational matters, workplace safety, and employee welfare issues at the grassroots level [3]. It also includes representatives from various departments, such as HR, plant supervisors, engineers, chemists, operators, and workmen, creating a collaborative platform for dialogue between management and employees [3] [3].

In terms of risk management, the committee is responsible for:

* Estimating the probability of risk assumption with available data and information and working out appropriate risk treatments in areas such as operations, threats, and likelihood of occurrence [4] [4].
* Reviewing and updating the company's risk management policy and strategy to ensure alignment with its mission and risk appetite [5] [5].

The committee also ensures that significant risks and their status are reported to senior management and the Board, ensuring oversight and timely decision-making [2] [2]. Additionally, it sets up a mechanism to carry out its functions, which may include delegating powers to executive directors or senior management as deemed necessary [6] [6].

Overall, the Risk Management Committee plays a vital role in identifying, assessing, and mitigating risks that could impact an organization's business, ensuring a proactive and effective risk management framework.

References:
[1]
[3]
[4]
[2]
[6]
[5]
- **Ground Truth**: The Risk Management Committee is responsible for monitoring and reviewing the risk management plan, assessing strategic/operational/financial risks, and reporting to the Board.
- **Latency**: 9.59s | **System Confidence**: 0.64
- **Metrics**:
  - **Faithfulness**: 0.00% (Invented committee name and roles)
  - **Context Recall**: 100.00% (Key facts present in context)
  - **Answer Relevance**: 100.00% (Directly answers question)

---

### Case 14: What are the criteria for paying commission to Non-Executive Directors?
- **Answer**: I don't have enough information from the provided documents.
- **Ground Truth**: The commission is determined based on their attendance, participation in Board meetings, and is subject to the approval of shareholders and the limit of net profits under the Act.
- **Latency**: 4.44s | **System Confidence**: 0.00
- **Metrics**:
  - **Faithfulness**: 0.00% (invented answer lacks context)
  - **Context Recall**: 100.00% (Key facts mentioned or referenced)
  - **Answer Relevance**: 0.00% (Off-topic and insufficient answer)

---

### Case 15: Which unit of Supreet Chemicals Limited was newly added to the reporting boundary in FY 2024-25?
- **Answer**: Based on the provided documents, Supreet Chemicals Limited has expanded its reporting boundary to include Unit 2 in FY 2024-25 [1]. This change improves the completeness of disclosures and reflects a more comprehensive organizational footprint [2].

[2]

There is no mention of any other unit being newly added to the reporting boundary in FY 2024-25 apart from Unit 2 [1].
- **Ground Truth**: Unit 2 was newly incorporated within the reporting boundary for disclosures in the FY 2024-25 ESG report.
- **Latency**: 3.73s | **System Confidence**: 1.00
- **Metrics**:
  - **Faithfulness**: 0.00% (Invents new information not supported by context)
  - **Context Recall**: 100.00% (Key facts present in context)
  - **Answer Relevance**: 100.00% (Directly answers question about Supreet Chemicals Limited)

---

### Case 16: Are employees allowed to accept gifts under the Code of Conduct?
- **Answer**: Based on the provided documents, employees are allowed to accept nominal gifts that are customarily given and of commemorative nature for special events, as stated in Section c) Gifts and donations of the Code of Business Conduct--Ethics-code.pdf [1] [2]. However, it is essential to note that these gifts should be of a nominal value and not intended to influence business decisions or obtain uncompetitive favors [3].

It's also worth mentioning that accepting gifts may be subject to interpretation under this Code of Ethics and Business Conduct, as stated in Section p) Interpretation of Code [2] [2]. In such cases, the Board of Directors or any designated person/committee has the authority to waive compliance with this Code for specific individuals [4].

Additionally, the Code of Conduct emphasizes the importance of adhering to the principles outlined in the Code, including confidentiality, fair competition, anti-corruption, human rights, and compliance with applicable laws [5] [6]. Employees are required to acknowledge and adhere to the Code as part of their employment [5].

There is no explicit mention of accepting gifts being prohibited or restricted under other sections of the provided documents.
- **Ground Truth**: Employees must not accept gifts, hospitality, or favors except token gifts of low value that are customary, subject to disclosure to HODs.
- **Latency**: 6.20s | **System Confidence**: 0.86
- **Metrics**:
  - **Faithfulness**: 100.00% (No contradictions found)
  - **Context Recall**: 100.00% (Key facts present in retrieved context)
  - **Answer Relevance**: 100.00% (Directly addresses user question)

---

### Case 17: What is the standard policy for rollover vacation days?
- **Answer**: I don't have enough information from the provided documents.
- **Ground Truth**: There is no information regarding vacation rollover or paid leaves in the provided documents. The system must refuse to answer.
- **Latency**: 2.93s | **System Confidence**: 0.00
- **Metrics**:
  - **Faithfulness**: 100.00% (Correctly refused to answer out-of-document query)
  - **Context Recall**: 100.00% (Correctly identified that context does not contain the answer)
  - **Answer Relevance**: 100.00% (Correctly addressed the query with refusal statement)

---

### Case 18: What is the company's password complexity requirement?
- **Answer**: I don't have enough information from the provided documents.
- **Ground Truth**: There is no information regarding password complexity or IT security guidelines in the provided documents. The system must refuse to answer.
- **Latency**: 3.50s | **System Confidence**: 0.00
- **Metrics**:
  - **Faithfulness**: 100.00% (Correctly refused to answer out-of-document query)
  - **Context Recall**: 100.00% (Correctly identified that context does not contain the answer)
  - **Answer Relevance**: 100.00% (Correctly addressed the query with refusal statement)

---

### Case 19: Who is the company's external auditor for IT systems?
- **Answer**: I don't have enough information from the provided documents.
- **Ground Truth**: There is no information regarding external IT systems auditors in the provided documents. The system must refuse to answer.
- **Latency**: 3.69s | **System Confidence**: 0.00
- **Metrics**:
  - **Faithfulness**: 100.00% (Correctly refused to answer out-of-document query)
  - **Context Recall**: 100.00% (Correctly identified that context does not contain the answer)
  - **Answer Relevance**: 100.00% (Correctly addressed the query with refusal statement)

---

### Case 20: What is the leave travel allowance policy for management trainees?
- **Answer**: I don't have enough information from the provided documents.
- **Ground Truth**: There is no information regarding leave travel allowances or trainee benefit packages in the provided documents. The system must refuse to answer.
- **Latency**: 3.48s | **System Confidence**: 0.00
- **Metrics**:
  - **Faithfulness**: 100.00% (Correctly refused to answer out-of-document query)
  - **Context Recall**: 100.00% (Correctly identified that context does not contain the answer)
  - **Answer Relevance**: 100.00% (Correctly addressed the query with refusal statement)

---
