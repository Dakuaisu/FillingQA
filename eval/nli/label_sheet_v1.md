# NLI gate label sheet v1 (PRD 7.5)

Run a4e39a65c2c8, seed 20261006, 40 pairs drawn from 95 prose (claim, cited chunk) pairs, stratified {'llm_seeded/other checks pass': 40, 'xbrl_auto/other checks pass': 0}. For each pair: does the chunk, on its own, support the claim? Label in labels_v1.yaml: true or false. No score is shown here.

## p01 (seed_0070 1, chunk 0000078003-24-000039:239.0:246.0)

**Claim:** Pfizer characterizes the trend in formulary placement of its branded products by managed care organizations as increasingly being placed on higher tiers or in non-preferred status.

**Chunk:**

```
[PFIZER INC (PFE) | 10-K | FY2023 | Item 1: BUSINESS]
The breadth of the products covered by formularies can vary considerably from one MCO to another, and many formularies include alternative and competitive products for treatment of particular medical problems. MCOs emphasize primary and preventive care, out-patient treatment and procedures performed at doctors’ offices and clinics as ways to manage costs. Hospitalization and surgery, typically the most expensive forms of treatment, are carefully managed, and drugs that can help in chronic care management and reduce the need for hospitalization, professional therapy or surgery may become favored first-line treatments for certain diseases. At the same time, MCOs may seek to exclude high-cost drugs from formularies in their efforts to manage and lower their costs.
Exclusion of a product from a formulary or other MCO-implemented restrictions can significantly impact drug usage in the MCO patient population and beyond. Consequently, pharmaceutical companies compete to gain access to formularies for their products, typically on the basis of unique product features, such as greater efficacy, better patient ease of use, or fewer side effects, as well as the overall cost of the therapy. We continue to seek to ensure that our major products are included on MCO formularies. However, our branded products are increasingly being placed on the higher tiers or in a non-preferred status. Continuing efforts by managed care entities to contain or reduce costs of healthcare and/or impose price controls may adversely affect demand for our products and our financial performance. See the Item 1A. Risk Factors—Managed Care Trends section.
RAW MATERIALS
We procure raw materials essential to our business from numerous suppliers worldwide. In general, these materials have been available in sufficient quantities to support our demand and in many cases are available from multiple suppliers. No significant impact to our operations due to the availability of raw materials is currently anticipated in 2024. However, we continue to see heightened demand in the industry for certain components and raw materials, which could potentially result in constraining available supply leading to a possible future impact on our business. We are continuing to monitor and implement mitigation strategies to reduce any potential risk or impact including active supplier management, qualification of additional suppliers and advanced purchasing to the extent possible.
GOVERNMENT REGULATION AND PRICE CONSTRAINTS
cannot be predicted with certainty, we do not currently anticipate they will have a material effect on our capital expenditures or competitive position.
```

## p02 (seed_0051 1, chunk 0000320193-26-000013:270.0:272.0)

**Claim:** Apple is currently subject to a court order in the U.S. preventing it from imposing any commission or fee on certain purchases that consumers make.

**Chunk:**

```
[Apple Inc. (AAPL) | 10-Q | Q2 FY2026 | Part II, Item 1A: Risk Factors]
While the Company maintains insurance coverage that is intended to address certain aspects of data security risks, such insurance coverage may be insufficient to cover all losses or all types of claims that may arise.
The technology industry, including, in some instances, the Company, is subject to intense media, political and regulatory scrutiny, which exposes the Company to increasing regulation, government investigations, legal actions and penalties.
From time to time, the Company has made changes to its business, including actions taken in response to litigation, competition, market conditions and legal and regulatory requirements. The Company expects to make further business changes in the future. For example, in the U.S., the Company has implemented changes to how developers communicate with consumers within apps on the U.S. storefront of the iOS and iPadOS® App Store regarding alternative purchasing mechanisms. The Company is also currently subject to a court order in the U.S. preventing it from imposing any commission or fee on certain purchases that consumers make. The Ninth Circuit Court has instructed the California District Court to further amend or modify its injunction to allow the Company to charge a commission. If the Company is ultimately unsuccessful in defending its commission structure or if similar restrictions are imposed or expanded in other jurisdictions, and as a result the Company’s commission is narrowed or eliminated, the Company’s business, results of operations, and financial condition could be materially and adversely affected.
```

## p03 (seed_0081 3, chunk 0000034088-23-000056:132.0:133.0)

**Claim:** Earnings excluding Identified Items is not meant to be viewed in isolation or as a substitute for net income (loss) attributable to ExxonMobil as prepared in accordance with U.S. GAAP.

**Chunk:**

```
[Exxon Mobil Corporation (XOM) | 10-Q | Q3 FY2023 | Part I, Item 2: MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS]
FUNCTIONAL EARNINGS SUMMARY
Earnings (loss) excluding Identified Items (non-GAAP) are earnings (loss) excluding individually significant non-operational events with, typically, an absolute corporate total earnings impact of at least $250 million in a given quarter. The earnings (loss) impact of an identified item for an individual segment may be less than $250 million when the item impacts several periods or several segments. Earnings (loss) excluding identified items does include non-operational earnings events or impacts that are generally below the $250 million threshold utilized for Identified Items. Management uses these figures to improve comparability of the underlying business across multiple periods by isolating and removing significant non-operational events from business results. The Corporation believes this view provides investors increased transparency into business results and trends and provides investors with a view of the business as seen through the eyes of management. Earnings (loss) excluding Identified Items is not meant to be viewed in isolation or as a substitute for net income (loss) attributable to ExxonMobil as prepared in accordance with U.S. GAAP.
```

## p04 (seed_0059 1, chunk 0000909832-23-000065:143.0:146.0)

**Claim:** In the Yesenia Murillo matter, Costco Wholesale Corporation is named as an alleged joint employer.

**Chunk:**

```
[COSTCO WHOLESALE CORP /NEW (COST) | 10-Q | Q1 FY2024 | Part I, Item 1: Financial Statements]
In September 2023, a former employee filed a class action against the Company alleging claims under California law for failure to pay minimum wage, to pay overtime, to provide meal and rest periods, to provide accurate wage statements, to timely pay final wages, to reimburse employee expenses, and for unfair business practices. Jordan Clower v. Costco Wholesale Corporation (Case No. 1:23-cv-01621). The Company has filed a motion to dismiss.
In November 2023, a former employee filed a class action against the Company alleging claims under California law for failure to pay minimum wage, failure to pay overtime, failure to provide meal and rest breaks, failure to provide accurate wage statements, failure to reimburse expenses, failure to pay wages when due, and failure to pay sick pay. Martin Reyes v. Costco Wholesale Corporation, Sacramento County Superior Court. (Case No. 23cv011351). The Company has not yet responded to the complaint.
In August 2023, a former employee of a third-party staffing company filed a letter with the California Labor and Workforce Development Agency threatening claims under the California Private Attorneys General Act for alleged Labor Code violations consisting of minimum wage and overtime violations, meal and rest period violations, wage statement violations and failure to pay all wages at termination. Yesenia Murillo v. Real Time Staffing Services, LLC and Costco Wholesale Corporation. The Company is named as an alleged joint employer. A complaint has not yet been filed.
In October 2023, current and former employees filed suit against the Company asserting collective and class claims on behalf of all “Junior Managers” under the Fair Labor Standards Act and New York Labor Law for failure to pay overtime compensation and for inaccurate wage notices and statements under New York law. Lock et al. v. Costco Wholesale Corp. (Case No. 2:23-cv-07904; E.D.N.Y.). The Company has not yet responded to the complaint.
```

## p05 (seed_0083 1, chunk 0000034088-26-000067:231.0:253.0)

**Claim:** Exxon Mobil Corporation identifies the ability to maintain near-term cost reductions as ongoing efficiencies without impairing competitive positioning as a risk factor in its Q1 FY2026 10-Q.

**Chunk:**

