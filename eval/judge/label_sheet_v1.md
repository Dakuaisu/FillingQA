# Judge validation label sheet (PRD 11.3)

50 (item, answer) pairs drawn with seed 20261005 from dev run 19693d4aa874 (claude_cli, claude-haiku-4-5-20251001), proportional by source {'llm_seeded': 15, 'xbrl_auto': 35}. OWNER-BLOCKED: label each 1-5 in eval/judge/labels_v1.yaml, before seeing any judge score.

Rubric:
- 5: Correct and complete: every material fact in the reference is stated and none is contradicted; figures match the reference at its printed precision, for the right company and period.
- 4: Correct in substance with a minor gap: the main fact is right, but a secondary detail is missing or a figure is rounded (within 0.5%) without changing the meaning.
- 3: Partially correct: some required facts are right and others are missing or wrong (for example one of two compared values, or the right figure for the wrong period).
- 2: Mostly incorrect: the main figure or claim is wrong, though related information from the filings is present.
- 1: Incorrect or no answer: wrong, irrelevant, invented, or a refusal when the reference has an answer. For an item whose reference is null (the system should abstain), giving a specific answer scores 1 and declining scores 5.

## seed_0003 (llm_seeded, table)

- Question: In Apple Inc.'s Q2 FY2026 10-Q, what was the fair value of corporate debt securities as of September 27, 2025?
- Reference: $46,560
- Answer:

```
# Answer

According to Apple Inc.'s Q2 FY2026 10-Q filing, **the fair value of corporate debt securities as of September 27, 2025 was $46,560 million** (or approximately $46.56 billion).

This can be found in the fair value measurement table in Part I, Item 1: Financial Statements of the filing, where corporate debt securities are classified as Level 2 investments. The breakdown shows:
- Adjusted Cost: $47,210 million
- Unrealized Gains: $266 million
- Unrealized Losses: $(916) million
- **Fair Value: $46,560 million**

Of this amount, $10,623 million was classified as current marketable securities and $35,937 million as non-current marketable securities.
```

## seed_0012 (llm_seeded, table)

- Question: What was the total goodwill balance for Costco Wholesale Corp at September 3, 2023, the end of fiscal year 2023, across all segments?
- Reference: $994
- Answer:

```
# Answer

I cannot answer this question based on the provided excerpts. The SEC filing excerpts supplied are all from **Target Corporation (TGT)**, not Costco Wholesale Corp. Additionally, the excerpts contain only revenue/sales data from 10-Q filings and do not include any goodwill balance information.

To answer your question about Costco Wholesale Corp's total goodwill balance at September 3, 2023 (end of fiscal year 2023), I would need:

- Costco's 10-K filing for fiscal year 2023 (filed in October 2023)
- Specifically, sections covering:
  - Consolidated Balance Sheet showing goodwill
  - Goodwill impairment testing disclosures
  - Segment reporting with goodwill details by segment

Would you be able to provide the relevant Costco SEC filings, or would you like me to help you find this information?
```

## seed_0013 (llm_seeded, table)

- Question: What were Costco Wholesale Corp's total assets in total across all segments as of February 15, 2026, the end of its Q2 FY2026 period?
- Reference: 83,639
- Answer:

```
# Answer

I cannot answer this question based on the provided excerpts. 

The SEC filing excerpts you've supplied are all from **JPMorgan Chase & Co (JPM)** 10-Q filings, not from Costco Wholesale Corp. The excerpts contain information about JPMorgan Chase's wholesale nonaccrual loan activity and wholesale net charge-offs/recoveries for various periods.

To find Costco Wholesale Corp's total assets as of February 15, 2026 (the end of its Q2 FY2026 period), you would need to access **Costco's 10-Q filing** for that quarter, where consolidated balance sheet information showing total assets would typically appear in Part I, Item 1 (Financial Statements).

If you can provide Costco's actual SEC filings or the relevant excerpts from those filings, I'd be happy to help you find the total assets figure.
```

## seed_0015 (llm_seeded, table)

- Question: In Costco Wholesale Corp's 10-Q for Q1 FY2025, what was the total Available-For-Sale Fair Value of investments across all maturity periods?
- Reference: $691
- Answer:

```
# Costco Wholesale Corp Q1 FY2025 Available-For-Sale Fair Value

Based on the SEC filing excerpt from Costco's 10-Q for Q1 FY2025 (as of November 24, 2024), the **total Available-For-Sale Fair Value of investments across all maturity periods was $691 million**.

This breaks down as follows:

| Maturity Period | Available-For-Sale Fair Value |
|---|---|
| Due in one year or less | $132 million |
| Due after one year through five years | $408 million |
| Due after five years | $151 million |
| **Total** | **$691 million** |

These investments consisted primarily of government and agency securities, which had a cost basis of $702 million with unrealized losses of $11 million, resulting in the recorded fair value of $691 million.
```

## seed_0020 (llm_seeded, table)

- Question: In JPMorgan Chase & Co's Q2 FY2026 10-Q (as of June 30, 2026), what were the total assets, in millions, of the firm-administered multi-seller conduits?
- Reference: 20,255
- Answer:

```
# Answer

According to JPMorgan Chase & Co's Q2 FY2026 10-Q filing (as of June 30, 2026), the **total assets of the firm-administered multi-seller conduits were $20,255 million**.

This figure is comprised of:
- Loans: $20,140 million
- Other assets: $115 million
- Trading assets: $— million

This information is found in the VIE (Variable Interest Entities) assets table in Part I, Item 1 of the Financial Statements section of the Q2 FY2026 10-Q.
```

## seed_0036 (llm_seeded, table)

- Question: What was Target Corporation's total plan assets fair value as of January 31, 2025, in its FY2024 fair value measurements table?
- Reference: $3,371
- Answer:

```
# Answer

According to Target Corporation's FY2024 10-K filing, the **total plan assets fair value as of January 31, 2025 was $3,371 million**.

This figure is shown in the Fair Value Measurements table in Item 8 (Financial Statements and Supplementary Data) of the FY2024 10-K filing.
```

## seed_0037 (llm_seeded, table)

- Question: In Target Corporation's Q3 FY2023 10-Q, what was the total accumulated other comprehensive income (loss) balance as of October 28, 2023?
- Reference: $(430)
- Answer:

```
# Answer

Based on Target Corporation's Q3 FY2023 10-Q filing, the **total accumulated other comprehensive income (loss) balance as of October 28, 2023 was $(430) million** (a loss of $430 million).

This balance consisted of:
- **Cash Flow Hedges:** $287 million
- **Currency Translation Adjustment:** $(24) million
- **Pension:** $(693) million

The balance decreased from $(419) million at January 28, 2023, due to a net decrease of $(11) million in accumulated other comprehensive income during the nine months ended October 28, 2023.
```

## seed_0038 (llm_seeded, table)

- Question: What was Target Corporation's total investment in share repurchases for the six months ended August 2, 2025 (Q2 FY2025)?
- Reference: $251
- Answer:

```
# Target Corporation Share Repurchases - Six Months Ended August 2, 2025

Based on the SEC filing excerpt from Target Corporation's Q2 FY2025 10-Q:

**Total investment in share repurchases: $251 million**

This represents the repurchase of **2.2 million shares** at an **average price of $114.59 per share** during the six-month period ended August 2, 2025.
```

## seed_0052 (llm_seeded, synthesis)

- Question: In Bank of America Corporation's fiscal year 2023 10-K, why does the company apply less reliance to broker quotes in less active markets when valuing assets and liabilities?
- Reference: Because broker quotes in less active markets may only be indicative, they are less reliable. The company also applies a higher degree of reliance to data that is more directly observable and less reliance to data developed through a broker's or pricing service's own internal modeling.
- Answer:

```
# Answer

Based on the excerpts provided, I cannot find information that directly addresses your question about why Bank of America applies less reliance to broker quotes in less active markets.

The excerpts you've provided focus on:
- Residual value insurance for leases
- Other asset-backed VIEs (Variable Interest Entities)
- Valuation adjustments on derivatives (CVA, FVA, DVA)
- Lease income tables

**However**, the answer to your question would typically be found in the **Fair Value Measurement disclosure** section of the 10-K (usually under Item 8: Financial Statements and Supplementary Data), which discusses:

1. **Valuation Hierarchy levels** (Level 1, 2, and 3 inputs)
2. **Broker quotes reliability** - In less active markets, broker quotes may be based on limited transaction data or theoretical models rather than actual executed trades
3. **Observable vs. unobservable inputs** - Less active markets mean fewer observable transactions, requiring greater reliance on modeling assumptions

The general principle is that **less active markets produce less reliable broker quotes** because they're based on fewer actual transactions, potentially stale pricing data, or theoretical valuations rather than market-confirmed prices.

To get the complete answer specific to BAC's 2023 10-K disclosures on this topic, you would need to review the full Fair Value Measurement note, which isn't included in these excerpts.
```

## seed_0057 (llm_seeded, synthesis)

- Question: In Costco Wholesale Corp's 10-K for fiscal year 2024 (FY2024), why does management say it maintains employee compensation above the industry average rather than seeking to minimize wages and benefits?
- Reference: Management believes that paying better than the industry average for much of its workforce is necessary to achieve its longer-term objectives of reducing employee turnover, increasing productivity and enhancing employee satisfaction, even if that means absorbing costs other employers might pass through to their workforces.
- Answer:

```
# Costco's Rationale for Above-Average Employee Compensation

Based on the excerpts provided, I need to note that **the specific FY2024 Item 1 narrative text is not included in the excerpts**—only FY2023 and FY2025 language are shown. However, the reasoning appears consistent across these periods:

## Management's Key Rationale:

**1. Warehouse Productivity & Efficiency**
- Management explicitly states: "We believe that our warehouses are among the most productive in the retail industry, owing largely to the commitment and efficiency of our employees."
- The above-average compensation is presented as a driver of productivity, not a cost to minimize.

**2. High Employee Retention**
- Competitive wages and benefits directly contribute to retention rates that Costco considers "especially for the industry, a high retention rate" (90% in 2023 for employees with 1+ year tenure; 94% in 2025).
- Lower turnover reduces hiring and training costs while maintaining an experienced workforce.

**3. Career Investment vs. Employment**
- Costco seeks to provide employees "not merely with employment but careers," supported by:
  - Promotion from within
  - Target of 50%+ full-time employment
  - Employee development programs

## Strategic Logic:
Rather than minimizing wages, Costco frames above-average compensation as **enabling business productivity and efficiency**. The implicit reasoning is that committed, experienced employees drive superior warehouse operations and customer service, which supports Costco's competitive positioning.

**Note:** To see the exact FY2024 management explanation, the full Item 1: Business section from the FY2024 10-K would be needed.
```

## seed_0067 (llm_seeded, synthesis)

- Question: In NVIDIA Corp's 10-Q for Q3 FY2026, what kinds of customer arrangements does the footnote say give rise to the unearned revenue included in the balance sheet line it references?
- Reference: Unearned revenue related to hardware and software support and cloud services, meaning NVIDIA's deferred amounts come from support and service arrangements.
- Answer:

```
# Answer

Based on the excerpts provided from NVIDIA's Q3 FY2026 10-Q, the footnote indicates that unearned revenue included in the balance sheet arises from the following customer arrangements:

1. **Hardware and software support**
2. **Cloud services**

This is stated in footnote (2) from chunk 0001045810-25-000230:188.0:191.0, which notes: "Includes unearned revenue related to hardware and software support and cloud services."
```

## seed_0069 (llm_seeded, synthesis)

- Question: In NVIDIA Corp's 10-Q for Q2 FY2026, what does the company say would be the consequence if it cannot create a competitive product for China's data center market that receives USG approval?
- Reference: NVIDIA says it would effectively be foreclosed from competing in China's data center computing/compute market, with a material and adverse impact on its business, operating results, and financial condition.
- Answer:

```
# Answer

Based on the provided excerpts, I don't have a filing explicitly labeled as "Q2 FY2026 10-Q," but the FY2026 10-K (which covers that period) directly addresses this question in its Risk Factors section.

According to NVIDIA's disclosure, if the company cannot create a competitive product for China's data center market that receives approval from both the USG and the Chinese government, the consequence would be:

> **"...our lost opportunity and the benefit to our competitors will have a material and adverse impact on our business, operating results, and financial condition."**

The filing expands on this by noting that:

1. **They are already experiencing foreclosure** from China's data center market under current export controls
2. **Competitors have benefited** - their effective foreclosure has already "helped our competitors build larger developer and customer ecosystems to challenge us worldwide"
3. **Long-term competitive damage** - the lost opportunity in China's market poses a material and adverse threat to their business going forward

The company emphasizes the severity of this situation by stating it in their Risk Factors section, indicating this is a significant concern for their business strategy and financial performance.
```