```
[Exxon Mobil Corporation (XOM) | 10-Q | Q1 FY2026 | Part I, Item 2: MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND]
regulatory incentives consistent with law; reservoir performance and optimization, including variability and timing factors
applicable to unconventional resources, the success of new unconventional technologies, and the ability of new technologies to
improve recovery relative to competitors; the level, outcome, and timing of exploration and development projects and decisions
to invest in future reserves and resources; timely completion of construction projects and commencement of start-up operations,
including reliance on third-party suppliers and service providers; final management approval of future projects and any changes
in the scope, terms, costs or assumptions of such projects as approved; the actions of governments, non-governmental
organizations, or other actors against our core business activities and acquisitions, divestitures or financing opportunities; war,
civil unrest, armed hostilities, attacks against the company or industry, and other geopolitical or security disturbances, including
disruption of land or sea transportation routes or distribution or shipping channels; decoupling of economies; disruption,
realignment, or breaking of current or historical trade or military alliances or global trade and supply chain networks; escalating
geopolitical volatility, including regime changes; expropriations, seizure, or capacity, insurance, shipping, import or export
limitations imposed directly or indirectly by governments or laws; opportunities for potential acquisitions, investments or
divestments and satisfaction of applicable conditions to closing, including timely regulatory approvals; the capture of
efficiencies within and between business lines and the ability to maintain near-term cost reductions as ongoing efficiencies
without impairing our competitive positioning; unforeseen technical or operating disruptions or difficulties and unplanned
maintenance; the development and competitiveness of alternative energy and emission reduction technologies; consumer
preferences including willingness and ability to pay for reduced emission products; the results of research programs and the
ability to bring new technologies to commercial scale on a cost-competitive basis; and other factors discussed under "Item 1A.
Risk Factors" of ExxonMobil’s 2025 Form 10-K.
Forward-looking and other statements regarding environmental and other sustainability efforts and aspirations are not an
indication that these statements are material to investors or require disclosure in our filing with the SEC or any other regulatory
```

## p06 (seed_0071 2, chunk 0000078003-24-000039:743.0:746.0)

**Claim:** These charges primarily represented product liability and other legal expenses related to products discontinued and/or divested by Pfizer.

**Chunk:**

```
[PFIZER INC (PFE) | 10-K | FY2023 | Item 7: MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS]
(h)For 2023, the total of $246 million includes charges of (i) $474 million for certain legal matters, primarily representing certain product liability and other legal expenses related to products discontinued and/or divested by Pfizer, and to a lesser extent, legal obligations related to pre-acquisition matters, and (ii) $127 million mostly related to our equity-method accounting pro-rata share of intangible asset amortization and impairments, costs of separating from GSK and restructuring costs recorded by Haleon, partially offset by: (i) a $222 million gain on the divestiture of our early-stage rare disease gene therapy portfolio to Alexion, and (ii) dividend income of $211 million related to our investment in Nimbus resulting from Takeda’s acquisition of Nimbus’s oral, selective allosteric tyrosine kinase 2 (TYK2) inhibitor program subsidiary. For 2022, the total of $636 million included charges of (i) $307 million mostly representing our equity-method accounting pro rata share of restructuring charges and costs of separating from GSK recorded by Haleon/the Consumer Healthcare JV, and adjustments to our equity-method basis differences which are also related to the separation of Haleon/the Consumer Healthcare JV from GSK, and (ii) $230 million for certain legal matters, primarily representing certain product liability and other legal expenses related to products discontinued and/or divested by Pfizer. For 2021, the total of $334 million included charges of (i) $185 million mostly representing our equity-method accounting pro rata share of restructuring charges and costs of separating from GSK recorded by the Consumer Healthcare JV, and (ii) $162 million for certain legal matters, primarily for certain product liability expenses related to products discontinued and/or divested by Pfizer, and to a lesser extent, legal obligations related to pre-acquisition matters.
(i)For 2021, the total of $141 million primarily included costs for consulting, legal, tax and advisory services associated with a non-recurring internal reorganization of legal entities.
ANALYSIS OF THE CONSOLIDATED STATEMENTS OF CASH FLOWS
```

## p07 (seed_0054 6, chunk 0000070858-25-000268:656.0:664.0)

**Claim:** The market multiplier approach utilized various market multiples, primarily pricing multiples, from comparable publicly-traded companies in industries similar to the reporting unit, with a control premium factored in based on observed comparable premiums for change-in-control transactions for financial institutions.

**Chunk:**

```
[Bank of America Corporation (BAC) | 10-Q | Q2 FY2025 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations]
We completed our annual goodwill impairment test as of June 30, 2025 using a quantitative assessment for the Consumer Banking reporting unit and a qualitative assessment for the remaining six reporting units. The quantitative assessment was performed for Consumer Banking because the Corporation combined its Consumer Lending and Deposits reporting units into a single reporting unit to correspond with the change in reporting structure that occurred in the Consumer Banking segment in the first quarter of 2025.
For the quantitative assessment, we compared the fair value of the reporting unit to its carrying value, as measured by allocated equity. The fair value was estimated based on the
combination of an income approach (which utilizes the present value of cash flows to estimate fair value) and a market multiplier approach (which utilizes observable market prices and metrics of peer companies to estimate fair value). The cash flows used in the income approach were based on the Corporation’s three-year internal forecasts along with long-term terminal growth values, which were discounted at 10.50 percent. The discount rate was derived from a capital asset pricing model that incorporates the risk and uncertainty in the cash flow forecasts, the financial markets and industries similar to the reporting units. The market multiplier approach utilized various market multiples, primarily pricing multiples, from comparable publicly-traded companies in industries similar to
the reporting unit. In addition, a control premium was factored in based upon observed comparable premiums paid for change-in-control transactions for financial institutions.
For the qualitative assessment, we used various factors, including macroeconomic conditions and outlook, industry and market pricing multiples, financial performance and other relevant reporting unit considerations, to support that it is not more likely than not that the fair value of the reporting units is less than the reporting units’ carrying value.
Based on our assessments, we have concluded that none of our reporting units are at risk of impairment, as each of the reporting units’ fair values are substantially in excess of their carrying values.
Non-GAAP Reconciliations
Table 43 provides reconciliations of certain non-GAAP financial measures to the most directly comparable GAAP financial measures.
```

## p08 (seed_0075 1, chunk 0000027419-24-000032:392.0:395.0)

**Claim:** Management characterizes the risk of inaccurate self-insurance liability estimates by stating that liabilities could be significantly affected if future occurrences or loss developments differ from the assumptions used in their estimates.

**Chunk:**

```
[TARGET CORPORATION (TGT) | 10-K | FY2023 | Item 7: Management's Discussion and Analysis of Financial Condition and Results of Operations]
Insurance/self-insurance: We retain a substantial portion of the risk related to certain general liability, workers' compensation, property loss, and team member medical and dental claims. However, we maintain stop-loss coverage to limit the exposure related to certain risks. Liabilities associated with these losses include estimates of both claims filed and losses incurred but not yet reported. We use actuarial methods which consider a number of factors to estimate our ultimate cost of losses. General liability and workers' compensation liabilities are recorded based on our estimate of their net present value; other liabilities referred to above are not discounted. Our workers' compensation and general liability accrual was $650 million and $560 million as of February 3, 2024, and January 28, 2023, respectively. We believe that the amounts accrued are appropriate; however, our liabilities could be significantly affected if future occurrences or loss developments differ from our assumptions. For example, a 5 percent increase or decrease in average claim costs would have impacted our self-insurance expense by $33 million in 2023. Historically, adjustments to our estimates have not been material. Refer to Part II, Item 7A, Quantitative and Qualitative Disclosures About Market Risk, for further disclosure of the market risks associated with these exposures. We maintain insurance coverage to limit our exposure to certain events, including network security matters.
Income taxes: We pay income taxes based on the tax statutes, regulations, and case law of the various jurisdictions in which we operate. Significant judgment is required in determining the timing and amounts of deductible and taxable items, and in evaluating the ultimate resolution of tax matters in dispute with tax authorities. The benefits of uncertain tax positions are recorded in our financial statements only after determining it is likely the uncertain tax positions would withstand challenge by taxing authorities. We periodically reassess these probabilities and record any changes in the financial statements as appropriate. Gross uncertain tax positions, including interest and penalties, were $366 million and $241 million as of February 3, 2024, and January 28, 2023, respectively. We believe the resolution of these matters will not materially affect our consolidated financial statements. Income taxes are described further in Note 19 to the Financial Statements.
```

## p09 (seed_0056 2, chunk 0000070858-25-000200:433.0:438.0)

**Claim:** The deterioration in commercial credit quality was primarily driven by commercial real estate due to the sustained high interest rate environment.

**Chunk:**