## seed_0070 (llm_seeded, synthesis)

- Question: In Pfizer Inc's FY2023 10-K, how does Pfizer characterize the trend in the formulary placement of its branded products by managed care organizations, and what effect does it say continuing managed care cost-containment efforts may have on the company?
- Reference: Pfizer says its branded products are increasingly being placed on higher tiers or in a non-preferred status, and that continuing efforts by managed care entities to contain or reduce healthcare costs and/or impose price controls may adversely affect demand for its products and its financial performance.
- Answer:

```
# Pfizer's Characterization of Formulary Placement Trends in FY2023 10-K

Based on the FY2023 10-K excerpt provided (Item 1: BUSINESS), Pfizer characterizes the formulary placement trend for its branded products as follows:

## Trend Characterization
**Pfizer's branded products are increasingly being placed on the higher tiers or in a non-preferred status** by managed care organizations.

## Anticipated Effect of Cost-Containment Efforts
Pfizer states that **continuing efforts by managed care entities to contain or reduce costs of healthcare and/or impose price controls may adversely affect demand for our products and our financial performance.**

## Context
The company notes that while it continues to seek to ensure its major products are included on MCO formularies, it faces competitive pressure because:
- MCOs seek to exclude high-cost drugs from formularies as part of their cost management strategies
- Pharmaceutical companies compete for formulary placement primarily based on unique product features (efficacy, ease of use, side effects) and overall therapy cost
- Exclusion from formularies or placement restrictions can significantly impact drug usage among MCO-managed patient populations

This disclosure highlights a key business risk that Pfizer faces from the healthcare industry's trend toward managed care and cost containment.
```

## seed_0071 (llm_seeded, synthesis)

- Question: For Pfizer Inc's fiscal year 2023, what was the nature of the $474 million in legal charges, and what does the filing say about the products they primarily relate to?
- Reference: The charges primarily represent product liability and other legal expenses tied to products that Pfizer discontinued and/or divested, and to a lesser extent legal obligations related to pre-acquisition matters. This indicates the costs stem mainly from legacy products no longer in Pfizer's portfolio rather than from its current operations.
- Answer:

```
# Pfizer FY2023 Legal Charges ($474 Million)

Based on Pfizer's FY2023 10-K filing, the **nature of the $474 million in legal charges** was:

1. **Primary (majority):** Certain **product liability and other legal expenses** related to **products discontinued and/or divested by Pfizer**

2. **Secondary (lesser extent):** Legal obligations related to **pre-acquisition matters**

## Key Points

The filing specifically states these charges were "primarily representing certain product liability and other legal expenses related to products discontinued and/or divested by Pfizer, and to a lesser extent, legal obligations related to pre-acquisition matters."

This indicates that Pfizer was primarily addressing historical liabilities from products it no longer owns or operates, rather than issues with current products. This is a common pattern for large pharmaceutical companies that divest product lines through M&A transactions and must retain certain legal obligations related to those divested assets.

The filing shows this was part of a broader trend—in 2022, Pfizer recorded $230 million in similar legal charges for discontinued/divested products, and in 2021, $162 million, indicating ongoing management of legacy product liabilities.
```

## seed_0072 (llm_seeded, synthesis)

- Question: In Pfizer Inc's FY2025 10-K, how does Pfizer characterize the potential impact on its results of operations if it receives adverse decisions in its patent litigation matters?
- Reference: Pfizer says adverse decisions in these patent matters could have a material adverse effect on its results of operations, which means it sees the outcomes of these challenges as a potentially significant financial risk.
- Answer:

```
# Pfizer's Characterization of Patent Litigation Impact

Based on the excerpts provided, I should note that **the specific materials shown are from Pfizer's 10-Q quarterly filings (Q3 FY2025, Q2 FY2025, and Q1 FY2026) rather than the FY2025 10-K annual report** you specifically asked about. However, these filings provide insight into how Pfizer characterizes patent litigation impacts:

## Key Characterizations:

**1. Financial Impact Recognition**
Pfizer identifies "the risk and impact of an adverse decision or settlement and risk related to the adequacy of reserves related to legal proceedings" as material factors affecting results of operations.

**2. Specific Intellectual Property Risks**
Pfizer characterizes adverse patent decisions as potentially resulting in:
- **Loss of patent coverage** from invalidity claims
- **Patent infringement claims** (asserted and unasserted)
- Patent revocation risks

**3. Direct Costs**
The company identifies:
- Legal defense costs
- Insurance expenses
- Settlement costs and contingencies

**4. Broader Impact**
Pfizer frames patent litigation within the broader context of intellectual property risks that could affect product protection and enforcement capabilities.

## Limitation:
To provide you with the precise language from the **FY2025 10-K annual report specifically**, I would need that document's excerpts. The materials provided are from quarterly filings, which may have slightly different or more detailed language in the annual report. Would you like me to help locate the specific FY2025 10-K filing?
```

## cmp_0003 (xbrl_auto, comparison)

- Question: What did Apple report as its payments for property, plant and equipment for the first two quarters of fiscal 2024 and for the first two quarters of fiscal 2026, and what is the difference?
- Reference: $4,344 million for the first two quarters of fiscal 2026, compared with $4,388 million for the first two quarters of fiscal 2024: a decrease of $44 million.
- Answer:

```
# Apple Property, Plant and Equipment Analysis

Based on the SEC filing excerpts provided, I can calculate the change in gross property, plant and equipment (which approximates capital expenditures) for the specified periods:

## First Two Quarters of Fiscal 2024 (Q1 + Q2 FY2024)
- **Starting balance** (September 30, 2023): $114,599 million
- **Ending balance** (March 30, 2024): $115,243 million
- **Net increase**: $644 million

## First Two Quarters of Fiscal 2026 (Q1 + Q2 FY2026)
- **Starting balance** (September 27, 2025): $125,848 million
- **Ending balance** (March 28, 2026): $127,557 million
- **Net increase**: $1,709 million

## Difference
**$1,709 million - $644 million = $1,065 million**

Apple invested $1,065 million more in property, plant and equipment during the first six months of fiscal 2026 compared to the first six months of fiscal 2024.

**Note:** This calculation is based on the net change in gross PP&E from balance sheet data. For precise "payments" figures, the Statement of Cash Flows (capital expenditures line item) from the full 10-Q filings would provide the most accurate cash outflow data.
```

## cmp_0004 (xbrl_auto, comparison)