```
[Bank of America Corporation (BAC) | 10-Q | Q1 FY2025 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations]
For more information on our accounting policies regarding delinquencies, nonperforming status and net charge-offs, see Note 1 – Summary of Significant Accounting Principles to the Consolidated Financial Statements of the Corporation’s 2024 Annual Report on Form 10-K and Note 5 – Outstanding Loans and Leases and Allowance for Credit Losses to the Consolidated Financial Statements.
Commercial Credit Portfolio
Outstanding commercial loans and leases increased $11.8 billion during the three months ended March 31, 2025 due to growth in U.S. and non-U.S. commercial, primarily in Global Markets and Global Banking. During the three months ended March 31, 2025, commercial credit quality deteriorated as reservable criticized utilized exposure increased primarily driven by commercial real estate due to the sustained high interest rate environment. Nonperforming commercial loans increased $142 million during the three months ended March 31, 2025, primarily in non-U.S. commercial and commercial real estate. Commercial net charge-offs decreased $137 million compared
to the same period in 2024 primarily due to lower charge-offs in the commercial real estate office portfolio.
With the exception of the office property type, which is further discussed in the Commercial Real Estate section herein, credit quality of commercial borrowers has remained relatively stable since December 31, 2024; however, we are closely monitoring emerging trends, including ongoing negotiations regarding international trade policies, as well as borrower performance in the current environment. Recent demand for office space continues to be stagnant, and future demand for office space continues to be uncertain as companies evaluate space needs with employment models that utilize a mix of remote and conventional office use.
The commercial allowance for loan and lease losses of $4.7 billion remained relatively unchanged during the three months ended March 31, 2025. For more information, see Allowance for Credit Losses on page 36.
```

## p10 (seed_0072 1, chunk 0000078003-26-000026:511.0:512.0)

**Claim:** Pfizer characterizes patent litigation settlements and judgments as potentially having a material adverse effect on its revenues.

**Chunk:**

```
[PFIZER INC (PFE) | 10-K | FY2025 | Item 7: MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS]
Intellectual Property Rights and Collaboration/Licensing Rights––The loss, expiration or invalidation of intellectual property rights, patent litigation settlements and judgments, and the expiration of co-promotion and licensing rights can have a material adverse effect on our revenues. Certain of our products have experienced patent-based expirations or loss of regulatory exclusivity in certain markets in the last few years, and we expect certain products to face new or increased generic competition over the next few years. We anticipate a significant reduction of revenue from patent-based or regulatory exclusivity expiries in 2026 through 2030 as several of our in-line products experience these expirations, with the rate of the reduction of revenues from patent-based or regulatory exclusivity expiries expected to significantly accelerate over the next few years. In 2026, the impact from patent-based or regulatory exclusivity expiries is expected to be $1.5 billion. We continue to vigorously defend our patent rights against infringement, and we will continue to support efforts that strengthen worldwide recognition of patent rights while taking necessary steps to help ensure appropriate patient access.
For additional information on patent rights we consider most significant to our business as a whole, including U.S., major Europe and Japan basic product patent expiration years, see the Item 1. Business––Patents and Other Intellectual Property Rights section. For a discussion of recent developments with respect to patent litigation involving certain of our products, see Note 16A1.
```

## p11 (seed_0079 2, chunk 0000034088-23-000056:75.0:77.0)

**Claim:** The company identifies specific examples of political and regulatory impacts, including forced divestiture of assets, restrictions on production, imports and exports, price controls, tax increases and retroactive tax claims, expropriation of property, cancellation of contract rights, sanctions and environmental regulations.

**Chunk:**

```
[Exxon Mobil Corporation (XOM) | 10-Q | Q3 FY2023 | Part I, Item 1: FINANCIAL STATEMENTS]
The operations and earnings of the Corporation and its affiliates throughout the world have been, and may in the future be, affected from time to time in varying degree by political developments and laws and regulations, such as forced divestiture of assets; restrictions on production, imports and exports; price controls; tax increases and retroactive tax claims; expropriation of property; cancellation of contract rights; sanctions and environmental regulations. Both the likelihood of such occurrences and their overall effect upon the Corporation vary greatly from country to country and are not predictable.
Note 4. Other Comprehensive Income Information
```

## p12 (seed_0081 1, chunk 0000034088-23-000056:132.0:133.0)

**Claim:** Management uses earnings excluding Identified Items to improve comparability of the underlying business across multiple periods by isolating and removing significant non-operational events from business results.

**Chunk:**

```
[Exxon Mobil Corporation (XOM) | 10-Q | Q3 FY2023 | Part I, Item 2: MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS]
FUNCTIONAL EARNINGS SUMMARY
Earnings (loss) excluding Identified Items (non-GAAP) are earnings (loss) excluding individually significant non-operational events with, typically, an absolute corporate total earnings impact of at least $250 million in a given quarter. The earnings (loss) impact of an identified item for an individual segment may be less than $250 million when the item impacts several periods or several segments. Earnings (loss) excluding identified items does include non-operational earnings events or impacts that are generally below the $250 million threshold utilized for Identified Items. Management uses these figures to improve comparability of the underlying business across multiple periods by isolating and removing significant non-operational events from business results. The Corporation believes this view provides investors increased transparency into business results and trends and provides investors with a view of the business as seen through the eyes of management. Earnings (loss) excluding Identified Items is not meant to be viewed in isolation or as a substitute for net income (loss) attributable to ExxonMobil as prepared in accordance with U.S. GAAP.
```

## p13 (seed_0073 4, chunk 0000078003-26-000095:150.0:154.0)

**Claim:** The dividend income was recorded in Other (income)/deductions—net.

**Chunk:**

```
[PFIZER INC (PFE) | 10-Q | Q2 FY2026 | Part I, Item 1: FINANCIAL STATEMENTS]
(a)The amounts for the second quarter and first six months of 2026 and 2025 primarily include certain product liability and other legal expenses.
(b)The amounts for the second quarter and first six months of 2026 represent intangible asset impairment charges associated with our Biopharma segment, composed of: (i) $3.8 billion in impairments of IPR&D assets, associated with a Phase 3 study for sigvotatug vedotin for the second line treatment of metastatic non-squamous NSCLC, reflecting unfavorable clinical trial results, and (ii) $525 million for Oxbryta (voxelotor) developed technology rights, after engaging with the FDA in July 2026 to discuss their assessment of data and analyses, and it was determined there was no viable pathway to return Oxbryta to the market in the U.S. The amount for the first six months of 2025 primarily included an intangible asset impairment charge associated with our Biopharma segment of $210 million for a Phase 2 indefinite-lived out-licensed asset that was discontinued by our out-licensing partner.
(c)See Note 2C.
(d)See Notes 1D and 16D in our 2025 Form 10-K and Note 7A.
(e)The amounts for the second quarter and first six months of 2026 include, among other things, dividend income of $98 million and $180 million, respectively, from our previous investment in ViiV. The amounts for the second quarter and first six months of 2025 included, among other things, dividend income of $73 million and $111 million, respectively, from our previous investment in ViiV.
```

## p14 (seed_0049 1, chunk 0000320193-24-000069:105.0:112.0)

**Claim:** As of March 30, 2024, two vendors each individually represented 10% or more of total vendor non-trade receivables, accounting for 47% and 19%.

**Chunk:**

```
[Apple Inc. (AAPL) | 10-Q | Q2 FY2024 | Part I, Item 1: Financial Statements]
Accounts Receivable
Trade Receivables
The Company’s third-party cellular network carriers accounted for 34% and 41% of total trade receivables as of March 30, 2024 and September 30, 2023, respectively. The Company requires third-party credit support or collateral from certain customers to limit credit risk.
Vendor Non-Trade Receivables
The Company has non-trade receivables from certain of its manufacturing vendors resulting from the sale of components to these vendors who manufacture subassemblies or assemble final products for the Company. The Company purchases these components directly from suppliers. The Company does not reflect the sale of these components in products net sales. Rather, the Company recognizes any gain on these sales as a reduction of products cost of sales when the related final products are sold by the Company. As of March 30, 2024, the Company had two vendors that individually represented 10% or more of total vendor non-trade receivables, which accounted for 47% and 19%. As of September 30, 2023, the Company had two vendors that individually represented 10% or more of total vendor non-trade receivables, which accounted for 48% and 23%.
Note 5 – Condensed Consolidated Financial Statement Details
The following table shows the Company’s condensed consolidated financial statement details as of March 30, 2024 and September 30, 2023 (in millions):
Property, Plant and Equipment, Net
```

## p15 (seed_0052 claim_1, chunk 0000070858-24-000122:1193.0:1195.0)

**Claim:** Bank of America applies less reliance to broker quotes in less active markets because such quotes may only be indicative and therefore are less reliable than more directly observable market data.

**Chunk:**

```
[Bank of America Corporation (BAC) | 10-K | FY2023 | Item 7: Bank of America Corporation and Subsidiaries Management's Discussion and Analysis of Financial Condition and Results of Operations Table of Contents]
volatility, lessened liquidity or in illiquid markets, there may be more variability in market pricing or a lack of market data to use in the valuation process. In keeping with the prudent application of estimates and management judgment in determining the fair value of assets and liabilities, we have in place various processes and controls that include: a model validation policy that requires review and approval of quantitative models used for deal pricing, financial statement fair value determination and risk quantification; a trading product valuation policy that requires verification of all traded product valuations; and a periodic review and substantiation of daily profit and loss reporting for all traded products. Primarily through validation controls, we utilize both broker and pricing service inputs which can and do include both market-observable and internally-modeled values and/or valuation inputs. Our reliance on this information is affected by our understanding of how the broker and/or pricing service develops its data with a higher degree of reliance applied to those that are more directly observable and lesser reliance applied to those developed through their own internal modeling. For example, broker quotes in less active markets may only be indicative and therefore less reliable. These processes and controls are performed independently of the business. For more information, see Note 20 – Fair Value Measurements and Note 21 – Fair Value Option to the Consolidated Financial Statements.
Level 3 Assets and Liabilities
Financial assets and liabilities, and MSRs, where values are based on valuation techniques that require inputs that are both unobservable and are significant to the overall fair value measurement are classified as Level 3 under the fair value hierarchy established in applicable accounting standards. The fair value of these Level 3 financial assets and liabilities and MSRs is determined using pricing models, discounted cash flow methodologies or similar techniques for which the determination of fair value requires significant management judgment or estimation.
```

## p16 (seed_0048 2, chunk 0000320193-25-000079:478.0:485.0)

**Claim:** These deferred gains and losses from cash flow hedges are subsequently reclassified into earnings when the hedged transaction affects earnings.

**Chunk:**

```
[Apple Inc. (AAPL) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data]
All derivative instruments are recorded in the Consolidated Balance Sheets at fair value. The accounting treatment for derivative gains and losses is based on intended use and hedge designation.
Gains and losses arising from amounts that are included in the assessment of cash flow hedge effectiveness are initially deferred in accumulated other comprehensive income/(loss) and subsequently reclassified into earnings when the hedged transaction affects earnings, and in the same line item in the Consolidated Statements of Operations. Gains and losses arising from amounts that are included in the assessment of fair value hedge effectiveness are recognized in the Consolidated Statements of Operations line item to which the hedge relates along with offsetting losses and gains related to the change in value of the hedged item.
For derivative instruments designated as cash flow and fair value hedges, amounts excluded from the assessment of hedge effectiveness are recognized on a straight-line basis over the life of the hedge in the Consolidated Statements of Operations line item to which the hedge relates. Changes in the fair value of amounts excluded from the assessment of hedge effectiveness are recognized in other comprehensive income/(loss).
Gains and losses arising from changes in the fair values of derivative instruments that are not designated as accounting hedges are recognized in the Consolidated Statements of Operations.
The Company classifies cash flows related to derivative instruments in the same section of the Consolidated Statements of Cash Flows as the items being hedged, which are generally classified as operating activities.
Foreign Exchange Rate Risk
To protect gross margins from fluctuations in foreign exchange rates, the Company may use forwards, options or other instruments, and may designate these instruments as cash flow hedges. The Company generally hedges portions of its forecasted foreign currency exposure associated with revenue and inventory purchases, typically for up to 12 months.
To protect the Company’s foreign currency–denominated term debt or marketable securities from fluctuations in foreign exchange rates, the Company may use forwards, cross-currency swaps or other instruments. The Company designates these instruments as either cash flow or fair value hedges. As of September 27, 2025, the maximum length of time over which the Company is hedging its exposure to the variability in future cash flows for term debt–related foreign currency transactions is 17 years.
```

## p17 (seed_0056 4, chunk 0000070858-25-000200:433.0:438.0)

**Claim:** With the exception of the office property type, credit quality of commercial borrowers remained relatively stable since December 31, 2024.

**Chunk:**

```
[Bank of America Corporation (BAC) | 10-Q | Q1 FY2025 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations]
For more information on our accounting policies regarding delinquencies, nonperforming status and net charge-offs, see Note 1 – Summary of Significant Accounting Principles to the Consolidated Financial Statements of the Corporation’s 2024 Annual Report on Form 10-K and Note 5 – Outstanding Loans and Leases and Allowance for Credit Losses to the Consolidated Financial Statements.
Commercial Credit Portfolio
Outstanding commercial loans and leases increased $11.8 billion during the three months ended March 31, 2025 due to growth in U.S. and non-U.S. commercial, primarily in Global Markets and Global Banking. During the three months ended March 31, 2025, commercial credit quality deteriorated as reservable criticized utilized exposure increased primarily driven by commercial real estate due to the sustained high interest rate environment. Nonperforming commercial loans increased $142 million during the three months ended March 31, 2025, primarily in non-U.S. commercial and commercial real estate. Commercial net charge-offs decreased $137 million compared
to the same period in 2024 primarily due to lower charge-offs in the commercial real estate office portfolio.
With the exception of the office property type, which is further discussed in the Commercial Real Estate section herein, credit quality of commercial borrowers has remained relatively stable since December 31, 2024; however, we are closely monitoring emerging trends, including ongoing negotiations regarding international trade policies, as well as borrower performance in the current environment. Recent demand for office space continues to be stagnant, and future demand for office space continues to be uncertain as companies evaluate space needs with employment models that utilize a mix of remote and conventional office use.
The commercial allowance for loan and lease losses of $4.7 billion remained relatively unchanged during the three months ended March 31, 2025. For more information, see Allowance for Credit Losses on page 36.
```

## p18 (seed_0053 1, chunk 0000070858-24-000122:1445.0:1453.0)

**Claim:** The Corporation enters into International Swaps and Derivatives Association, Inc. (ISDA) master netting agreements or similar agreements with substantially all of the Corporation's derivative counterparties.

**Chunk:**

```
[Bank of America Corporation (BAC) | 10-K | FY2023 | Item 8: Financial Statements and Supplementary Data Table of Contents]
(1)Represents the total contract/notional amount of derivative assets and liabilities outstanding.
(2)Includes certain out-of-the-money purchased options that have a liability amount primarily due to the deferral of option premiums to the end of the contract.
(3)Includes certain out-of-the-money written options that have an asset amount primarily due to the deferral of option premiums to the end of the contract.
(4)The net derivative asset (liability) and notional amount of written credit derivatives for which the Corporation held purchased credit derivatives with identical underlying referenced names were $(1.2) billion and $276.9 billion at December 31, 2022.
Offsetting of Derivatives
The Corporation enters into International Swaps and Derivatives Association, Inc. (ISDA) master netting agreements or similar agreements with substantially all of the Corporation’s derivative counterparties. Where legally enforceable, these master netting agreements give the Corporation, in the event of default by the counterparty, the right to liquidate securities held as collateral and to offset receivables and payables with the same counterparty. For purposes of the Consolidated Balance Sheet, the Corporation offsets derivative assets and liabilities and cash collateral held with the same counterparty where it has such a legally enforceable master netting agreement.
The following table presents derivative instruments included in derivative assets and liabilities on the Consolidated Balance
Sheet at December 31, 2023 and 2022 by primary risk (e.g., interest rate risk) and the platform, where applicable, on which these derivatives are transacted. Balances are presented on a gross basis, prior to the application of counterparty and cash collateral netting. Total gross derivative assets and liabilities are adjusted on an aggregate basis to take into consideration the effects of legally enforceable master netting agreements, which include reducing the balance for counterparty netting and cash collateral received or paid.
For more information on offsetting of securities financing agreements, see Note 10 – Securities Financing Agreements, Short-term Borrowings, Collateral and Restricted Cash.
```

## p19 (seed_0083 3, chunk 0000034088-26-000067:231.0:253.0)

**Claim:** These cautionary statements suggest the company recognizes a significant risk that its cost reductions may not prove to be sustainable over time and that maintaining them could potentially compromise competitive positioning.

**Chunk:**