- Question: How did Apple's total revenue for the second quarter of fiscal 2026 compare with the second quarter of fiscal 2024?
- Reference: $111,184 million for the second quarter of fiscal 2026, compared with $90,753 million for the second quarter of fiscal 2024: an increase of $20,431 million.
- Answer:

```
# Apple's Q2 Revenue Comparison: FY2026 vs FY2024

Based on the SEC filings provided, here's how Apple's total revenue compared:

| Metric | Q2 FY2026 | Q2 FY2024 | Change |
|--------|-----------|-----------|--------|
| **Total Net Sales** | **$111,184 million** | **$90,753 million** | **+$20,431 million** |
| | | | **(+22.5%)** |

## Key Points:

- **Apple's Q2 FY2026 revenue was significantly higher** than Q2 FY2024, increasing by approximately **$20.4 billion or 22.5%**

- This growth was driven across most product categories:
  - **iPhone**: $56,994M (FY2026) vs $45,963M (FY2024) - up 24%
  - **Services**: $30,976M (FY2026) vs $23,867M (FY2024) - up 30%
  - **iPad**: $6,914M (FY2026) vs $5,559M (FY2024) - up 24%
  - **Mac**: $8,399M (FY2026) vs $7,451M (FY2024) - up 13%
  - **Wearables, Home and Accessories**: $7,901M (FY2026) vs $7,913M (FY2024) - essentially flat

The strong year-over-year growth was particularly pronounced in iPhone and Services revenue.
```

## cmp_0014 (xbrl_auto, comparison)

- Question: What did Costco report as its cost of revenue for the first three quarters of fiscal 2024 and for the first three quarters of fiscal 2026, and what is the difference?
- Reference: $180,748 million for the first three quarters of fiscal 2026, compared with $152,770 million for the first three quarters of fiscal 2024: an increase of $27,978 million.
- Answer:

```
# Unable to Answer from Provided Excerpts

I appreciate the question, but unfortunately the excerpts provided do not contain the actual financial data needed to answer it. The chunks included only contain:

- Fiscal year end information
- Accounting policies (use of estimates)
- Recent accounting pronouncements not yet adopted
- Note 2 headers (Investments)

These are boilerplate sections from the 10-Q filings' notes to financial statements, not the actual condensed consolidated statements of income where the "Cost of revenues" line item would appear.

## What I Would Need

To find Costco's cost of revenue for the first three quarters (36 weeks) of each fiscal year, I would need excerpts from:

1. **Condensed Consolidated Statements of Income** from the Q3 FY2024 10-Q (showing YTD 36-week results through May 12, 2024)
2. **Condensed Consolidated Statements of Income** from the Q3 FY2026 10-Q (showing YTD 36-week results through May 10, 2026)

These statements would contain the line item "Costs of revenues" or "Cost of goods sold" with the actual dollar amounts.

Would you be able to provide those specific financial statement excerpts?
```

## cmp_0035 (xbrl_auto, comparison)

- Question: Target payments for property, plant and equipment, the first quarter of fiscal 2024 versus the first quarter of fiscal 2026: what are the two figures and the difference?
- Reference: $1,035 million for the first quarter of fiscal 2026, compared with $674 million for the first quarter of fiscal 2024: an increase of $361 million.
- Answer:

```
# Target Property, Plant and Equipment Expenditures: Q1 FY2024 vs Q1 FY2026

Based on the Consolidated Statements of Cash Flows from Target's SEC filings:

| Period | Expenditures for Property and Equipment |
|--------|------------------------------------------|
| Q1 FY2024 (Three Months Ended May 4, 2024) | **$674 million** |
| Q1 FY2026 (Three Months Ended May 2, 2026) | **$1,035 million** |
| **Difference** | **$361 million** |

**Summary:** Target's capital expenditures for property, plant and equipment increased by $361 million (approximately 54%) from Q1 FY2024 to Q1 FY2026, rising from $674 million to $1,035 million.
```

## cmp_0039 (xbrl_auto, comparison)

- Question: What is the difference between Exxon Mobil's total assets at the end of the first quarter of fiscal 2025 and at the end of the first quarter of fiscal 2024?
- Reference: $451,908 million at the end of the first quarter of fiscal 2025, compared with $377,918 million at the end of the first quarter of fiscal 2024: an increase of $73,990 million.
- Answer:

```
# Exxon Mobil Total Assets Comparison: Q1 FY2025 vs Q1 FY2024

Based on the SEC filings provided:

| Period | Total Assets |
|--------|--------------|
| **March 31, 2025 (Q1 FY2025)** | **$451,908 million** |
| **March 31, 2024 (Q1 FY2024)** | **$377,918 million** |
| **Difference** | **$73,990 million** |

**Answer: Exxon Mobil's total assets increased by approximately $74.0 billion** from the end of Q1 FY2024 to the end of Q1 FY2025.

This represents an increase of about 19.6% year-over-year. The significant growth in total assets was driven primarily by increases in property, plant and equipment (from $213.7 billion to $292.6 billion), as well as increases in investments, advances and long-term receivables, and other current assets.
```

## xbrl_0001 (xbrl_auto, xbrl_numeric)

- Question: What did Apple report as its research and development expense for fiscal 2023?
- Reference: $29,915 million for the fiscal year ended September 30, 2023.
- Answer:

```
# Apple's R&D Expense for Fiscal 2023

Based on the provided SEC filing excerpts, I cannot find the specific dollar amount for Apple's research and development expense for fiscal 2023.

The excerpt from Apple's FY2023 10-K filing (chunk 0000320193-23-000106) discusses R&D expenses qualitatively, noting that:

> "The year-over-year growth in R&D expense in 2023 was driven primarily by increases in headcount-related expenses."

However, this excerpt only contains the **Management's Discussion and Analysis (MD&A)** section, which explains the reasons for changes in expenses rather than providing the actual financial figures. The specific dollar amount would typically be found in Apple's **Consolidated Statements of Operations** in the 10-K filing, which is not included in these excerpts.

To find Apple's exact R&D expense for fiscal 2023, you would need to review the complete financial statements section of Apple's FY2023 10-K filing.
```

## xbrl_0005 (xbrl_auto, xbrl_numeric)

- Question: What was the balance of Apple's cash and cash equivalents on December 28, 2024?
- Reference: $30,299 million as of December 28, 2024.
- Answer:

```
# Apple's Cash and Cash Equivalents on December 28, 2024

Based on the SEC filing excerpts provided (Apple Inc.'s Q1 FY2025 10-Q), **Apple's cash and cash equivalents totaled $30,299 million** as of December 28, 2024.

This total comprised:
- **Cash**: $27,073 million
- **Money market funds**: $937 million
- **U.S. Treasury securities**: $903 million
- **U.S. agency securities**: $314 million
- **Certificates of deposit and time deposits**: $874 million
- **Commercial paper**: $101 million
- **Non-U.S. government securities**: $50 million
- **Corporate debt securities**: $47 million
```

## xbrl_0016 (xbrl_auto, xbrl_numeric)

- Question: What did Apple report as its operating income for the third quarter of fiscal 2026?
- Reference: $35,695 million for the three months ended June 27, 2026.
- Answer:

```
# Answer

Based on the SEC filings provided, **the operating income figure for Q3 fiscal 2026 is not included in the excerpts available to me.**

The Q3 FY2026 10-Q excerpt (dated June 27, 2026) only contains the **Operating Expenses** table, which shows:
- Total operating expenses: **$19,075 million**

However, to answer your question about **operating income**, I would need the full income statement from that filing, which would typically show:
- Net sales/Revenue
- Gross profit
- Operating expenses (which we have)
- **Operating income** (Revenue - Operating Expenses, or Gross Profit - Operating Expenses)

To find Apple's Q3 FY2026 operating income, you would need to access the complete income statement section of the Q3 FY2026 10-Q filing, which is not included in the excerpts provided.
```

## xbrl_0019 (xbrl_auto, xbrl_numeric)

- Question: How much net cash provided by operating activities did Apple report for the fiscal year ended September 27, 2025?
- Reference: $111,482 million for the fiscal year ended September 27, 2025.
- Answer:

```
# Answer

Based on the excerpts provided, I **cannot find the specific net cash provided by operating activities** for Apple's fiscal year ended September 27, 2025.

While the excerpts include Apple's FY2025 10-K filing, the provided chunks only show:
- Supplemental cash flow disclosures (cash paid for income taxes: $43,369 million)
- Consolidated statements of operations data

The main operating activities section of the cash flow statement for FY2025 is not included in the excerpts provided. To answer this question, you would need to access the complete **Consolidated Statements of Cash Flows** from Apple's FY2025 10-K filing, specifically the line item for "Net cash provided by operating activities" for the year ended September 27, 2025.
```

## xbrl_0020 (xbrl_auto, xbrl_numeric)

- Question: Apple payments for repurchases of common stock, the first quarter of fiscal 2026: what was the figure?
- Reference: $24,701 million for the three months ended December 27, 2025.
- Answer:

```
# Apple Q1 FY2026 Share Repurchases

Based on the provided SEC filing excerpts, **I cannot find a specific figure for Q1 FY2026 alone**.

Here's what the excerpts contain:

- **6 months ended March 28, 2026** (Q1 + Q2 FY2026): **$36.0 billion**
- **9 months ended June 27, 2026** (Q1 + Q2 + Q3 FY2026): **$61.8 billion**

The six-month figure of $36.0 billion covers both the first and second quarters combined, but the excerpts don't break this down into Q1-specific data.

**To find the Q1 FY2026 figure**, you would need to either:
1. Review Apple's Q1 FY2026 10-Q filing directly (for the quarter ended December 28, 2025), or
2. Calculate it as: $36.0B (six months) minus the Q2-only repurchases

The filing excerpts provided don't contain the Q1-specific information needed to answer your question precisely.
```

## xbrl_0027 (xbrl_auto, xbrl_numeric)

- Question: What was the balance of Bank of America's total stockholders' equity on December 31, 2025?
- Reference: $303,243 million as of December 31, 2025.
- Answer:

```
# Bank of America's Total Stockholders' Equity - December 31, 2025

I cannot find the answer to your question in the provided SEC filing excerpts. 

The excerpts included focus on:
- Loan portfolio details (commercial and consumer loans)
- Fair value measurements of financial instruments
- Loan quality metrics (nonperforming loans, past due accounts)

To find **total stockholders' equity as of December 31, 2025**, you would need to reference:

1. **The Consolidated Balance Sheet** (typically in Item 8 - Financial Statements)
2. **The Statement of Changes in Stockholders' Equity**

These sections would show the total stockholders' equity line item at a specific point in time.

Would you be able to provide additional excerpts from Bank of America's 10-K filing that include the balance sheet or equity statement? That would allow me to give you the specific figure you're looking for.
```

## xbrl_0031 (xbrl_auto, xbrl_numeric)

- Question: What did Bank of America report as its income before income taxes for fiscal 2025?
- Reference: $37,695 million for the fiscal year ended December 31, 2025.
- Answer:

```
# Bank of America FY2025 Income Before Income Taxes

According to Bank of America's fiscal 2025 10-K filing, the corporation reported **$37,695 million** (or approximately **$37.7 billion**) in income before income tax expense for the year ended December 31, 2025.

This represents an increase from fiscal 2024, when the company reported $33,223 million in income before income taxes.
```

## xbrl_0036 (xbrl_auto, xbrl_numeric)

- Question: How much net interest income did Bank of America report for the fiscal year ended December 31, 2025?
- Reference: $60,096 million for the fiscal year ended December 31, 2025.
- Answer:

```
# Bank of America Net Interest Income - FY2025

I apologize, but the SEC filing excerpts provided do not contain information about Bank of America's net interest income for fiscal year 2025. 

The excerpts included focus on:
- Loan portfolio composition and nonperforming assets (Tables 25, 27, 30)
- Fair value measurements (Item 8)

Net interest income would typically be found in:
- **Consolidated Statements of Income** (part of the Financial Statements)
- **MD&A Results of Operations section** discussing revenue and net interest income trends

To find Bank of America's FY2025 net interest income, you would need to review:
1. The **Consolidated Statements of Income** in Item 8 of the 10-K
2. The **"Results of Operations"** or **"Net Interest Income"** section in Item 7 (MD&A)

Would you like me to help you locate this information if you can provide excerpts from those sections of the filing?
```

## xbrl_0040 (xbrl_auto, xbrl_numeric)

- Question: Bank of America income tax expense, the second quarter of fiscal 2024: what was the figure?
- Reference: $663 million for the three months ended June 30, 2024.
- Answer:

```
# Bank of America Q2 FY2024 Income Tax Expense

I cannot provide the specific income tax expense figure for the second quarter of fiscal 2024 based on the excerpts provided.

The excerpts include:
- A full-year 2024 income tax reconciliation from the 10-K (showing $2,122 million total for the entire fiscal year)
- Interest income/expense tables from the Q2 2024 10-Q

However, **the specific income tax expense line item from the Q2 2024 quarterly 10-Q is not included in the provided excerpts**. This quarterly figure would typically be found in:
- The condensed consolidated statements of income in the Q2 10-Q filing
- Or in the tax reconciliation note specific to the first half or second quarter

To find this information, you would need to access Bank of America's Q2 2024 10-Q filing (filed around July/August 2024) and look for the income tax expense in either:
1. The condensed consolidated statements of income, or
2. The income tax note disclosure

Would you like me to help you locate this document or look for additional excerpts?
```

## xbrl_0043 (xbrl_auto, xbrl_numeric)

- Question: According to its fiscal 2024 10-K, what figure did Costco report for total current assets as of September 1, 2024?
- Reference: $34,246 million as of September 1, 2024.
- Answer:

```
# Answer

According to Costco's fiscal 2024 10-K, **total current assets as of September 1, 2024 were $34,246 million** (or approximately $34.2 billion).

This figure is shown in the Consolidated Balance Sheets in Item 8: Financial Statements and Supplementary Data, and represents the sum of:
- Cash and cash equivalents: $9,906 million
- Short-term investments: $1,238 million
- Receivables, net: $2,721 million
- Merchandise inventories: $18,647 million
- Other current assets: $1,734 million
```

## xbrl_0053 (xbrl_auto, xbrl_numeric)

- Question: Costco total liabilities at the end of fiscal 2025: what was the figure?
- Reference: $47,935 million as of August 31, 2025.
- Answer:

```
# Costco Total Liabilities at End of Fiscal 2025

I cannot provide the specific total liabilities figure based on the excerpts provided. 

The excerpts you've shared are from Costco's **10-Q quarterly reports** (for Q1, Q2, and Q3 of fiscal 2025) and contain only accounting policy disclosures and fiscal year-end date information. They do not include the actual **consolidated balance sheet** where total liabilities would be reported.

## To find this information, I would need:

The **10-K annual report** for fiscal 2025 (ended August 31, 2025), specifically:
- The **Consolidated Balance Sheet** section showing total liabilities as of August 31, 2025

Since fiscal 2025 ended on August 31, 2025, and today's date is October 2, 2026, Costco's fiscal 2025 10-K should be available on the SEC's EDGAR database or Costco's investor relations website.

Would you be able to provide an excerpt from Costco's fiscal 2025 10-K balance sheet, or would you like help locating that document?
```

## xbrl_0054 (xbrl_auto, xbrl_numeric)

- Question: Costco cost of revenue, fiscal 2024: what was the figure?
- Reference: $222,358 million for the fiscal year ended September 1, 2024.
- Answer:

```
# Costco Cost of Revenue - Fiscal 2024

Based on the SEC filing excerpts provided, **I cannot find the specific cost of revenue figure** for Costco's fiscal 2024. 

The excerpts include:
- Net sales information ($249,625 million)
- Membership fee revenue ($4,828 million)
- MD&A highlights and tax information

However, the complete **Consolidated Statement of Income** (which would show the cost of revenue line item) is not included in these excerpts.

**To find this figure, you would need to:**
- Look at the full Consolidated Statements of Income in Item 8 of Costco's FY2024 10-K filing (Form 10-K for fiscal year ended September 1, 2024)
- The line item is typically labeled "Cost of sales" or "Cost of revenue"

If you have access to the complete 10-K income statement, that would show Costco's cost of revenue for fiscal 2024.
```

## xbrl_0055 (xbrl_auto, xbrl_numeric)

- Question: According to its 10-Q for the first quarter of fiscal 2024, what figure did Costco report for operating income in the 12 weeks ended November 26, 2023?
- Reference: $1,984 million for the 12 weeks ended November 26, 2023.
- Answer:

```
I cannot answer this question based on the provided excerpts. The context you've shared contains only **Target Corporation (TGT)** SEC filings from their 10-Q reports for various fiscal periods. There is no information about **Costco** in any of the excerpts provided.

To find Costco's operating income for the 12 weeks ended November 26, 2023 (from their Q1 FY2024 10-Q), you would need to provide the actual Costco 10-Q filing excerpt or access Costco's SEC filings directly through the SEC's EDGAR database.
```

## xbrl_0057 (xbrl_auto, xbrl_numeric)

- Question: What amount of payments for repurchases of common stock did Costco record in the first two quarters of fiscal 2026?
- Reference: $419 million for the 24 weeks ended February 15, 2026.
- Answer:

```
# Costco Stock Repurchases - First Half of Fiscal 2026

Based on the SEC filing excerpts provided, **Costco recorded approximately $420 million in payments for repurchases of common stock during the first two quarters of fiscal 2026**.

According to the Q2 FY2026 10-Q filing (chunk 0000909832-26-000029):

> "During the first half of 2026 and 2025, we repurchased 454,000 and 443,000 shares of common stock, at an average price per share of $924.46 and $932.03, totaling approximately $420 and $413."

**Details:**
- **Shares repurchased:** 454,000 shares
- **Average price per share:** $924.46
- **Total amount:** Approximately $420 million

The filing notes that these amounts may differ from the cash flow statements due to timing differences in unsettled repurchases at the end of each quarter.
```

## xbrl_0058 (xbrl_auto, xbrl_numeric)

- Question: How much income before income taxes did Costco report for the 36 weeks ended May 12, 2024?
- Reference: $6,627 million for the 36 weeks ended May 12, 2024.
- Answer:

```
# Answer

I cannot answer this question based on the provided SEC filing excerpts. All of the excerpts provided are from **JPMorgan Chase & Co (JPM)**, not Costco. The filings shown are JPMorgan Chase's 10-Q reports for Q2 FY2024 and Q2 FY2026.

To find Costco's income before income taxes for the 36 weeks ended May 12, 2024, you would need to:

1. Access Costco's 10-Q filing for that period (which would cover the second quarter of their fiscal year 2024)
2. Locate the Consolidated Statement of Income in that filing
3. Find the line item for "Income Before Provision for Income Taxes" for the 36-week period

If you can provide Costco's relevant SEC filing excerpts, I'd be happy to help you locate this information.
```

## xbrl_0064 (xbrl_auto, xbrl_numeric)

- Question: JPMorgan Chase noninterest income, the third quarter of fiscal 2024: what was the figure?
- Reference: $19,249 million for the three months ended September 30, 2024.
- Answer:

```
# JPMorgan Chase Q3 FY2024 Noninterest Income

Based on the SEC filings excerpts provided, I cannot locate the **exact Q3 2024 total company noninterest revenue figure** in the materials shown.

However, here's what the excerpts contain:

## Available Data:

**Q3 2023 (Prior Year Comparison):**
- Noninterest revenue: **$16,820 million** ($16.82 billion)
- Source: Q3 FY2024 10-Q consolidated financial statements table

**Q3 2024 Segment Data from MD&A:**
The management discussion shows noninterest revenue for at least two major business segments:
- One segment: $3.8 billion
- Another segment: $10.9 billion
- **Subtotal: $14.7 billion**

(These segments appear incomplete, likely missing Consumer & Community Banking and other corporate items)

## Issue:

The consolidated financial statements table excerpt showing Q3 2024 data only displays the prior-year 2023 column. The current quarter 2024 figures appear to be in the full 10-Q but are not shown in these particular excerpts.

**To get the precise Q3 2024 noninterest revenue figure, you would need to review the complete financial statements table in the actual 10-Q filing.**
```

## xbrl_0066 (xbrl_auto, xbrl_numeric)

- Question: How much net interest income did JPMorgan Chase report for the three months ended June 30, 2026?
- Reference: $25,511 million for the three months ended June 30, 2026.
- Answer:

```
# JPMorgan Chase Net Interest Income for Q2 2026

According to JPMorgan Chase's 10-Q filing for Q2 FY2026, the company reported **net interest income of $25,511 million** (or approximately **$25.5 billion**) for the three months ended June 30, 2026.

This represents a **10% increase** compared to the same period in 2025, when net interest income was $23,209 million.

**Source:** JPMorgan Chase & Co. Q2 FY2026 10-Q, Part I, Item 2: Management's Discussion and Analysis of Financial Condition and Results of Operations.
```

## xbrl_0069 (xbrl_auto, xbrl_numeric)

- Question: How much income tax expense did JPMorgan Chase report for the three months ended September 30, 2024?
- Reference: $4,080 million for the three months ended September 30, 2024.
- Answer:

```
# JPMorgan Chase Income Tax Expense for Q3 2024

According to JPMorgan Chase's Q3 FY2024 10-Q filing, the company reported **income tax expense of $4,080 million** for the three months ended September 30, 2024.

This represented a 14% increase compared to $3,582 million in the same quarter of 2023. The effective tax rate was 24.0% for Q3 2024, compared to 21.4% in Q3 2023.
```

## xbrl_0082 (xbrl_auto, xbrl_numeric)

- Question: What amount of income before income taxes did NVIDIA record in the first two quarters of fiscal 2025?
- Reference: $36,493 million for the six months ended July 28, 2024.
- Answer:

```
# Answer

Based on the provided SEC filing excerpts, I can only find **partial information** for your question:

## Q1 FY2025 (Three Months Ended April 28, 2024)
The excerpt shows that **Income before income tax was 66.5% of revenue**, but the **absolute dollar amount is not provided** in these excerpts—only the percentage is shown.

## Q2 FY2025
**No Q2 FY2025 data is included in the provided excerpts.** The chunks provided include:
- Q1 FY2025 data
- Q1 FY2026 and Q2 FY2027 data (later fiscal years)

But Q2 FY2025 (which would have ended around July 2024) is not included.

## To Answer Your Question Completely
To provide the specific dollar amounts for income before income taxes for both Q1 and Q2 of fiscal 2025, I would need:
1. The actual revenue figures (in dollars) for Q1 FY2025 to calculate the absolute income before income tax amount
2. The Q2 FY2025 10-Q filing, which is not included in these excerpts

Would you be able to provide the full Q1 FY2025 and Q2 FY2025 10-Q filings with the actual consolidated statements of income?
```

## xbrl_0088 (xbrl_auto, xbrl_numeric)

- Question: According to its 10-Q for the second quarter of fiscal 2027, what figure did NVIDIA report for inventories as of July 26, 2026?
- Reference: $31,575 million as of July 26, 2026.
- Answer:

```
# Answer

According to NVIDIA's 10-Q for the second quarter of fiscal 2027, the company reported **total inventories of $31,575 million** as of July 26, 2026.

This comprised:
- Raw materials: $11,341 million
- Work in process: $13,377 million
- Finished goods: $6,857 million
```

## xbrl_0094 (xbrl_auto, xbrl_numeric)

- Question: What did NVIDIA report as its net cash provided by operating activities for the first three quarters of fiscal 2024?
- Reference: $16,591 million for the nine months ended October 29, 2023.
- Answer:

```
# Answer

I cannot find the information about NVIDIA's net cash provided by operating activities for the first three quarters of fiscal 2024 in the provided SEC filing excerpts.

The excerpts you've shared contain information from NVIDIA's MD&A (Management's Discussion and Analysis) section and notes to financial statements, which discuss revenue, operating expenses, and segment performance for Q3 FY2024. However, **cash flow statement data is not included in these excerpts**.

To find NVIDIA's net cash provided by operating activities for the first nine months of fiscal 2024, you would need to:

1. Review the **Statement of Cash Flows** section of NVIDIA's 10-Q filing for Q3 FY2024 (filing 0001045810-23-000227)
2. Look for the line item "Net cash provided by operating activities" for the nine-month period ended October 30, 2023

If you can provide additional excerpts that include the cash flow statement from that filing, I'd be happy to help identify the specific figure.
```

## xbrl_0106 (xbrl_auto, xbrl_numeric)

- Question: Pfizer selling, general and administrative expense, fiscal 2023: what was the figure?
- Reference: $14,771 million for the fiscal year ended December 31, 2023.
- Answer:

```
# Pfizer Selling, General and Administrative Expense - Fiscal 2023

Based on the SEC filing excerpts provided, I can find the **nine-month figure** for 2023:

**Nine Months Ended October 1, 2023: $10,196 million**

However, the excerpts provided do not include Pfizer's complete **fiscal year 2023 10-K annual report**, which would contain the full-year figure for the period ending December 31, 2023. 

To obtain the complete fiscal 2023 selling, informational and administrative expense figure, you would need to consult Pfizer's **2023 10-K annual report**, which would show the full-year results including the fourth quarter (October-December 2023).
```

## xbrl_0111 (xbrl_auto, xbrl_numeric)

- Question: What did Pfizer report as its total stockholders' equity as of June 30, 2024?
- Reference: $87,700 million as of June 30, 2024.
- Answer:

```
# Pfizer Stockholders' Equity as of June 30, 2024

Based on Pfizer's Q3 FY2024 10-Q filing, **Pfizer reported total stockholders' equity of $87,700 million ($87.7 billion) as of June 30, 2024**.

This figure is shown in the Condensed Consolidated Statements of Equity, which breaks down the components as follows:
- Common stock par value: $480 million
- Additional paid-in capital: $93,197 million
- Treasury stock cost: $(114,757) million
- Retained earnings: $116,596 million
- Accumulated other comprehensive loss: $(7,816) million

**Total stockholders' equity: $87,700 million**

(Note: This does not include non-controlling interests of $275 million, which would bring total equity to $87,975 million.)
```

## xbrl_0118 (xbrl_auto, xbrl_numeric)

- Question: How much did Pfizer carry in total current assets at the end of fiscal 2023?
- Reference: $43,333 million as of December 31, 2023.
- Answer:

```
# Pfizer's Total Current Assets at End of Fiscal 2023

According to Pfizer's 10-K filing for fiscal year 2023, **total current assets as of December 31, 2023 were $43,333 million (or approximately $43.3 billion)**.

This breaks down as follows:
- Cash and cash equivalents: $2,853 million
- Short-term investments: $9,837 million
- Trade accounts receivable: $11,177 million
- Inventories: $10,189 million
- Current tax assets: $3,978 million
- Other current assets: $5,299 million

**Total: $43,333 million**
```

## xbrl_0120 (xbrl_auto, xbrl_numeric)

- Question: What was the balance of Pfizer's long-term debt, excluding the current portion on December 31, 2025?
- Reference: $61,641 million as of December 31, 2025.
- Answer:

```
# Pfizer's Long-Term Debt as of December 31, 2025

Based on Pfizer's FY2025 10-K filing, the balance of long-term debt, excluding the current portion, was:

**$61,293 million (principal amount)**

This figure represents the total senior unsecured long-term debt by maturity date, with the following composition:
- Notes due 2027-2065 ranging from $500 million to $11,000 million depending on maturity
- The Notes due 2026 ($6,000 million as of December 31, 2024) had matured and were paid off by year-end 2025

**If including fair value adjustments:**
- Add: Net fair value adjustments related to hedging and purchase accounting: **$834 million**
- **Total adjusted balance: $62,127 million**

The principal amount of $61,293 million represents the actual outstanding debt obligations, while the $62,127 million figure represents how the debt would be reported on the balance sheet with accounting adjustments for hedging activities and purchase accounting.
```

## xbrl_0125 (xbrl_auto, xbrl_numeric)

- Question: How much income before income taxes did Target report for the fiscal year ended January 31, 2026?
- Reference: $4,767 million for the fiscal year ended January 31, 2026.
- Answer:

```
# Answer

Based on the SEC filings provided, **Target reported earnings before income taxes of $4.8 billion for the fiscal year ended January 31, 2026** (fiscal year 2025).

This information is found in the Income Taxes note from Target's FY2025 10-K filing, which states: "Earnings before income taxes were $4.8 billion, $5.3 billion, and $5.3 billion during 2025, 2024, and 2023, respectively."
```

## xbrl_0138 (xbrl_auto, xbrl_numeric)

- Question: How much operating income did Target report for the fiscal year ended February 3, 2024?
- Reference: $5,707 million for the fiscal year ended February 3, 2024.
- Answer:

```
# Target Operating Income for Fiscal Year Ended February 3, 2024

Target reported **$5,707 million** in operating income for the fiscal year ended February 3, 2024.

This figure is found in Target's 10-K filing (FY2023) in the "After-Tax Return on Invested Capital" table within Management's Discussion and Analysis. This same figure is also confirmed as a comparative period in Target's subsequent FY2024 10-K filing.
```

## xbrl_0141 (xbrl_auto, xbrl_numeric)

- Question: How much net income did Exxon Mobil report for the six months ended June 30, 2024?
- Reference: $17,460 million for the six months ended June 30, 2024.
- Answer:

```
# Exxon Mobil Net Income for Six Months Ended June 30, 2024

According to Exxon Mobil's Q2 2024 10-Q filing (SEC filing 0000034088-24-000050), **net income attributable to ExxonMobil for the six months ended June 30, 2024 was $17,460 million** (or approximately $17.5 billion).

This figure comes from the Condensed Consolidated Statement of Income and is calculated as:
- Net income (including noncontrolling interests): $18,137 million
- Less: Net income attributable to noncontrolling interests: $677 million
- **Equals: Net income attributable to ExxonMobil: $17,460 million**

For comparison, net income for the same period in 2023 was $19,310 million, representing a decline year-over-year.
```

## xbrl_0149 (xbrl_auto, xbrl_numeric)

- Question: What did Exxon Mobil report as its total liabilities as of March 31, 2024?
- Reference: $164,866 million as of March 31, 2024.
- Answer:

```
# Answer

Based on the provided SEC filing excerpts, I cannot find Exxon Mobil's total liabilities as of March 31, 2024. 

The excerpts included focus on:
- Guarantees and obligations
- Segment earnings results
- Stock repurchase activity
- Chemical products performance

To find the total liabilities as of March 31, 2024, you would need to refer to Exxon Mobil's **Consolidated Balance Sheet** (typically found in Part I, Item 1: Financial Statements of the 10-Q filing). This information would show the company's total assets, total liabilities, and shareholders' equity as of that date.

If you have access to the complete Q1 2024 10-Q filing (SEC filing 0000034088-24-000029), please provide the balance sheet section, and I can extract the exact total liabilities figure for you.
```

## xbrl_0153 (xbrl_auto, xbrl_numeric)

- Question: What was the balance of Exxon Mobil's cash and cash equivalents on June 30, 2024?
- Reference: $26,460 million as of June 30, 2024.
- Answer:

```
# Exxon Mobil's Cash and Cash Equivalents on June 30, 2024

Based on Exxon Mobil Corporation's 10-Q filing for Q2 FY2024, the balance of **cash and cash equivalents on June 30, 2024 was $26,460 million** (or approximately **$26.5 billion**).

This information is found in the consolidated balance sheet in Part I, Item 1: Financial Statements of the Q2 FY2024 10-Q filing. The company also held an additional $28 million in restricted cash and cash equivalents as of that date.

For comparison, this represented a decrease from the December 31, 2023 balance of $31,539 million.
```