```
[Exxon Mobil Corporation (XOM) | 10-Q | Q1 FY2026 | Part I, Item 2: MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND]
regulatory incentives consistent with law; reservoir performance and optimization, including variability and timing factors
applicable to unconventional resources, the success of new unconventional technologies, and the ability of new technologies to
improve recovery relative to competitors; the level, outcome, and timing of exploration and development projects and decisions
to invest in future reserves and resources; timely completion of construction projects and commencement of start-up operations,
including reliance on third-party suppliers and service providers; final management approval of future projects and any changes
in the scope, terms, costs or assumptions of such projects as approved; the actions of governments, non-governmental
organizations, or other actors against our core business activities and acquisitions, divestitures or financing opportunities; war,
civil unrest, armed hostilities, attacks against the company or industry, and other geopolitical or security disturbances, including
disruption of land or sea transportation routes or distribution or shipping channels; decoupling of economies; disruption,
realignment, or breaking of current or historical trade or military alliances or global trade and supply chain networks; escalating
geopolitical volatility, including regime changes; expropriations, seizure, or capacity, insurance, shipping, import or export
limitations imposed directly or indirectly by governments or laws; opportunities for potential acquisitions, investments or
divestments and satisfaction of applicable conditions to closing, including timely regulatory approvals; the capture of
efficiencies within and between business lines and the ability to maintain near-term cost reductions as ongoing efficiencies
without impairing our competitive positioning; unforeseen technical or operating disruptions or difficulties and unplanned
maintenance; the development and competitiveness of alternative energy and emission reduction technologies; consumer
preferences including willingness and ability to pay for reduced emission products; the results of research programs and the
ability to bring new technologies to commercial scale on a cost-competitive basis; and other factors discussed under "Item 1A.
Risk Factors" of ExxonMobil’s 2025 Form 10-K.
Forward-looking and other statements regarding environmental and other sustainability efforts and aspirations are not an
indication that these statements are material to investors or require disclosure in our filing with the SEC or any other regulatory
```

## p20 (seed_0058 1, chunk 0000909832-24-000049:704.0:704.0)

**Claim:** Costco Wholesale Corp is a named defendant in the Wei and Henry bodily injury actions related to Real Water.

**Chunk:**

```
[COSTCO WHOLESALE CORP /NEW (COST) | 10-K | FY2024 | Item 8: Financial Statements and Supplementary Data]
The Company is a named defendant in four bodily injury actions relating to its sale of Real Water, an alkalized water previously sold at the Company and other retailers. Kaveh et al. v. Costco Wholesale Corp. et al., Case No. A23-864391-B, District Court, Clark County, NV Wei, et al. v. Costco Wholesale Corp. et al. Case No. A-22-856147-B, District Court, Clark County, NV Henry et al. v. Costco Wholesale Corp. et al., Case No. A21844176-B, District Court, Clark County, NV Lampman et al. vs. Costco Wholesale Corp. et al. Case No. A-23-868638-C, District Court, Clark County, NV. The plaintiffs allegedly sustained liver or other bodily damage as a result of consuming the product, and seek compensatory and punitive damages from all defendants, which include the manufacturer, distributors, testing equipment makers and retailers. The Kaveh case is set for trial on March 17, 2025. Wei and Henry have been consolidated with Brown. et al., vs. AffinityLifestyles.com, Inc., et al., Case No. A-21-831776-B, District Court, Clark County, NV. The Company is not a named defendant in Brown. Wei/Henry/Brown is set for trial starting October 7, 2024.
```

## p21 (seed_0068 3, chunk 0001045810-25-000230:354.0:360.0)

**Claim:** One AI research and deployment company contributed a meaningful amount of NVIDIA's revenue through cloud services purchases from NVIDIA's customers in the third quarter of fiscal year 2026.

**Chunk:**

```
[NVIDIA CORP (NVDA) | 10-Q | Q3 FY2026 | Part I, Item 2: Management's Discussion and Analysis of Financial Condition and Results of Operations]
Direct Customers – For the third quarter of fiscal year 2026, four direct customers with sales greater than 10% of total revenue included: Customer A at 22%, Customer B at 15%, Customer C at 13%, and Customer D at 11%, which were attributable to the Compute & Networking segment. For the first nine months of fiscal year 2026, sales to two direct customers represented 21% and 13% of total revenue, respectively, both of which were attributable to the Compute & Networking segment. The customers referenced above may represent different customers than those reported in a previous period.
For the third quarter of fiscal year 2025, sales to three direct customers each represented 12% of total revenue, which were attributable to the Compute & Networking segment. For the first nine months of fiscal year 2025, sales to three direct customers represented 12%, 11%, and 11% of total revenue, which were attributable to the Compute & Networking segment.
Indirect Customers – Indirect customer revenue is an estimation based upon multiple factors including customer purchase order information, product specifications, internal sales data, and other sources. Indirect customers primarily purchase our products through system integrators and distributors.
We generate a significant amount of our revenue from a limited number of indirect customers, some individually representing 10% or more of our revenue. Certain companies purchase cloud and related services through various direct and indirect customers. We estimate that one AI research and deployment company contributed to a meaningful amount of our revenue purchasing cloud services from our customers in the third quarter of fiscal year 2026. Our revenue is concentrated among a limited number of direct, indirect and cloud service purchasers and this trend may continue.
Revenue by geographic region is designated based on the location of the customers' headquarters of direct customers even if the estimated revenue may be attributable to indirect customers in a different location. Revenue from sales to customers headquartered outside of the United States accounted for 31% and 34% of total revenue for the third quarter and first nine months of fiscal year 2026, respectively, and 44% and 41% of total revenue for the third quarter and first nine months of fiscal year 2025, respectively.
Gross Profit and Gross Margin
```

## p22 (seed_0066 2, chunk 0001045810-25-000023:1199.0:1205.0)

**Claim:** The certifications will not be deemed 'filed' for purposes of Section 18 of the Exchange Act.

**Chunk:**

```
[NVIDIA CORP (NVDA) | 10-K | FY2025 | Item 15: Exhibits and Financial Statement Schedules]
* Filed herewith.
+ Management contract or compensatory plan or arrangement.
# In accordance with Item 601(b)(32)(ii) of Regulation S-K and SEC Release Nos. 33-8238 and 34-47986, Final Rule: Management's Reports on Internal Control Over Financial Reporting and Certification of Disclosure in Exchange Act Periodic Reports, the certifications furnished in Exhibits 32.1 and 32.2 hereto are deemed to accompany this Annual Report on Form 10-K and will not be deemed “filed” for purpose of Section 18 of the Exchange Act. Such certifications will not be deemed to be incorporated by reference into any filing under the Securities Act or the Exchange Act, except to the extent that the registrant specifically incorporates it by reference.
^ Certain exhibits and schedules have been omitted in accordance with Regulation S-K Item 601(a)(5).
Copies of above exhibits not contained herein are available to any shareholder upon written request to:
Investor Relations: NVIDIA Corporation, 2788 San Tomas Expressway, Santa Clara, CA 95051
```

## p23 (seed_0063 2, chunk 0001628280-25-048859:1284.0:1301.0)

**Claim:** The transfers occurred as a result of an increase in observability and a decrease in the significance of unobservable inputs.

**Chunk:**

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2025 | Part I, Item 1: Financial Statements]
(g)Loan originations are included in purchases.
(h)Includes financial assets and liabilities that have matured, been partially or fully repaid, impacts of modifications, deconsolidations associated with beneficial interests in VIEs and other items.
Level 3 analysis
Consolidated balance sheets changes
The following describes significant changes to level 3 assets since December 31, 2024, for those items measured at fair value on a recurring basis. Refer to Assets and liabilities measured at fair value on a nonrecurring basis on page 110 for further information on changes impacting items measured at fair value on a nonrecurring basis.
Three and nine months ended September 30, 2025
Level 3 assets were $25.4 billion at September 30, 2025, reflecting a decrease of $53 million from June 30, 2025, and an increase of $1.7 billion from December 31, 2024.
The increase for the nine months ended September 30, 2025 was predominantly driven by higher:
•Other trading assets of $301 million due to gains and purchases.
•Gross derivative receivables of $1.2 billion due to gains and purchases primarily offset by settlements and net transfers.
Refer to the sections below for additional information.
Transfers between levels for instruments carried at fair value on a recurring basis
For the three months ended September 30, 2025 and 2024, there were no significant transfers from level 2 into level 3.
For the three months ended September 30, 2025, significant transfers from level 3 into level 2 included the following:
•$914 million and $1.2 billion of gross equity derivative receivables and gross equity derivative payables, respectively, as a result of an increase in observability and a decrease in the significance of unobservable inputs.
For the three months ended September 30, 2024, there were no significant transfers from level 3 into level 2.
For the nine months ended September 30, 2025, significant transfers from level 2 into level 3 included the following:
•$1.1 billion and $1.2 billion of gross equity derivative receivables and gross equity derivative payables, respectively, as a result of a decrease in observability and an increase in the significance of unobservable inputs.
```

## p24 (seed_0055 3, chunk 0000070858-25-000405:253.0:260.0)

**Claim:** The decline in return on average allocated capital occurred due to an increase in allocated capital, which was only partially offset by the higher net income.

**Chunk:**

```
[Bank of America Corporation (BAC) | 10-Q | Q3 FY2025 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations]
Global Markets offers sales and trading services and research services to institutional clients across fixed-income, credit, currency, commodity and equity businesses. Global Markets product coverage includes securities and derivative products in both the primary and secondary markets. For more information about Global Markets, see Business Segment Operations in the MD&A of the Corporation’s 2024 Annual Report on Form 10-K.
The following explanations for period-over-period changes in results for Global Markets, including those disclosed under Sales and Trading Revenue, are the same for amounts including and excluding net DVA. Amounts excluding net DVA are a non-GAAP financial measure. For more information on net DVA, see Supplemental Financial Data on page 7.
Net income for Global Markets increased $99 million to $1.6 billion for the three months ended September 30, 2025 compared to the same period in 2024. Net DVA gains totaled $14 million compared to losses of $8 million in 2024. Excluding net DVA, net income increased $82 million to $1.6 billion. These increases were primarily driven by higher revenue, partially offset by higher noninterest expense.
Revenue increased $594 million to $6.2 billion primarily due to higher sales and trading revenue and investment banking fees. Sales and trading revenue increased $431 million, and excluding net DVA, increased $409 million. These increases were primarily driven by higher revenue in Equities and FICC. For more information, see Sales and Trading Revenue in this section.
Noninterest expense increased $452 million to $3.9 billion primarily driven by higher revenue-related expenses and continued investments in the business, including people and technology.
Average total assets increased $100.3 billion to $1.0 trillion for the three months ended September 30, 2025 compared to the same period in 2024 driven by loan growth, higher levels of inventory and increased financing activity.
The return on average allocated capital was 13 percent, down from 14 percent in the same period a year ago, due to an increase in allocated capital, partially offset by higher net income. For information on capital allocated to the business segments, see Business Segment Operations on page 11.
```

## p25 (seed_0048 1, chunk 0000320193-25-000079:478.0:485.0)

**Claim:** Gains and losses arising from amounts included in the assessment of cash flow hedge effectiveness are initially deferred in accumulated other comprehensive income/(loss).

**Chunk:**

```
[Apple Inc. (AAPL) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data]
All derivative instruments are recorded in the Consolidated Balance Sheets at fair value. The accounting treatment for derivative gains and losses is based on intended use and hedge designation.
Gains and losses arising from amounts that are included in the assessment of cash flow hedge effectiveness are initially deferred in accumulated other comprehensive income/(loss) and subsequently reclassified into earnings when the hedged transaction affects earnings, and in the same line item in the Consolidated Statements of Operations. Gains and losses arising from amounts that are included in the assessment of fair value hedge effectiveness are recognized in the Consolidated Statements of Operations line item to which the hedge relates along with offsetting losses and gains related to the change in value of the hedged item.
For derivative instruments designated as cash flow and fair value hedges, amounts excluded from the assessment of hedge effectiveness are recognized on a straight-line basis over the life of the hedge in the Consolidated Statements of Operations line item to which the hedge relates. Changes in the fair value of amounts excluded from the assessment of hedge effectiveness are recognized in other comprehensive income/(loss).
Gains and losses arising from changes in the fair values of derivative instruments that are not designated as accounting hedges are recognized in the Consolidated Statements of Operations.
The Company classifies cash flows related to derivative instruments in the same section of the Consolidated Statements of Cash Flows as the items being hedged, which are generally classified as operating activities.
Foreign Exchange Rate Risk
To protect gross margins from fluctuations in foreign exchange rates, the Company may use forwards, options or other instruments, and may designate these instruments as cash flow hedges. The Company generally hedges portions of its forecasted foreign currency exposure associated with revenue and inventory purchases, typically for up to 12 months.
To protect the Company’s foreign currency–denominated term debt or marketable securities from fluctuations in foreign exchange rates, the Company may use forwards, cross-currency swaps or other instruments. The Company designates these instruments as either cash flow or fair value hedges. As of September 27, 2025, the maximum length of time over which the Company is hedging its exposure to the variability in future cash flows for term debt–related foreign currency transactions is 17 years.
```

## p26 (seed_0076 4, chunk 0000027419-25-000018:704.0:708.0)

**Claim:** The statement that accumulated benefit obligation (which excludes assumed future salary growth) is materially consistent with the projected benefit obligation suggests that the effect of assumed future salary growth on the plan's obligations is immaterial, despite the 3.00% compensation increase assumption.

**Chunk:**

```
[TARGET CORPORATION (TGT) | 10-K | FY2024 | Item 8: Financial Statements and Supplementary Data]
(a)The actuarial gain was primarily driven by changes in the weighted average discount rate.
(b)Accumulated benefit obligation—the present value of benefits earned to date assuming no future salary growth—is materially consistent with the projected benefit obligation in each period presented.
Plan Assets
```

## p27 (seed_0054 2, chunk 0000070858-25-000268:991.0:993.0)

**Claim:** The Corporation concluded that none of its reporting units are at risk of impairment.

**Chunk:**

```
[Bank of America Corporation (BAC) | 10-Q | Q2 FY2025 | Part I, Item 1: Financial Statements]
NOTE 7 Goodwill and Intangible Assets
Goodwill
The table below presents goodwill balances by business segment at June 30, 2025 and December 31, 2024. The reporting units utilized for goodwill impairment testing are the operating segments or one level below. The Corporation completed its annual goodwill impairment test as of June 30, 2025 by using a quantitative assessment for the Consumer Banking reporting unit and a qualitative assessment for the remaining six reporting units. Based on the assessments, the Corporation concluded that none of its reporting units are at risk of impairment, as each of the reporting units’ fair values are substantially in excess of their carrying values. For more information regarding the nature of and accounting for the Corporation’s annual goodwill impairment testing, see Note 1 – Summary of Significant Accounting Principles to the Consolidated Financial Statements of the Corporation’s 2024 Annual Report on Form 10-K.
```

## p28 (seed_0083 3, chunk 0000034088-26-000067:323.0:335.0)

**Claim:** These cautionary statements suggest the company recognizes a significant risk that its cost reductions may not prove to be sustainable over time and that maintaining them could potentially compromise competitive positioning.

**Chunk:**

```
[Exxon Mobil Corporation (XOM) | 10-Q | Q1 FY2026 | Part I, Item 2: MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND]
Structural Cost Savings (Non-GAAP)
Structural Cost Savings describes decreases in cash opex excluding energy and production taxes as a result of operational
efficiencies, workforce reductions, divestment-related reductions, and other cost-savings measures that are expected to be
sustainable compared to 2019 levels. Relative to 2019, estimated cumulative Structural Cost Savings totaled $15.6 billion,
which included an additional $0.6 billion in the first three months of 2026. The total change between periods in expenses below
will reflect both Structural Cost Savings and other changes in spend, including market factors, such as inflation and foreign
exchange impacts, as well as changes in activity levels and costs associated with new operations, mergers and acquisitions, new
business venture development, and early-stage projects. Structural Cost Savings from new operations, mergers and acquisitions,
and new business venture developments are included in the cumulative Structural Cost Savings. Estimates of cumulative annual
structural savings may be revised depending on whether cost reductions realized in prior periods are determined to be
sustainable compared to 2019 levels. Structural Cost Savings are stewarded internally to support management's oversight of
spending over time. This measure is useful for investors to understand the Corporation's efforts to optimize spending through
disciplined expense management.
```

## p29 (seed_0053 4, chunk 0000070858-24-000122:1445.0:1453.0)

**Claim:** For purposes of the Consolidated Balance Sheet, the Corporation offsets derivative assets and liabilities with the same counterparty where it has a legally enforceable ISDA master netting agreement.

**Chunk:**

```
[Bank of America Corporation (BAC) | 10-K | FY2023 | Item 8: Financial Statements and Supplementary Data Table of Contents]
(1)Represents the total contract/notional amount of derivative assets and liabilities outstanding.
(2)Includes certain out-of-the-money purchased options that have a liability amount primarily due to the deferral of option premiums to the end of the contract.
(3)Includes certain out-of-the-money written options that have an asset amount primarily due to the deferral of option premiums to the end of the contract.
(4)The net derivative asset (liability) and notional amount of written credit derivatives for which the Corporation held purchased credit derivatives with identical underlying referenced names were $(1.2) billion and $276.9 billion at December 31, 2022.
Offsetting of Derivatives
The Corporation enters into International Swaps and Derivatives Association, Inc. (ISDA) master netting agreements or similar agreements with substantially all of the Corporation’s derivative counterparties. Where legally enforceable, these master netting agreements give the Corporation, in the event of default by the counterparty, the right to liquidate securities held as collateral and to offset receivables and payables with the same counterparty. For purposes of the Consolidated Balance Sheet, the Corporation offsets derivative assets and liabilities and cash collateral held with the same counterparty where it has such a legally enforceable master netting agreement.
The following table presents derivative instruments included in derivative assets and liabilities on the Consolidated Balance
Sheet at December 31, 2023 and 2022 by primary risk (e.g., interest rate risk) and the platform, where applicable, on which these derivatives are transacted. Balances are presented on a gross basis, prior to the application of counterparty and cash collateral netting. Total gross derivative assets and liabilities are adjusted on an aggregate basis to take into consideration the effects of legally enforceable master netting agreements, which include reducing the balance for counterparty netting and cash collateral received or paid.
For more information on offsetting of securities financing agreements, see Note 10 – Securities Financing Agreements, Short-term Borrowings, Collateral and Restricted Cash.
```

## p30 (seed_0074 1, chunk 0000078003-25-000114:498.0:503.0)

**Claim:** The increase in Medicare rebates in the first quarter of 2025 was primarily driven by the impact of higher manufacturer discounts as a result of IRA Medicare Part D Redesign.

**Chunk:**

```
[PFIZER INC (PFE) | 10-Q | Q1 FY2025 | Part I, Item 2: MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS]
(a)The increase in Medicare rebates in the first quarter of 2025 is primarily driven by the impact of higher manufacturer discounts as a result of IRA Medicare Part D Redesign. See the Overview of Our Performance, Operating Environment, Strategy and Outlook section within MD&A.
(b)The 2024 amount included a $771 million favorable final adjustment to the estimated non-cash Paxlovid revenue reversal of $3.5 billion recorded in the fourth quarter of 2023.
Product revenue deductions are primarily a function of product sales volume, mix of products sold, contractual or legislative discounts and rebates.
For information on our accruals for product revenue deductions, including the balance sheet classification of these accruals, see Note 1B.
Total Revenues––Selected Product Discussion
Biopharma
```

## p31 (seed_0053 3, chunk 0000070858-24-000122:1445.0:1453.0)

**Claim:** Where legally enforceable, these ISDA master netting agreements also give the Corporation the right to offset receivables and payables with the same counterparty.

**Chunk:**

```
[Bank of America Corporation (BAC) | 10-K | FY2023 | Item 8: Financial Statements and Supplementary Data Table of Contents]
(1)Represents the total contract/notional amount of derivative assets and liabilities outstanding.
(2)Includes certain out-of-the-money purchased options that have a liability amount primarily due to the deferral of option premiums to the end of the contract.
(3)Includes certain out-of-the-money written options that have an asset amount primarily due to the deferral of option premiums to the end of the contract.
(4)The net derivative asset (liability) and notional amount of written credit derivatives for which the Corporation held purchased credit derivatives with identical underlying referenced names were $(1.2) billion and $276.9 billion at December 31, 2022.
Offsetting of Derivatives
The Corporation enters into International Swaps and Derivatives Association, Inc. (ISDA) master netting agreements or similar agreements with substantially all of the Corporation’s derivative counterparties. Where legally enforceable, these master netting agreements give the Corporation, in the event of default by the counterparty, the right to liquidate securities held as collateral and to offset receivables and payables with the same counterparty. For purposes of the Consolidated Balance Sheet, the Corporation offsets derivative assets and liabilities and cash collateral held with the same counterparty where it has such a legally enforceable master netting agreement.
The following table presents derivative instruments included in derivative assets and liabilities on the Consolidated Balance
Sheet at December 31, 2023 and 2022 by primary risk (e.g., interest rate risk) and the platform, where applicable, on which these derivatives are transacted. Balances are presented on a gross basis, prior to the application of counterparty and cash collateral netting. Total gross derivative assets and liabilities are adjusted on an aggregate basis to take into consideration the effects of legally enforceable master netting agreements, which include reducing the balance for counterparty netting and cash collateral received or paid.
For more information on offsetting of securities financing agreements, see Note 10 – Securities Financing Agreements, Short-term Borrowings, Collateral and Restricted Cash.
```

## p32 (seed_0073 4, chunk 0000078003-26-000095:107.0:110.0)

**Claim:** The dividend income was recorded in Other (income)/deductions—net.

**Chunk:**

```
[PFIZER INC (PFE) | 10-Q | Q2 FY2026 | Part I, Item 1: FINANCIAL STATEMENTS]
C. Sale of Investment
Sale of Investment in ViiV––On March 31, 2026, which fell in our second fiscal quarter of 2026, Pfizer completed the exit of its 11.7% investment in ViiV. We received $1.875 billion in cash proceeds. See Note 4 and Note 2C in our 2025 Form 10-K.
Dividend income from our investment in ViiV, recorded in Other (income)/deductions—net, was $98 million and $73 million for the three months ended June 28, 2026 and June 29, 2025, respectively, and $180 million and $111 million for the six months ended June 28, 2026 and June 29, 2025, respectively (see Note 4).
D. Research and Development Arrangement
```

## p33 (seed_0068 4, chunk 0001045810-25-000230:354.0:360.0)

**Claim:** NVIDIA characterizes its revenue as concentrated among a limited number of direct, indirect and cloud service purchasers, and suggests this trend may continue into the future.

**Chunk:**

```
[NVIDIA CORP (NVDA) | 10-Q | Q3 FY2026 | Part I, Item 2: Management's Discussion and Analysis of Financial Condition and Results of Operations]
Direct Customers – For the third quarter of fiscal year 2026, four direct customers with sales greater than 10% of total revenue included: Customer A at 22%, Customer B at 15%, Customer C at 13%, and Customer D at 11%, which were attributable to the Compute & Networking segment. For the first nine months of fiscal year 2026, sales to two direct customers represented 21% and 13% of total revenue, respectively, both of which were attributable to the Compute & Networking segment. The customers referenced above may represent different customers than those reported in a previous period.
For the third quarter of fiscal year 2025, sales to three direct customers each represented 12% of total revenue, which were attributable to the Compute & Networking segment. For the first nine months of fiscal year 2025, sales to three direct customers represented 12%, 11%, and 11% of total revenue, which were attributable to the Compute & Networking segment.
Indirect Customers – Indirect customer revenue is an estimation based upon multiple factors including customer purchase order information, product specifications, internal sales data, and other sources. Indirect customers primarily purchase our products through system integrators and distributors.
We generate a significant amount of our revenue from a limited number of indirect customers, some individually representing 10% or more of our revenue. Certain companies purchase cloud and related services through various direct and indirect customers. We estimate that one AI research and deployment company contributed to a meaningful amount of our revenue purchasing cloud services from our customers in the third quarter of fiscal year 2026. Our revenue is concentrated among a limited number of direct, indirect and cloud service purchasers and this trend may continue.
Revenue by geographic region is designated based on the location of the customers' headquarters of direct customers even if the estimated revenue may be attributable to indirect customers in a different location. Revenue from sales to customers headquartered outside of the United States accounted for 31% and 34% of total revenue for the third quarter and first nine months of fiscal year 2026, respectively, and 44% and 41% of total revenue for the third quarter and first nine months of fiscal year 2025, respectively.
Gross Profit and Gross Margin
```

## p34 (seed_0063 1, chunk 0001628280-25-048859:1284.0:1301.0)

**Claim:** For the three months ended September 30, 2025, JPMorgan Chase & Co reported significant transfers from level 3 into level 2 of $914 million of gross equity derivative receivables and $1.2 billion of gross equity derivative payables.

**Chunk:**

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2025 | Part I, Item 1: Financial Statements]
(g)Loan originations are included in purchases.
(h)Includes financial assets and liabilities that have matured, been partially or fully repaid, impacts of modifications, deconsolidations associated with beneficial interests in VIEs and other items.
Level 3 analysis
Consolidated balance sheets changes
The following describes significant changes to level 3 assets since December 31, 2024, for those items measured at fair value on a recurring basis. Refer to Assets and liabilities measured at fair value on a nonrecurring basis on page 110 for further information on changes impacting items measured at fair value on a nonrecurring basis.
Three and nine months ended September 30, 2025
Level 3 assets were $25.4 billion at September 30, 2025, reflecting a decrease of $53 million from June 30, 2025, and an increase of $1.7 billion from December 31, 2024.
The increase for the nine months ended September 30, 2025 was predominantly driven by higher:
•Other trading assets of $301 million due to gains and purchases.
•Gross derivative receivables of $1.2 billion due to gains and purchases primarily offset by settlements and net transfers.
Refer to the sections below for additional information.
Transfers between levels for instruments carried at fair value on a recurring basis
For the three months ended September 30, 2025 and 2024, there were no significant transfers from level 2 into level 3.
For the three months ended September 30, 2025, significant transfers from level 3 into level 2 included the following:
•$914 million and $1.2 billion of gross equity derivative receivables and gross equity derivative payables, respectively, as a result of an increase in observability and a decrease in the significance of unobservable inputs.
For the three months ended September 30, 2024, there were no significant transfers from level 3 into level 2.
For the nine months ended September 30, 2025, significant transfers from level 2 into level 3 included the following:
•$1.1 billion and $1.2 billion of gross equity derivative receivables and gross equity derivative payables, respectively, as a result of a decrease in observability and an increase in the significance of unobservable inputs.
```

## p35 (seed_0060 3, chunk 0000909832-26-000051:204.0:215.0)

**Claim:** Membership fee increases drove membership fee revenue growth in Q3 FY2026

**Chunk:**

```
[COSTCO WHOLESALE CORP /NEW (COST) | 10-Q | Q3 FY2026 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations]
•We opened four new warehouses: three in the U.S. and one in Canada, compared to nine new warehouses, including one relocation;
•Net sales increased 12% to $69,154, driven by an increase in comparable sales and sales at 23 net new warehouses opened since the end of the third quarter of 2025;
•Higher gasoline prices positively impacted net sales by $1,367, or 221 basis points, and changes in foreign currencies positively impacted net sales by approximately $643, or 104 basis points;
•Membership fee revenue increased 11% to $1,373, primarily driven by new member sign-ups, membership fee increases, and upgrades to Executive Membership;
•Gross margin as a percentage of net sales and excluding the impact of gasoline price inflation increased one basis point;
•SG&A expenses as a percentage of net sales and excluding the impact of gasoline price inflation decreased two basis points;
•The effective tax rate was 25.4%, compared to 26.2%;
•Net income increased to $2,192, $4.93 per diluted share, compared to $1,903, $4.28 per diluted share; and
•A quarterly cash dividend of $1.47 per share was declared on April 15, 2026, and paid on May 15, 2026.
RESULTS OF OPERATIONS
```

## p36 (seed_0081 2, chunk 0000034088-23-000056:132.0:133.0)

**Claim:** The Corporation believes that earnings excluding Identified Items provides investors increased transparency into business results and trends and provides investors with a view of the business as seen through the eyes of management.

**Chunk:**

```
[Exxon Mobil Corporation (XOM) | 10-Q | Q3 FY2023 | Part I, Item 2: MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS]
FUNCTIONAL EARNINGS SUMMARY
Earnings (loss) excluding Identified Items (non-GAAP) are earnings (loss) excluding individually significant non-operational events with, typically, an absolute corporate total earnings impact of at least $250 million in a given quarter. The earnings (loss) impact of an identified item for an individual segment may be less than $250 million when the item impacts several periods or several segments. Earnings (loss) excluding identified items does include non-operational earnings events or impacts that are generally below the $250 million threshold utilized for Identified Items. Management uses these figures to improve comparability of the underlying business across multiple periods by isolating and removing significant non-operational events from business results. The Corporation believes this view provides investors increased transparency into business results and trends and provides investors with a view of the business as seen through the eyes of management. Earnings (loss) excluding Identified Items is not meant to be viewed in isolation or as a substitute for net income (loss) attributable to ExxonMobil as prepared in accordance with U.S. GAAP.
```

## p37 (seed_0048 4, chunk 0000320193-25-000079:478.0:485.0)

**Claim:** For derivative instruments designated as cash flow hedges, amounts excluded from the assessment of hedge effectiveness are recognized on a straight-line basis over the life of the hedge in the Consolidated Statements of Operations line item to which the hedge relates.

**Chunk:**

```
[Apple Inc. (AAPL) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data]
All derivative instruments are recorded in the Consolidated Balance Sheets at fair value. The accounting treatment for derivative gains and losses is based on intended use and hedge designation.
Gains and losses arising from amounts that are included in the assessment of cash flow hedge effectiveness are initially deferred in accumulated other comprehensive income/(loss) and subsequently reclassified into earnings when the hedged transaction affects earnings, and in the same line item in the Consolidated Statements of Operations. Gains and losses arising from amounts that are included in the assessment of fair value hedge effectiveness are recognized in the Consolidated Statements of Operations line item to which the hedge relates along with offsetting losses and gains related to the change in value of the hedged item.
For derivative instruments designated as cash flow and fair value hedges, amounts excluded from the assessment of hedge effectiveness are recognized on a straight-line basis over the life of the hedge in the Consolidated Statements of Operations line item to which the hedge relates. Changes in the fair value of amounts excluded from the assessment of hedge effectiveness are recognized in other comprehensive income/(loss).
Gains and losses arising from changes in the fair values of derivative instruments that are not designated as accounting hedges are recognized in the Consolidated Statements of Operations.
The Company classifies cash flows related to derivative instruments in the same section of the Consolidated Statements of Cash Flows as the items being hedged, which are generally classified as operating activities.
Foreign Exchange Rate Risk
To protect gross margins from fluctuations in foreign exchange rates, the Company may use forwards, options or other instruments, and may designate these instruments as cash flow hedges. The Company generally hedges portions of its forecasted foreign currency exposure associated with revenue and inventory purchases, typically for up to 12 months.
To protect the Company’s foreign currency–denominated term debt or marketable securities from fluctuations in foreign exchange rates, the Company may use forwards, cross-currency swaps or other instruments. The Company designates these instruments as either cash flow or fair value hedges. As of September 27, 2025, the maximum length of time over which the Company is hedging its exposure to the variability in future cash flows for term debt–related foreign currency transactions is 17 years.
```

## p38 (seed_0077 3, chunk 0000027419-26-000022:131.0:131.0)

**Claim:** The filing directs readers to Note 3 for additional information about these interchange fee settlements.

**Chunk:**

```
[TARGET CORPORATION (TGT) | 10-Q | Q1 FY2026 | Part I, Item 1: Financial Statements]
(a)For the three months ended May 3, 2025, includes $593 million of pretax net gains related to settlements of credit card interchange fee litigation matters. Note 3 provides additional information.
```

## p39 (seed_0060 4, chunk 0000909832-26-000051:225.0:226.0)

**Claim:** Upgrades to Executive Membership drove membership fee revenue growth in Q3 FY2026

**Chunk:**

```
[COSTCO WHOLESALE CORP /NEW (COST) | 10-Q | Q3 FY2026 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations]
Membership fee revenue increased 11% and 13% in the third quarter and first thirty-six weeks of 2026, driven by new member sign-ups, membership fee increases and upgrades to Executive Membership. At the end of the third quarter of 2026, our renewal rates were 92.2% in the U.S. and Canada and 89.7% worldwide. Renewal rates were negatively impacted by a higher number of memberships sold online, including through digital promotions, entering the renewal rate calculation. These memberships renew at a slightly lower rate on average.
As previously reported, we increased our annual membership fees in the U.S. and Canada, effective September 1, 2024. We account for membership fee revenue on a deferred basis, recognized ratably over the one-year membership period. The fee income increase accounted for approximately 25% and 35% of membership income growth during the third quarter and first thirty-six weeks of 2026.
```

## p40 (seed_0049 6, chunk 0000320193-24-000069:105.0:112.0)

**Claim:** Interpretation: concentration eased modestly but remained high, with the top two vendors together at 66% (47%+19%) versus 71% (48%+23%) previously. This suggests continued significant exposure to a small number of vendors, especially the largest, though the absolute balance fell.

**Chunk:**

```
[Apple Inc. (AAPL) | 10-Q | Q2 FY2024 | Part I, Item 1: Financial Statements]
Accounts Receivable
Trade Receivables
The Company’s third-party cellular network carriers accounted for 34% and 41% of total trade receivables as of March 30, 2024 and September 30, 2023, respectively. The Company requires third-party credit support or collateral from certain customers to limit credit risk.
Vendor Non-Trade Receivables
The Company has non-trade receivables from certain of its manufacturing vendors resulting from the sale of components to these vendors who manufacture subassemblies or assemble final products for the Company. The Company purchases these components directly from suppliers. The Company does not reflect the sale of these components in products net sales. Rather, the Company recognizes any gain on these sales as a reduction of products cost of sales when the related final products are sold by the Company. As of March 30, 2024, the Company had two vendors that individually represented 10% or more of total vendor non-trade receivables, which accounted for 47% and 19%. As of September 30, 2023, the Company had two vendors that individually represented 10% or more of total vendor non-trade receivables, which accounted for 48% and 23%.
Note 5 – Condensed Consolidated Financial Statement Details
The following table shows the Company’s condensed consolidated financial statement details as of March 30, 2024 and September 30, 2023 (in millions):
Property, Plant and Equipment, Net
```
