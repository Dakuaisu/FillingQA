# xbrl_numeric spot-check (PRD 11.1: 10% of XBRL items)

16 of 160 candidates, drawn with seed 20261001 (`python -m scripts.xbrl_candidates`). OWNER-BLOCKED: nothing here is reviewed.
For each: is the question well-formed, is the answer right, are the gold chunks
right and complete?

## xbrl_0031

- Question: What did Bank of America report as its income before income taxes for fiscal 2025?
- Reference answer: $37,695 million for the fiscal year ended December 31, 2025.
- Accessions: 0000070858-26-000157
- xbrl_fact_id: 36280
- tags: BAC, pretax_income, FY2025, 10-K, annual, template:dur_report, unit_scale_millions

### 0000070858-26-000157:1218.0:1218.0

```
[Bank of America Corporation (BAC) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data Table of Contents]
[Table: Consolidated Statement of Income | Bank of America Corporation | FY2025 10-K | Item 8 | in millions, USD]
|  | 2025 | 2024 | 2023 |
|---|---|---|---|
| Net interest income |  |  |  |
| Interest income | $138,566 | $146,607 | $130,262 |
| Interest expense | 78,470 | 90,547 | 73,331 |
| Net interest income | 60,096 | 56,060 | 56,931 |
| Noninterest income |  |  |  |
| Fees and commissions | 39,402 | 36,291 | 32,009 |
| Market making and similar activities | 12,014 | 12,967 | 12,732 |
| Other income (loss) | 1,585 | 538 | 1,097 |
| Total noninterest income | 53,001 | 49,796 | 45,838 |
| Total revenue, net of interest expense | 113,097 | 105,856 | 102,769 |
| Provision for credit losses | 5,675 | 5,821 | 4,394 |
| Noninterest expense |  |  |  |
| Compensation and benefits | 42,346 | 40,182 | 38,330 |
| Information processing and communications | 7,453 | 7,231 | 6,707 |
| Occupancy and equipment | 7,448 | 7,289 | 7,164 |
| Product delivery and transaction related | 3,924 | 3,494 | 3,608 |
| Professional fees | 2,580 | 2,669 | 2,159 |
| Marketing | 2,204 | 1,956 | 1,927 |
| Other general operating | 3,772 | 3,991 | 5,950 |
| Total noninterest expense | 69,727 | 66,812 | 65,845 |
| Income before income taxes | 37,695 | 33,223 | 32,530 |
| Income tax expense | 7,186 | 6,250 | 6,225 |
```

### 0000070858-26-000157:1960.0:1960.0

```
[Bank of America Corporation (BAC) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data Table of Contents]
[Table: Income Before Income Tax Expense | Bank of America Corporation | FY2025 10-K | Item 8 | in millions, USD]
|  | December 31 2025 | December 31 2024 | December 31 2023 |
|---|---|---|---|
| U.S. | $28,813 | $24,251 | $23,978 |
| Non-U.S. (1) | 8,882 | 8,972 | 8,552 |
| Income before income tax expense | $37,695 | $33,223 | $32,530 |
```

### 0000070858-26-000157:2183.1:2183.1

```
[Bank of America Corporation (BAC) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data Table of Contents]
[Table | Bank of America Corporation | FY2025 10-K | Item 8 | in millions, USD]
|  |  | Total Assets at Year End (1) | Total Revenue, Net of Interest Expense (2) | Income Before Income Taxes | Net Income |
|---|---|---|---|---|---|
| Total Consolidated | 2025 | $3,411,738 | $113,097 | $37,695 | $30,509 |
|  | 2024 | 3,261,299 | 105,856 | 33,223 | 26,973 |
|  | 2023 |  | 102,769 | 32,530 | 26,305 |
```

## xbrl_0032

- Question: Bank of America income tax expense, fiscal 2025: what was the figure?
- Reference answer: $7,186 million for the fiscal year ended December 31, 2025.
- Accessions: 0000070858-26-000157
- xbrl_fact_id: 36334
- tags: BAC, income_tax, FY2025, 10-K, annual, template:dur_figure, unit_scale_millions

### 0000070858-26-000157:1218.0:1218.0

```
[Bank of America Corporation (BAC) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data Table of Contents]
[Table: Consolidated Statement of Income | Bank of America Corporation | FY2025 10-K | Item 8 | in millions, USD]
|  | 2025 | 2024 | 2023 |
|---|---|---|---|
| Net interest income |  |  |  |
| Interest income | $138,566 | $146,607 | $130,262 |
| Interest expense | 78,470 | 90,547 | 73,331 |
| Net interest income | 60,096 | 56,060 | 56,931 |
| Noninterest income |  |  |  |
| Fees and commissions | 39,402 | 36,291 | 32,009 |
| Market making and similar activities | 12,014 | 12,967 | 12,732 |
| Other income (loss) | 1,585 | 538 | 1,097 |
| Total noninterest income | 53,001 | 49,796 | 45,838 |
| Total revenue, net of interest expense | 113,097 | 105,856 | 102,769 |
| Provision for credit losses | 5,675 | 5,821 | 4,394 |
| Noninterest expense |  |  |  |
| Compensation and benefits | 42,346 | 40,182 | 38,330 |
| Information processing and communications | 7,453 | 7,231 | 6,707 |
| Occupancy and equipment | 7,448 | 7,289 | 7,164 |
| Product delivery and transaction related | 3,924 | 3,494 | 3,608 |
| Professional fees | 2,580 | 2,669 | 2,159 |
| Marketing | 2,204 | 1,956 | 1,927 |
| Other general operating | 3,772 | 3,991 | 5,950 |
| Total noninterest expense | 69,727 | 66,812 | 65,845 |
| Income before income taxes | 37,695 | 33,223 | 32,530 |
| Income tax expense | 7,186 | 6,250 | 6,225 |
```

### 0000070858-26-000157:1963.0:1963.0

```
[Bank of America Corporation (BAC) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data Table of Contents]
[Table: Income Tax Expense | Bank of America Corporation | FY2025 10-K | Item 8 | in millions, USD]
|  | 2025 | 2024 | 2023 |
|---|---|---|---|
| Current income tax expense |  |  |  |
| U.S. federal | $4,202 | $4,709 | $4,760 |
| U.S. state and local | 442 | 603 | 559 |
| Non-U.S. | 2,247 | 2,065 | 1,918 |
| Total current expense | 6,891 | 7,377 | 7,237 |
| Deferred income tax expense (benefit) |  |  |  |
| U.S. federal | (114) | (1,679) | (1,233) |
| U.S. state and local | 239 | 153 | (62) |
| Non-U.S. | 170 | 399 | 283 |
| Total deferred expense (benefit) | 295 | (1,127) | (1,012) |
| Total income tax expense | $7,186 | $6,250 | $6,225 |
```

### 0000070858-26-000157:1967.1:1967.1

```
[Bank of America Corporation (BAC) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data Table of Contents]
[Table: Reconciliation of Income Tax Expense | Bank of America Corporation | FY2025 10-K | Item 8 | in millions, USD]
|  | Amount 2025 | Percent 2025 | Amount 2024 | Percent 2024 | Amount 2023 | Percent 2023 |
|---|---|---|---|---|---|---|
| Foreign tax effects | 550 | 1.5 | 586 | 1.7 | 381 | 1.2 |
| Effect of cross-border tax laws | (205) | (0.5) | (175) | (0.5) | (83) | (0.3) |
| Changes in valuation allowances | 149 | 0.4 | 224 | 0.7 | 303 | 0.9 |
| Other | (8) | — | (68) | (0.2) | (87) | (0.2) |
| Total income tax expense (benefit) | $7,186 | 19.1% | $6,250 | 18.8% | $6,225 | 19.1% |
```

## xbrl_0033

- Question: According to its 10-Q for the first quarter of fiscal 2026, what figure did Bank of America report for total assets as of March 31, 2026?
- Reference answer: $3,496,186 million as of March 31, 2026.
- Accessions: 0000070858-26-000249
- xbrl_fact_id: 33612
- tags: BAC, total_assets, FY2026, 10-Q, instant, template:ins_filing, unit_scale_millions

### 0000070858-26-000249:1105.1:1105.1

```
[Bank of America Corporation (BAC) | 10-Q | Q1 FY2026 | Part I, Item 1: Financial Statements]
[Table: Results of Business Segments and All Other (1) | Bank of America Corporation | Q1 FY2026 10-Q | Part I, Item 1 | in millions, USD]
| At and for the three months ended March 31 | Total Corporation (2) 2026 | Total Corporation (2) 2025 | Consumer Banking 2026 | Consumer Banking 2025 | Global Wealth & Investment Management 2026 | Global Wealth & Investment Management 2025 |
|---|---|---|---|---|---|---|
| Net income | $8,584 | $7,360 | $3,060 | $2,531 | $1,329 | $1,007 |
| Period-end total assets | $3,496,186 | $3,349,039 | $1,058,618 | $1,054,637 | $336,511 | $329,816 |
|  | Global Banking |  | Global Markets |  | All Other |  |
|  | 2026 | 2025 | 2026 | 2025 | 2026 | 2025 |
| Net interest income | $3,230 | $3,151 | $1,861 | $1,189 | $(39) | $(22) |
| Noninterest income | 3,057 | 2,841 | 5,248 | 5,396 | (684) | (672) |
| Total revenue, net of interest expense | 6,287 | 5,992 | 7,109 | 6,585 | (723) | (694) |
| Provision for credit losses | 185 | 154 | 27 | 28 | (9) | (8) |
| Noninterest expense |  |  |  |  |  |  |
| Compensation and benefits (3) | 1,212 | 1,240 | 1,158 | 1,052 | — | — |
| Other noninterest expense | 2,011 | 1,944 | 3,212 | 2,759 | 163 | 290 |
```

### 0000070858-26-000249:600.1:600.1

```
[Bank of America Corporation (BAC) | 10-Q | Q1 FY2026 | Part I, Item 1: Financial Statements]
[Table: Consolidated Balance Sheet | Bank of America Corporation | Q1 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  |  | March 31 2026 | December 31 2025 |
|---|---|---|---|
|  | Loans held-for-sale (includes $5,431 and $2,271 measured at fair value) | 10,944 | 5,165 |
|  | Customer and other receivables | 96,082 | 98,186 |
|  | Other assets (includes $12,107 and $9,058 measured at fair value) | 168,921 | 164,986 |
|  | Total assets | $3,496,186 | $3,411,738 |
|  | Liabilities |  |  |
|  | Deposits in U.S. offices: |  |  |
|  | Noninterest-bearing | $529,194 | $517,834 |
|  | Interest-bearing (includes $1,783 and $1,223 measured at fair value) | 1,372,969 | 1,361,177 |
|  | Deposits in non-U.S. offices: |  |  |
|  | Noninterest-bearing | 14,924 | 14,216 |
|  | Interest-bearing | 120,576 | 125,502 |
|  | Total deposits | 2,037,663 | 2,018,729 |
|  | Federal funds purchased and securities loaned or sold under agreements to repurchase (includes $227,301 and $223,067 measured at fair value) | 353,020 | 344,716 |
|  | Trading account liabilities | 129,833 | 105,996 |
|  | Derivative liabilities | 43,938 | 42,076 |
|  | Short-term borrowings (includes $11,444 and $8,051 measured at fair value) | 57,630 | 48,088 |
```

## xbrl_0040

- Question: Bank of America income tax expense, the second quarter of fiscal 2024: what was the figure?
- Reference answer: $663 million for the three months ended June 30, 2024.
- Accessions: 0000070858-24-000208, 0000070858-25-000268
- xbrl_fact_id: 36318
- tags: BAC, income_tax, FY2024, 10-Q, quarter, template:dur_figure, unit_scale_millions

### 0000070858-24-000208:703.1:703.1

```
[Bank of America Corporation (BAC) | 10-Q | Q2 FY2024 | Part I, Item 1: Financial Statements]
[Table: Consolidated Statement of Income | Bank of America Corporation | Q2 FY2024 10-Q | Part I, Item 1 | in millions, USD]
|  | Three Months Ended June 30 2024 | Three Months Ended June 30 2023 | Six Months Ended June 30 2024 | Six Months Ended June 30 2023 |
|---|---|---|---|---|
| Marketing | 487 | 513 | 942 | 971 |
| Other general operating | 870 | 1,221 | 2,447 | 2,160 |
| Total noninterest expense | 16,309 | 16,038 | 33,546 | 32,276 |
| Income before income taxes | 7,560 | 8,034 | 14,822 | 17,123 |
| Income tax expense | 663 | 626 | 1,251 | 1,554 |
| Net income | $6,897 | $7,408 | $13,571 | $15,569 |
| Preferred stock dividends | 315 | 306 | 847 | 811 |
| Net income applicable to common shareholders | $6,582 | $7,102 | $12,724 | $14,758 |
| Per common share information |  |  |  |  |
| Earnings | $0.83 | $0.88 | $1.60 | $1.83 |
| Diluted earnings | 0.83 | 0.88 | 1.59 | 1.82 |
| Average common shares issued and outstanding | 7,897.9 | 8,040.9 | 7,933.3 | 8,053.5 |
| Average diluted common shares issued and outstanding | 7,960.9 | 8,080.7 | 7,996.2 | 8,162.6 |
```

### 0000070858-25-000268:678.1:678.1

```
[Bank of America Corporation (BAC) | 10-Q | Q2 FY2025 | Part I, Item 1: Financial Statements]
[Table: Consolidated Statement of Income | Bank of America Corporation | Q2 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | Three Months Ended June 30 2025 | Three Months Ended June 30 2024 | Six Months Ended June 30 2025 | Six Months Ended June 30 2024 |
|---|---|---|---|---|
| Marketing | 563 | 487 | 1,069 | 942 |
| Other general operating | 1,019 | 870 | 2,078 | 2,447 |
| Total noninterest expense | 17,183 | 16,309 | 34,953 | 33,546 |
| Income before income taxes | 7,688 | 7,560 | 15,804 | 14,822 |
| Income tax expense | 572 | 663 | 1,292 | 1,251 |
| Net income | $7,116 | $6,897 | $14,512 | $13,571 |
| Preferred stock dividends and other | 291 | 315 | 697 | 847 |
| Net income applicable to common shareholders | $6,825 | $6,582 | $13,815 | $12,724 |
| Per common share information |  |  |  |  |
| Earnings | $0.90 | $0.83 | $1.81 | $1.60 |
| Diluted earnings | 0.89 | 0.83 | 1.79 | 1.59 |
| Average common shares issued and outstanding | 7,581.2 | 7,897.9 | 7,629.5 | 7,933.3 |
| Average diluted common shares issued and outstanding | 7,651.6 | 7,960.9 | 7,711.2 | 7,996.2 |
```

## xbrl_0044

- Question: Costco diluted earnings per share, the first two quarters of fiscal 2026: what was the figure?
- Reference answer: $9.08 for the 24 weeks ended February 15, 2026.
- Accessions: 0000909832-26-000029
- xbrl_fact_id: 1528
- tags: COST, eps_diluted, FY2026, 10-Q, ytd, template:dur_figure, unit_scale_none

### 0000909832-26-000029:33.0:33.0

```
[COSTCO WHOLESALE CORP /NEW (COST) | 10-Q | Q2 FY2026 | Part I, Item 1: Financial Statements]
[Table: CONDENSED CONSOLIDATED STATEMENTS OF INCOME | COSTCO WHOLESALE CORP /NEW | Q2 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | 12 Weeks Ended February 15, 2026 | 12 Weeks Ended February 16, 2025 | 24 Weeks Ended February 15, 2026 | 24 Weeks Ended February 16, 2025 |
|---|---|---|---|---|
| REVENUE |  |  |  |  |
| Net sales | $68,242 | $62,530 | $134,220 | $123,515 |
| Membership fees | 1,355 | 1,193 | 2,684 | 2,359 |
| Total revenue | 69,597 | 63,723 | 136,904 | 125,874 |
| OPERATING EXPENSES |  |  |  |  |
| Merchandise costs | 60,719 | 55,744 | 119,229 | 109,853 |
| Selling, general and administrative | 6,272 | 5,663 | 12,606 | 11,509 |
| Operating income | 2,606 | 2,316 | 5,069 | 4,512 |
| OTHER INCOME (EXPENSE) |  |  |  |  |
| Interest expense | (33) | (36) | (68) | (73) |
| Interest income and other, net | 148 | 142 | 303 | 289 |
| INCOME BEFORE INCOME TAXES | 2,721 | 2,422 | 5,304 | 4,728 |
| Provision for income taxes | 686 | 634 | 1,268 | 1,142 |
| NET INCOME | $2,035 | $1,788 | $4,036 | $3,586 |
| NET INCOME PER COMMON SHARE: |  |  |  |  |
| Basic | $4.58 | $4.03 | $9.09 | $8.08 |
| Diluted | $4.58 | $4.02 | $9.08 | $8.06 |
| Shares used in calculation (000s): |  |  |  |  |
```

## xbrl_0061

- Question: JPMorgan Chase total deposits at the end of the first quarter of fiscal 2025: what was the figure?
- Reference answer: $2,495,877 million as of March 31, 2025.
- Accessions: 0000019617-25-000421
- xbrl_fact_id: 25947
- tags: JPM, deposits, FY2025, 10-Q, instant, template:ins_figure, unit_scale_millions

### 0000019617-25-000421:1033.1:1033.1

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q1 FY2025 | Part I, Item 1: Financial Statements]
[Table: Consolidated balance sheets (unaudited) | JPMorgan Chase & Co | Q1 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | March 31, 2025 | December 31, 2024 |
|---|---|---|
| Other assets (included $18,093 and $15,122 at fair value and assets pledged of $7,713 and $6,288) | 178,427 | 178,197 |
| Total assets(a) | $4,357,856 | $4,002,814 |
| Liabilities |  |  |
| Deposits (included $37,139 and $33,768 at fair value) | $2,495,877 | $2,406,032 |
| Federal funds purchased and securities loaned or sold under repurchase agreements (included $459,466 and $226,329 at fair value) | 533,046 | 296,835 |
| Short-term borrowings (included $34,936 and $26,521 at fair value) | 64,980 | 52,893 |
| Trading liabilities | 187,103 | 192,883 |
| Accounts payable and other liabilities (included $7,935 and $5,893 at fair value) | 293,538 | 280,672 |
| Beneficial interests issued by consolidated VIEs (included $7 and $1 at fair value) | 24,668 | 27,323 |
| Long-term debt (included $106,848 and $100,780 at fair value) | 407,224 | 401,418 |
| Total liabilities(a) | 4,006,436 | 3,658,056 |
| Commitments and contingencies (refer to Notes 22, 23 and 24) |  |  |
| Stockholders’ equity |  |  |
| Preferred stock ($1 par value; authorized 200,000,000 shares; issued 2,005,375 and 2,005,375 shares) | 20,045 | 20,050 |
```

### 0000019617-25-000421:1750.0:1750.0

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q1 FY2025 | Part I, Item 1: Financial Statements]
[Table: Note 15 – Deposits | JPMorgan Chase & Co | Q1 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | March 31, 2025 | December 31, 2024 |
|---|---|---|
| U.S. offices |  |  |
| Noninterest-bearing (included $33,545 and $28,904 at fair value)(a) | $581,623 | $592,500 |
| Interest-bearing (included $1,290 and $1,101 at fair value)(a) | 1,416,585 | 1,345,914 |
| Total deposits in U.S. offices | 1,998,208 | 1,938,414 |
| Non-U.S. offices |  |  |
| Noninterest-bearing (included $1,926 and $2,255 at fair value)(a) | 29,856 | 26,806 |
| Interest-bearing (included $378 and $1,508 at fair value)(a) | 467,813 | 440,812 |
| Total deposits in non-U.S. offices | 497,669 | 467,618 |
| Total deposits | $2,495,877 | $2,406,032 |
```

## xbrl_0082

- Question: What amount of income before income taxes did NVIDIA record in the first two quarters of fiscal 2025?
- Reference answer: $36,493 million for the six months ended July 28, 2024.
- Accessions: 0001045810-24-000264, 0001045810-25-000209
- xbrl_fact_id: 45993
- tags: NVDA, pretax_income, FY2025, 10-Q, ytd, template:dur_record, unit_scale_millions

### 0001045810-24-000264:43.0:43.0

```
[NVIDIA CORP (NVDA) | 10-Q | Q2 FY2025 | Part I, Item 1: Financial Statements (Unaudited)]
[Table: Condensed Consolidated Statements of Income | NVIDIA CORP | Q2 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | Three Months Ended Jul 28, 2024 | Three Months Ended Jul 30, 2023 | Six Months Ended Jul 28, 2024 | Six Months Ended Jul 30, 2023 |
|---|---|---|---|---|
| Revenue | $30,040 | $13,507 | $56,084 | $20,699 |
| Cost of revenue | 7,466 | 4,045 | 13,105 | 6,589 |
| Gross profit | 22,574 | 9,462 | 42,979 | 14,110 |
| Operating expenses |  |  |  |  |
| Research and development | 3,090 | 2,040 | 5,810 | 3,916 |
| Sales, general and administrative | 842 | 622 | 1,618 | 1,253 |
| Total operating expenses | 3,932 | 2,662 | 7,428 | 5,169 |
| Operating income | 18,642 | 6,800 | 35,551 | 8,941 |
| Interest income | 444 | 187 | 803 | 338 |
| Interest expense | (61) | (65) | (125) | (131) |
| Other, net | 189 | 59 | 264 | 42 |
| Other income (expense), net | 572 | 181 | 942 | 249 |
| Income before income tax | 19,214 | 6,981 | 36,493 | 9,190 |
| Income tax expense | 2,615 | 793 | 5,013 | 958 |
| Net income | $16,599 | $6,188 | $31,480 | $8,232 |
| Net income per share: |  |  |  |  |
| Basic | $0.68 | $0.25 | $1.28 | $0.33 |
```

### 0001045810-25-000209:264.0:264.0

```
[NVIDIA CORP (NVDA) | 10-Q | Q2 FY2026 | Part I, Item 1: Financial Statements (Unaudited)]
[Table | NVIDIA CORP | Q2 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Three Months Ended Jul 27, 2025 (In millions) | Three Months Ended Jul 28, 2024 (In millions) | Six Months Ended Jul 27, 2025 (In millions) | Six Months Ended Jul 28, 2024 (In millions) |
|---|---|---|---|---|
| Segment operating income | $30,605 | $20,217 | $54,299 | $38,505 |
| Stock-based compensation expense | (1,624) | (1,154) | (3,099) | (2,164) |
| Unallocated cost of revenue and operating expenses | (440) | (280) | (859) | (508) |
| Acquisition-related and other costs | (101) | (141) | (263) | (282) |
| Interest income | 592 | 444 | 1,108 | 803 |
| Interest expense | (62) | (61) | (124) | (125) |
| Other income (expense), net | 2,236 | 189 | 2,055 | 264 |
| Consolidated income before income tax | $31,206 | $19,214 | $53,117 | $36,493 |
```

### 0001045810-25-000209:44.0:44.0

```
[NVIDIA CORP (NVDA) | 10-Q | Q2 FY2026 | Part I, Item 1: Financial Statements (Unaudited)]
[Table: Condensed Consolidated Statements of Income | NVIDIA CORP | Q2 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Three Months Ended Jul 27, 2025 | Three Months Ended Jul 28, 2024 | Six Months Ended Jul 27, 2025 | Six Months Ended Jul 28, 2024 |
|---|---|---|---|---|
| Revenue | $46,743 | $30,040 | $90,805 | $56,084 |
| Cost of revenue | 12,890 | 7,466 | 30,284 | 13,105 |
| Gross profit | 33,853 | 22,574 | 60,521 | 42,979 |
| Operating expenses |  |  |  |  |
| Research and development | 4,291 | 3,090 | 8,280 | 5,810 |
| Sales, general and administrative | 1,122 | 842 | 2,163 | 1,618 |
| Total operating expenses | 5,413 | 3,932 | 10,443 | 7,428 |
| Operating income | 28,440 | 18,642 | 50,078 | 35,551 |
| Interest income | 592 | 444 | 1,108 | 803 |
| Interest expense | (62) | (61) | (124) | (125) |
| Other income (expense), net | 2,236 | 189 | 2,055 | 264 |
| Total other income (expense), net | 2,766 | 572 | 3,039 | 942 |
| Income before income tax | 31,206 | 19,214 | 53,117 | 36,493 |
| Income tax expense | 4,784 | 2,615 | 7,920 | 5,013 |
| Net income | $26,422 | $16,599 | $45,197 | $31,480 |
| Net income per share: |  |  |  |  |
| Basic | $1.08 | $0.68 | $1.85 | $1.28 |
```

## xbrl_0087

- Question: How much did NVIDIA carry in total liabilities at the end of the third quarter of fiscal 2025?
- Reference answer: $30,114 million as of October 27, 2024.
- Accessions: 0001045810-24-000316
- xbrl_fact_id: 46567
- tags: NVDA, total_liabilities, FY2025, 10-Q, instant, template:ins_carry, unit_scale_millions

### 0001045810-24-000316:57.0:57.0

```
[NVIDIA CORP (NVDA) | 10-Q | Q3 FY2025 | Part I, Item 1: Financial Statements (Unaudited)]
[Table: Condensed Consolidated Balance Sheets | NVIDIA CORP | Q3 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | Oct 27, 2024 | Jan 28, 2024 |
|---|---|---|
| Assets |  |  |
| Current assets: |  |  |
| Cash and cash equivalents | $9,107 | $7,280 |
| Marketable securities | 29,380 | 18,704 |
| Accounts receivable, net | 17,693 | 9,999 |
| Inventories | 7,654 | 5,282 |
| Prepaid expenses and other current assets | 3,806 | 3,080 |
| Total current assets | 67,640 | 44,345 |
| Property and equipment, net | 5,343 | 3,914 |
| Operating lease assets | 1,755 | 1,346 |
| Goodwill | 4,724 | 4,430 |
| Intangible assets, net | 838 | 1,112 |
| Deferred income tax assets | 10,276 | 6,081 |
| Other assets | 5,437 | 4,500 |
| Total assets | $96,013 | $65,728 |
| Liabilities and Shareholders' Equity |  |  |
| Current liabilities: |  |  |
| Accounts payable | $5,353 | $2,699 |
| Accrued and other current liabilities | 11,126 | 6,682 |
| Short-term debt | — | 1,250 |
| Total current liabilities | 16,479 | 10,631 |
| Long-term debt | 8,462 | 8,459 |
| Long-term operating lease liabilities | 1,490 | 1,119 |
| Other long-term liabilities | 3,683 | 2,541 |
| Total liabilities | 30,114 | 22,750 |
| Commitments and contingencies - see Note 12 |  |  |
| Shareholders’ equity: |  |  |
| Preferred stock | — | — |
| Common stock | 25 | 25 |
```

## xbrl_0104

- Question: What did Pfizer report as its long-term debt, excluding the current portion as of March 30, 2025?
- Reference answer: $57,639 million as of March 30, 2025.
- Accessions: 0000078003-25-000114
- xbrl_fact_id: 55838
- tags: PFE, long_term_debt_noncurrent, FY2025, 10-Q, instant, template:ins_report, unit_scale_millions

### 0000078003-25-000114:64.1:64.1

```
[PFIZER INC (PFE) | 10-Q | Q1 FY2025 | Part I, Item 1: FINANCIAL STATEMENTS]
[Table: CONDENSED CONSOLIDATED BALANCE SHEETS | PFIZER INC | Q1 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | March 30, 2025 (Unaudited) | December 31, 2024 |
|---|---|---|
| Accrued compensation and related items | 2,607 | 3,838 |
| Deferred revenues | 1,012 | 1,511 |
| Other current liabilities | 20,016 | 19,720 |
| Total current liabilities | 36,452 | 42,995 |
| Long-term debt | 57,639 | 57,405 |
| Pension and postretirement benefit obligations | 2,021 | 2,115 |
| Noncurrent deferred tax liabilities | 2,258 | 2,122 |
| Other taxes payable | 5,724 | 6,112 |
| Other noncurrent liabilities | 13,297 | 14,150 |
| Total liabilities | 117,391 | 124,899 |
| Commitments and Contingencies |  |  |
| Common stock | 481 | 480 |
| Additional paid-in capital | 93,856 | 93,603 |
| Treasury stock | (115,008) | (114,763) |
| Retained earnings | 119,590 | 116,725 |
| Accumulated other comprehensive loss | (8,581) | (7,842) |
| Total Pfizer Inc. shareholders’ equity | 90,338 | 88,203 |
| Equity attributable to noncontrolling interests | 299 | 294 |
| Total equity | 90,637 | 88,497 |
| Total liabilities and equity | $208,028 | $213,396 |
```

## xbrl_0107

- Question: What did Pfizer report as its total liabilities as of December 31, 2023?
- Reference answer: $137,213 million as of December 31, 2023.
- Accessions: 0000078003-24-000039, 0000078003-24-000107, 0000078003-24-000166, 0000078003-24-000191, 0000078003-25-000054
- xbrl_fact_id: 55705
- tags: PFE, total_liabilities, FY2023, 10-K, instant, template:ins_report, unit_scale_millions

### 0000078003-24-000039:838.1:838.1

```
[PFIZER INC (PFE) | 10-K | FY2023 | Item 8: FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA]
[Table: Pfizer Inc. and Subsidiary Companies | PFIZER INC | FY2023 10-K | Item 8 | in millions, USD]
|  | As of December 31, 2023 | As of December 31, 2022 |
|---|---|---|
| Total current liabilities | 47,794 | 42,138 |
| Long-term debt | 61,538 | 32,884 |
| Pension and postretirement benefit obligations | 2,167 | 2,250 |
| Noncurrent deferred tax liabilities | 640 | 1,023 |
| Other taxes payable | 8,534 | 9,812 |
| Other noncurrent liabilities | 16,539 | 13,180 |
| Total liabilities | 137,213 | 101,288 |
| Commitments and Contingencies |  |  |
| Preferred stock, no par value, at stated value; 27 shares authorized; no shares issued or outstanding as of December 31, 2023 and December 31, 2022 | — | — |
| Common stock, $0.05 par value; 12,000 shares authorized; issued: 2023—9,562; 2022—9,519 | 478 | 476 |
| Additional paid-in capital | 92,631 | 91,802 |
| Treasury stock, shares at cost: 2023—3,916; 2022—3,903 | (114,487) | (113,969) |
| Retained earnings | 118,353 | 125,656 |
| Accumulated other comprehensive loss | (7,961) | (8,304) |
| Total Pfizer Inc. shareholders’ equity | 89,014 | 95,661 |
| Equity attributable to noncontrolling interests | 274 | 256 |
| Total equity | 89,288 | 95,916 |
| Total liabilities and equity | $226,501 | $197,205 |
```

### 0000078003-24-000107:65.1:65.1

```
[PFIZER INC (PFE) | 10-Q | Q1 FY2024 | Part I, Item 1: FINANCIAL STATEMENTS]
[Table: CONDENSED CONSOLIDATED BALANCE SHEETS | PFIZER INC | Q1 FY2024 10-Q | Part I, Item 1 | in millions, USD]
|  | March 31, 2024 (Unaudited) | December 31, 2023 |
|---|---|---|
| Deferred revenues | 2,502 | 2,700 |
| Other current liabilities | 18,788 | 20,537 |
| Total current liabilities | 40,497 | 47,794 |
| Long-term debt | 61,307 | 61,538 |
| Pension and postretirement benefit obligations | 2,076 | 2,167 |
| Noncurrent deferred tax liabilities | 931 | 640 |
| Other taxes payable | 8,603 | 8,534 |
| Other noncurrent liabilities | 15,122 | 16,539 |
| Total liabilities | 128,537 | 137,213 |
| Commitments and Contingencies |  |  |
| Common stock | 480 | 478 |
| Additional paid-in capital | 92,997 | 92,631 |
| Treasury stock | (114,755) | (114,487) |
| Retained earnings | 121,318 | 118,353 |
| Accumulated other comprehensive loss | (7,758) | (7,961) |
| Total Pfizer Inc. shareholders’ equity | 92,282 | 89,014 |
| Equity attributable to noncontrolling interests | 276 | 274 |
| Total equity | 92,558 | 89,288 |
| Total liabilities and equity | $221,095 | $226,501 |
```

### 0000078003-24-000166:65.1:65.1

```
[PFIZER INC (PFE) | 10-Q | Q2 FY2024 | Part I, Item 1: FINANCIAL STATEMENTS]
[Table: CONDENSED CONSOLIDATED BALANCE SHEETS | PFIZER INC | Q2 FY2024 10-Q | Part I, Item 1 | in millions, USD]
|  | June 30, 2024 (Unaudited) | December 31, 2023 |
|---|---|---|
| Accrued compensation and related items | 2,566 | 2,776 |
| Deferred revenues | 2,528 | 2,700 |
| Other current liabilities | 16,410 | 20,537 |
| Total current liabilities | 43,819 | 47,794 |
| Long-term debt | 57,506 | 61,538 |
| Pension and postretirement benefit obligations | 2,040 | 2,167 |
| Noncurrent deferred tax liabilities | 2,227 | 640 |
| Other taxes payable | 6,532 | 8,534 |
| Other noncurrent liabilities | 16,095 | 16,539 |
| Total liabilities | 128,218 | 137,213 |
| Commitments and Contingencies |  |  |
| Common stock | 480 | 478 |
| Additional paid-in capital | 93,197 | 92,631 |
| Treasury stock | (114,757) | (114,487) |
| Retained earnings | 116,596 | 118,353 |
| Accumulated other comprehensive loss | (7,816) | (7,961) |
| Total Pfizer Inc. shareholders’ equity | 87,700 | 89,014 |
| Equity attributable to noncontrolling interests | 275 | 274 |
| Total equity | 87,975 | 89,288 |
| Total liabilities and equity | $216,193 | $226,501 |
```

### 0000078003-24-000191:66.1:66.1

```
[PFIZER INC (PFE) | 10-Q | Q3 FY2024 | Part I, Item 1: FINANCIAL STATEMENTS]
[Table: CONDENSED CONSOLIDATED BALANCE SHEETS | PFIZER INC | Q3 FY2024 10-Q | Part I, Item 1 | in millions, USD]
|  | September 29, 2024 (Unaudited) | December 31, 2023 |
|---|---|---|
| Accrued compensation and related items | 3,383 | 2,776 |
| Deferred revenues | 2,020 | 2,700 |
| Other current liabilities | 19,917 | 20,537 |
| Total current liabilities | 43,211 | 47,794 |
| Long-term debt | 58,002 | 61,538 |
| Pension and postretirement benefit obligations | 2,073 | 2,167 |
| Noncurrent deferred tax liabilities | 2,158 | 640 |
| Other taxes payable | 5,905 | 8,534 |
| Other noncurrent liabilities | 15,569 | 16,539 |
| Total liabilities | 126,918 | 137,213 |
| Commitments and Contingencies |  |  |
| Common stock | 480 | 478 |
| Additional paid-in capital | 93,477 | 92,631 |
| Treasury stock | (114,760) | (114,487) |
| Retained earnings | 121,059 | 118,353 |
| Accumulated other comprehensive loss | (7,971) | (7,961) |
| Total Pfizer Inc. shareholders’ equity | 92,286 | 89,014 |
| Equity attributable to noncontrolling interests | 272 | 274 |
| Total equity | 92,558 | 89,288 |
| Total liabilities and equity | $219,476 | $226,501 |
```

### 0000078003-25-000054:778.1:778.1

```
[PFIZER INC (PFE) | 10-K | FY2024 | Item 8: FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA]
[Table: Pfizer Inc. and Subsidiary Companies | PFIZER INC | FY2024 10-K | Item 8 | in millions, USD]
|  | As of December 31, 2024 | As of December 31, 2023 |
|---|---|---|
| Other current liabilities | 19,720 | 20,537 |
| Total current liabilities | 42,995 | 47,794 |
| Long-term debt | 57,405 | 61,538 |
| Pension and postretirement benefit obligations | 2,115 | 2,167 |
| Noncurrent deferred tax liabilities | 2,122 | 640 |
| Other taxes payable | 6,112 | 8,534 |
| Other noncurrent liabilities | 14,150 | 16,539 |
| Total liabilities | 124,899 | 137,213 |
| Commitments and Contingencies |  |  |
| Common stock, $0.05 par value; 12,000 shares authorized; issued: 2024—9,593; 2023—9,562 | 480 | 478 |
| Additional paid-in capital | 93,603 | 92,631 |
| Treasury stock, shares at cost: 2024—3,926; 2023—3,916 | (114,763) | (114,487) |
| Retained earnings | 116,725 | 118,353 |
| Accumulated other comprehensive loss | (7,842) | (7,961) |
| Total Pfizer Inc. shareholders’ equity | 88,203 | 89,014 |
| Equity attributable to noncontrolling interests | 294 | 274 |
| Total equity | 88,497 | 89,288 |
| Total liabilities and equity | $213,396 | $226,501 |
```

## xbrl_0110

- Question: How much payments for property, plant and equipment did Pfizer report for the fiscal year ended December 31, 2025?
- Reference answer: $2,629 million for the fiscal year ended December 31, 2025.
- Accessions: 0000078003-26-000026
- xbrl_fact_id: 57397
- tags: PFE, capex, FY2025, 10-K, annual, template:dur_how_much, unit_scale_millions

### 0000078003-26-000026:784.1:784.1

```
[PFIZER INC (PFE) | 10-K | FY2025 | Item 8: FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA]
[Table: Pfizer Inc. and Subsidiary Companies | PFIZER INC | FY2025 10-K | Item 8 | in millions, USD]
|  | Year Ended December 31, 2025 | Year Ended December 31, 2024 | Year Ended December 31, 2023 |
|---|---|---|---|
| Other liabilities(b) | (3,667) | (3,115) | 595 |
| Other tax accounts, net | (2,805) | (1,345) | (982) |
| Net cash provided by/(used in) operating activities | 11,704 | 12,744 | 8,700 |
| Investing Activities |  |  |  |
| Purchases of property, plant and equipment | (2,629) | (2,909) | (3,907) |
| Purchases of short-term investments | (14,356) | (10,133) | (30,974) |
| Proceeds from redemptions/sales of short-term investments | 17,959 | 4,128 | 39,264 |
| Net (purchases of)/proceeds from redemptions/sales of short-term investments with original maturities of three months or less | (2,675) | 3,136 | 5,174 |
| Purchases of long-term investments | (294) | (180) | (204) |
| Proceeds from redemptions/sales of long-term investments | 1,095 | 1,570 | 1,979 |
| Proceeds from partial sales of investment in Haleon(c) | 6,311 | 7,040 | — |
| Acquisitions of businesses, net of cash acquired | (6,927) | — | (43,430) |
| Other investing activities, net | 165 | 2 | (179) |
| Net cash provided by/(used in) investing activities | (1,351) | 2,652 | (32,278) |
| Financing Activities |  |  |  |
| Proceeds from short-term borrowings | — | 8,907 | 4,525 |
```

## xbrl_0115

- Question: What did Pfizer report as its net cash provided by operating activities for the first two quarters of fiscal 2024?
- Reference answer: -$691 million for the six months ended June 30, 2024.
- Accessions: 0000078003-24-000166, 0000078003-25-000138
- xbrl_fact_id: 55976
- tags: PFE, operating_cash_flow, FY2024, 10-Q, ytd, template:dur_report, unit_scale_millions

### 0000078003-24-000166:78.0:78.0

```
[PFIZER INC (PFE) | 10-Q | Q2 FY2024 | Part I, Item 1: FINANCIAL STATEMENTS]
[Table: CONDENSED CONSOLIDATED STATEMENTS OF CASH FLOWS | PFIZER INC | Q2 FY2024 10-Q | Part I, Item 1 | in millions, USD]
|  | Six Months Ended June 30, 2024 | Six Months Ended July 2, 2023 |
|---|---|---|
| Operating Activities |  |  |
| Net income before allocation to noncontrolling interests | $3,171 | $7,894 |
| Discontinued operations—net of tax | 12 | (1) |
| Net income from continuing operations before allocation to noncontrolling interests | 3,159 | 7,895 |
| Adjustments to reconcile net income from continuing operations before allocation to noncontrolling interests to net cash provided by/(used in) operating activities: |  |  |
| Depreciation and amortization | 3,467 | 3,060 |
| Asset write-offs and impairments | 431 | 327 |
| Deferred taxes | (1,224) | (1,471) |
| Share-based compensation expense | 426 | 253 |
| Benefit plan contributions in excess of expense/income | (338) | (322) |
| Other adjustments, net | 260 | (317) |
| Other changes in assets and liabilities, net of acquisitions and divestitures | (6,871) | (9,423) |
| Net cash provided by/(used in) operating activities | (691) | 4 |
| Investing Activities |  |  |
| Purchases of property, plant and equipment | (1,341) | (2,053) |
| Purchases of short-term investments | (1,254) | (21,006) |
| Proceeds from redemptions/sales of short-term investments | 1,712 | 12,594 |
| Net (purchases of)/proceeds from redemptions/sales of short-term investments with original maturities of three months or less | 3,538 | (11,217) |
| Purchases of long-term investments | (108) | (92) |
| Proceeds from redemptions/sales of long-term investments | 312 | 172 |
```

### 0000078003-25-000138:77.0:77.0

```
[PFIZER INC (PFE) | 10-Q | Q2 FY2025 | Part I, Item 1: FINANCIAL STATEMENTS]
[Table: CONDENSED CONSOLIDATED STATEMENTS OF CASH FLOWS | PFIZER INC | Q2 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | Six Months Ended June 29, 2025 | Six Months Ended June 30, 2024 |
|---|---|---|
| Operating Activities |  |  |
| Net income before allocation to noncontrolling interests | $5,901 | $3,171 |
| Discontinued operations—net of tax | 25 | 12 |
| Net income from continuing operations before allocation to noncontrolling interests | 5,876 | 3,159 |
| Adjustments to reconcile net income from continuing operations before allocation to noncontrolling interests to net cash provided by/(used in) operating activities: |  |  |
| Depreciation and amortization | 3,243 | 3,467 |
| Asset write-offs and impairments | 498 | 431 |
| Deferred taxes | (935) | (1,224) |
| Share-based compensation expense | 373 | 426 |
| Benefit plan contributions in excess of expense/income | (334) | (338) |
| Other adjustments, net | (61) | 260 |
| Other changes in assets and liabilities, net of acquisitions and divestitures | (6,908) | (6,871) |
| Net cash provided by/(used in) operating activities | 1,753 | (691) |
| Investing Activities |  |  |
| Purchases of property, plant and equipment | (1,182) | (1,341) |
| Purchases of short-term investments | (6,085) | (1,254) |
| Proceeds from redemptions/sales of short-term investments | 10,500 | 1,712 |
| Net (purchases of)/proceeds from redemptions/sales of short-term investments with original maturities of three months or less | (2,668) | 3,538 |
| Purchases of long-term investments | (86) | (108) |
| Proceeds from redemptions/sales of long-term investments | 145 | 312 |
```

## xbrl_0130

- Question: What was the balance of Target's total assets on February 1, 2025?
- Reference answer: $57,769 million as of February 1, 2025.
- Accessions: 0000027419-25-000018, 0000027419-25-000101, 0000027419-25-000118, 0000027419-25-000126, 0000027419-26-000016
- xbrl_fact_id: 11877
- tags: TGT, total_assets, FY2024, 10-K, instant, template:ins_balance, unit_scale_millions

### 0000027419-25-000018:489.0:489.0

```
[TARGET CORPORATION (TGT) | 10-K | FY2024 | Item 8: Financial Statements and Supplementary Data]
[Table: Consolidated Statements of Financial Position | TARGET CORPORATION | FY2024 10-K | Item 8 | in millions, USD]
|  | February 1, 2025 | February 3, 2024 |
|---|---|---|
| Assets |  |  |
| Cash and cash equivalents | $4,762 | $3,805 |
| Inventory | 12,740 | 11,886 |
| Other current assets | 1,952 | 1,807 |
| Total current assets | 19,454 | 17,498 |
| Property and equipment |  |  |
| Land | 6,735 | 6,547 |
| Buildings and improvements | 38,752 | 37,066 |
| Fixtures and equipment | 8,917 | 8,765 |
| Computer hardware and software | 3,710 | 3,428 |
| Construction-in-progress | 1,185 | 1,703 |
| Accumulated depreciation | (26,277) | (24,413) |
| Property and equipment, net | 33,022 | 33,096 |
| Operating lease assets | 3,763 | 3,362 |
| Other noncurrent assets | 1,530 | 1,400 |
| Total assets | $57,769 | $55,356 |
| Liabilities and shareholders' investment |  |  |
| Accounts payable | $13,053 | $12,098 |
| Accrued and other current liabilities | 6,110 | 6,090 |
| Current portion of long-term debt and other borrowings | 1,636 | 1,116 |
| Total current liabilities | 20,799 | 19,304 |
| Long-term debt and other borrowings | 14,304 | 14,922 |
| Noncurrent operating lease liabilities | 3,582 | 3,279 |
| Deferred income taxes | 2,303 | 2,480 |
| Other noncurrent liabilities | 2,115 | 1,939 |
| Total noncurrent liabilities | 22,304 | 22,620 |
| Shareholders' investment |  |  |
| Common stock | 38 | 38 |
```

### 0000027419-25-000101:44.0:44.0

```
[TARGET CORPORATION (TGT) | 10-Q | Q1 FY2025 | Part I, Item 1: Financial Statements]
[Table: Consolidated Statements of Financial Position | TARGET CORPORATION | Q1 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | May 3, 2025 | February 1, 2025 | May 4, 2024 |
|---|---|---|---|
| Assets |  |  |  |
| Cash and cash equivalents | $2,887 | $4,762 | $3,604 |
| Inventory | 13,048 | 12,740 | 11,730 |
| Other current assets | 1,824 | 1,952 | 1,744 |
| Total current assets | 17,759 | 19,454 | 17,078 |
| Property and equipment, net | 33,182 | 33,022 | 33,114 |
| Operating lease assets | 3,739 | 3,763 | 3,486 |
| Other noncurrent assets | 1,505 | 1,530 | 1,439 |
| Total assets | $56,185 | $57,769 | $55,117 |
| Liabilities and shareholders’ investment |  |  |  |
| Accounts payable | $11,823 | $13,053 | $11,561 |
| Accrued and other current liabilities | 6,029 | 6,110 | 5,684 |
| Current portion of long-term debt and other borrowings | 1,139 | 1,636 | 2,614 |
| Total current liabilities | 18,991 | 20,799 | 19,859 |
| Long-term debt and other borrowings | 14,334 | 14,304 | 13,487 |
| Noncurrent operating lease liabilities | 3,564 | 3,582 | 3,392 |
| Deferred income taxes | 2,338 | 2,303 | 2,543 |
| Other noncurrent liabilities | 2,011 | 2,115 | 1,996 |
| Total noncurrent liabilities | 22,247 | 22,304 | 21,418 |
| Shareholders’ investment |  |  |  |
```

### 0000027419-25-000118:44.0:44.0

```
[TARGET CORPORATION (TGT) | 10-Q | Q2 FY2025 | Part I, Item 1: Financial Statements]
[Table: Consolidated Statements of Financial Position | TARGET CORPORATION | Q2 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | August 2, 2025 | February 1, 2025 | August 3, 2024 |
|---|---|---|---|
| Assets |  |  |  |
| Cash and cash equivalents | $4,341 | $4,762 | $3,497 |
| Inventory | 12,881 | 12,740 | 12,604 |
| Other current assets | 1,812 | 1,952 | 1,817 |
| Total current assets | 19,034 | 19,454 | 17,918 |
| Property and equipment, net | 33,568 | 33,022 | 33,075 |
| Operating lease assets | 3,694 | 3,763 | 3,545 |
| Other noncurrent assets | 1,555 | 1,530 | 1,457 |
| Total assets | $57,851 | $57,769 | $55,995 |
| Liabilities and shareholders’ investment |  |  |  |
| Accounts payable | $12,019 | $13,053 | $12,595 |
| Accrued and other current liabilities | 6,068 | 6,110 | 5,749 |
| Current portion of long-term debt and other borrowings | 1,136 | 1,636 | 1,640 |
| Total current liabilities | 19,223 | 20,799 | 19,984 |
| Long-term debt and other borrowings | 15,320 | 14,304 | 13,654 |
| Noncurrent operating lease liabilities | 3,514 | 3,582 | 3,444 |
| Deferred income taxes | 2,413 | 2,303 | 2,495 |
| Other noncurrent liabilities | 1,961 | 2,115 | 1,989 |
| Total noncurrent liabilities | 23,208 | 22,304 | 21,582 |
| Shareholders’ investment |  |  |  |
```

### 0000027419-25-000126:44.0:44.0

```
[TARGET CORPORATION (TGT) | 10-Q | Q3 FY2025 | Part I, Item 1: Financial Statements]
[Table: Consolidated Statements of Financial Position | TARGET CORPORATION | Q3 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | November 1, 2025 | February 1, 2025 | November 2, 2024 |
|---|---|---|---|
| Assets |  |  |  |
| Cash and cash equivalents | $3,822 | $4,762 | $3,433 |
| Inventory | 14,896 | 12,740 | 15,165 |
| Other current assets | 1,984 | 1,952 | 1,956 |
| Total current assets | 20,702 | 19,454 | 20,554 |
| Property and equipment, net | 33,710 | 33,022 | 32,931 |
| Operating lease assets | 3,739 | 3,763 | 3,513 |
| Other noncurrent assets | 1,840 | 1,530 | 1,533 |
| Total assets | $59,991 | $57,769 | $58,531 |
| Liabilities and shareholders’ investment |  |  |  |
| Accounts payable | $13,792 | $13,053 | $14,419 |
| Accrued and other current liabilities | 6,317 | 6,110 | 5,738 |
| Current portion of long-term debt and other borrowings | 1,133 | 1,636 | 1,635 |
| Total current liabilities | 21,242 | 20,799 | 21,792 |
| Long-term debt and other borrowings | 15,366 | 14,304 | 14,346 |
| Noncurrent operating lease liabilities | 3,542 | 3,582 | 3,418 |
| Deferred income taxes | 2,279 | 2,303 | 2,419 |
| Other noncurrent liabilities | 2,061 | 2,115 | 2,067 |
| Total noncurrent liabilities | 23,248 | 22,304 | 22,250 |
| Shareholders’ investment |  |  |  |
```

### 0000027419-26-000016:506.0:506.0

```
[TARGET CORPORATION (TGT) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data]
[Table: Consolidated Statements of Financial Position | TARGET CORPORATION | FY2025 10-K | Item 8 | in millions, USD]
|  | January 31, 2026 | February 1, 2025 |
|---|---|---|
| Assets |  |  |
| Cash and cash equivalents | $5,488 | $4,762 |
| Inventory | 12,304 | 12,740 |
| Other current assets | 2,213 | 1,952 |
| Total current assets | 20,005 | 19,454 |
| Property and equipment, net | 33,749 | 33,022 |
| Operating lease assets | 3,703 | 3,763 |
| Other noncurrent assets | 2,033 | 1,530 |
| Total assets | $59,490 | $57,769 |
| Liabilities and shareholders' investment |  |  |
| Accounts payable | $12,622 | $13,053 |
| Accrued and other current liabilities | 6,478 | 6,110 |
| Current portion of long-term debt and other borrowings | 2,130 | 1,636 |
| Total current liabilities | 21,230 | 20,799 |
| Long-term debt and other borrowings | 14,326 | 14,304 |
| Noncurrent operating lease liabilities | 3,462 | 3,582 |
| Deferred income taxes | 2,265 | 2,303 |
| Other noncurrent liabilities | 2,042 | 2,115 |
| Total noncurrent liabilities | 22,095 | 22,304 |
| Shareholders' investment |  |  |
| Common stock | 38 | 38 |
| Additional paid-in capital | 7,247 | 6,996 |
| Retained earnings | 9,297 | 8,090 |
| Accumulated other comprehensive loss | (417) | (458) |
| Total shareholders' investment | 16,165 | 14,666 |
| Total liabilities and shareholders' investment | $59,490 | $57,769 |
```

## xbrl_0146

- Question: Exxon Mobil total current assets at the end of the first quarter of fiscal 2025: what was the figure?
- Reference answer: $91,233 million as of March 31, 2025.
- Accessions: 0000034088-25-000024
- xbrl_fact_id: 49398
- tags: XOM, current_assets, FY2025, 10-Q, instant, template:ins_figure, unit_scale_millions

### 0000034088-25-000024:48.0:48.0

```
[Exxon Mobil Corporation (XOM) | 10-Q | Q1 FY2025 | Part I, Item 1: FINANCIAL STATEMENTS]
[Table | Exxon Mobil Corporation | Q1 FY2025 10-Q | Part I, Item 1 | in millions]
|  | March 31, 2025 | December 31, 2024 |
|---|---|---|
| ASSETS |  |  |
| Current assets |  |  |
| Cash and cash equivalents | 17,036 | 23,029 |
| Cash and cash equivalents – restricted | 1,476 | 158 |
| Notes and accounts receivable – net | 46,303 | 43,681 |
| Inventories |  |  |
| Crude oil, products and merchandise | 20,502 | 19,444 |
| Materials and supplies | 3,976 | 4,080 |
| Other current assets | 1,940 | 1,598 |
| Total current assets | 91,233 | 91,990 |
| Investments, advances and long-term receivables | 47,853 | 47,200 |
| Property, plant and equipment – net | 292,646 | 294,318 |
| Other assets, including intangibles – net | 20,176 | 19,967 |
| Total Assets | 451,908 | 453,475 |
| LIABILITIES |  |  |
| Current liabilities |  |  |
| Notes and loans payable | 4,728 | 4,955 |
| Accounts payable and accrued liabilities | 63,987 | 61,297 |
| Income taxes payable | 5,114 | 4,055 |
| Total current liabilities | 73,829 | 70,307 |
| Long-term debt | 32,823 | 36,755 |
| Postretirement benefits reserves | 10,015 | 9,700 |
| Deferred income tax liabilities | 39,091 | 39,042 |
| Long-term obligations to equity companies | 1,381 | 1,346 |
| Other long-term obligations | 24,963 | 25,719 |
| Total Liabilities | 182,102 | 182,869 |
| Commitments and contingencies (Note 3) |  |  |
| EQUITY |  |  |
```

## xbrl_0158

- Question: Exxon Mobil total stockholders' equity at the end of the first quarter of fiscal 2026: what was the figure?
- Reference answer: $254,381 million as of March 31, 2026.
- Accessions: 0000034088-26-000067
- xbrl_fact_id: 52067
- tags: XOM, stockholders_equity, FY2026, 10-Q, instant, template:ins_figure, unit_scale_millions

### 0000034088-26-000067:58.1:58.1

```
[Exxon Mobil Corporation (XOM) | 10-Q | Q1 FY2026 | Part I, Item 1: FINANCIAL STATEMENTS]
[Table | Exxon Mobil Corporation | Q1 FY2026 10-Q | Part I, Item 1 | in millions]
|  | Note Reference Number | March 31, 2026 | December 31, 2025 |
|---|---|---|---|
| EQUITY |  |  |  |
| Common stock without par value (9,000 million shares authorized, 8,019 million shares issued) |  | 46,426 | 46,150 |
| Earnings reinvested |  | 482,344 | 482,494 |
| Accumulated other comprehensive income | 5 | (11,098) | (10,863) |
| Common stock held in treasury (3,874 million shares at March 31, 2026 and 3,840 million shares at December 31, 2025) |  | (263,291) | (258,395) |
| ExxonMobil share of equity |  | 254,381 | 259,386 |
| Noncontrolling interests |  | 6,615 | 7,240 |
| Total Equity |  | 260,996 | 266,626 |
| Total Liabilities and Equity |  | 464,410 | 448,980 |
```

## xbrl_0160

- Question: What did Exxon Mobil report as its total current assets as of March 31, 2026?
- Reference answer: $97,787 million as of March 31, 2026.
- Accessions: 0000034088-26-000067
- xbrl_fact_id: 49403
- tags: XOM, current_assets, FY2026, 10-Q, instant, template:ins_report, unit_scale_millions

### 0000034088-26-000067:58.0:58.0

```
[Exxon Mobil Corporation (XOM) | 10-Q | Q1 FY2026 | Part I, Item 1: FINANCIAL STATEMENTS]
[Table | Exxon Mobil Corporation | Q1 FY2026 10-Q | Part I, Item 1 | in millions]
|  | Note Reference Number | March 31, 2026 | December 31, 2025 |
|---|---|---|---|
| ASSETS |  |  |  |
| Current assets |  |  |  |
| Cash and cash equivalents |  | 8,435 | 10,681 |
| Notes and accounts receivable – net |  | 61,783 | 44,562 |
| Inventories |  |  |  |
| Crude oil, products and merchandise |  | 21,838 | 22,979 |
| Materials and supplies |  | 3,137 | 3,323 |
| Other current assets |  | 2,594 | 1,837 |
| Total current assets |  | 97,787 | 83,382 |
| Investments, advances and long-term receivables |  | 46,125 | 45,317 |
| Property, plant and equipment – net |  | 298,781 | 299,373 |
| Other assets, including intangibles – net |  | 21,717 | 20,908 |
| Total Assets |  | 464,410 | 448,980 |
| LIABILITIES |  |  |  |
| Current liabilities |  |  |  |
| Notes and loans payable |  | 14,531 | 9,296 |
| Accounts payable and accrued liabilities |  | 77,088 | 60,911 |
| Income taxes payable |  | 2,759 | 2,123 |
| Total current liabilities |  | 94,378 | 72,330 |
| Long-term debt |  | 33,130 | 34,241 |
| Postretirement benefits reserves |  | 8,940 | 8,847 |
| Deferred income tax liabilities |  | 40,018 | 40,216 |
| Long-term obligations to equity companies |  | 562 | 542 |
| Other long-term obligations |  | 26,386 | 26,178 |
| Total Liabilities |  | 203,414 | 182,354 |
| Commitments and contingencies | 7 |  |  |
```

# Flagged, outside the seeded 10%

Selected by rule (value <= 0), not by the seed: xbrl_0070, xbrl_0113, xbrl_0115, xbrl_0116, xbrl_0117, xbrl_0119. A zero may be
printed as a dash; a negative sits under a line whose label reads as positive.
Already shown above in the seeded 10%: xbrl_0115.

## xbrl_0070

- Question: How much net cash provided by operating activities did JPMorgan Chase report for the nine months ended September 30, 2023?
- Reference answer: -$47,257 million for the nine months ended September 30, 2023.
- Accessions: 0000019617-23-000524, 0000019617-24-000611
- xbrl_fact_id: 29291
- tags: JPM, operating_cash_flow, FY2023, 10-Q, ytd, template:dur_how_much, unit_scale_millions

### 0000019617-23-000524:1402.0:1402.0

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2023 | Part I, Item 1: Financial Statements.]
[Table: Consolidated statements of cash flows (unaudited) | JPMorgan Chase & Co | Q3 FY2023 10-Q | Part I, Item 1 | in millions, USD]
|  | Nine months ended September 30, 2023 | Nine months ended September 30, 2022 |
|---|---|---|
| Operating activities |  |  |
| Net income | $40,245 | $26,668 |
| Adjustments to reconcile net income to net cash used in operating activities: |  |  |
| Provision for credit losses | 6,558 | 4,101 |
| Depreciation and amortization | 4,175 | 5,380 |
| Deferred tax (benefit)/expense | (4,544) | (3,455) |
| Bargain purchase gain associated with the First Republic acquisition | (2,812) | — |
| Other | 3,611 | 3,815 |
| Originations and purchases of loans held-for-sale | (83,534) | (131,589) |
| Proceeds from sales, securitizations and paydowns of loans held-for-sale | 83,169 | 149,420 |
| Net change in: |  |  |
| Trading assets | (151,151) | (114,006) |
| Securities borrowed | (2,852) | 12,347 |
| Accrued interest and accounts receivable | (166) | (41,621) |
| Other assets | 39,371 | (17,114) |
| Trading liabilities | 30,787 | 34,950 |
| Accounts payable and other liabilities | (11,955) | 75,961 |
| Other operating adjustments | 1,841 | 1,040 |
| Net cash provided by/(used in) operating activities | (47,257) | 5,897 |
| Investing activities |  |  |
| Net change in: |  |  |
| Federal funds sold and securities purchased under resale agreements | (34,101) | (40,741) |
| Held-to-maturity securities: |  |  |
```

### 0000019617-24-000611:1281.0:1281.0

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2024 | Part I, Item 1: Financial Statements.]
[Table: Consolidated statements of cash flows (unaudited) | JPMorgan Chase & Co | Q3 FY2024 10-Q | Part I, Item 1 | in millions, USD]
|  | Nine months ended September 30, 2024 | Nine months ended September 30, 2023 |
|---|---|---|
| Operating activities |  |  |
| Net income | $44,466 | $40,245 |
| Adjustments to reconcile net income to net cash used in operating activities: |  |  |
| Provision for credit losses | 8,047 | 6,558 |
| Depreciation and amortization | 5,973 | 4,175 |
| Deferred tax benefit | (243) | (4,544) |
| Estimated bargain purchase gain associated with the First Republic acquisition | (103) | (2,812) |
| Initial gain on the Visa share exchange | (7,990) | — |
| Other | 1,716 | 3,611 |
| Originations and purchases of loans held-for-sale | (160,573) | (83,534) |
| Proceeds from sales, securitizations and paydowns of loans held-for-sale | 148,287 | 83,169 |
| Net change in: |  |  |
| Trading assets | (237,756) | (151,151) |
| Securities borrowed | (51,688) | (2,852) |
| Accrued interest and accounts receivable | (15,491) | (166) |
| Other assets | (1,470) | 39,371 |
| Trading liabilities | 53,495 | 30,787 |
| Accounts payable and other liabilities | 17,399 | (11,955) |
| Other operating adjustments | 6,161 | 1,841 |
| Net cash (used in) operating activities | (189,770) | (47,257) |
| Investing activities |  |  |
| Net change in: |  |  |
| Federal funds sold and securities purchased under resale agreements | (114,402) | (34,101) |
```

## xbrl_0113

- Question: How much income tax expense did Pfizer report for the nine months ended October 1, 2023?
- Reference answer: -$320 million for the nine months ended October 1, 2023.
- Accessions: 0000078003-23-000115, 0000078003-24-000191
- xbrl_fact_id: 55168
- tags: PFE, income_tax, FY2023, 10-Q, ytd, template:dur_how_much, unit_scale_millions

### 0000078003-23-000115:49.0:49.0

```
[PFIZER INC (PFE) | 10-Q | Q3 FY2023 | Part I, Item 1: FINANCIAL STATEMENTS]
[Table: CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS | PFIZER INC | Q3 FY2023 10-Q | Part I, Item 1 | in millions, USD]
|  | Three Months Ended October 1, 2023 | Three Months Ended October 2, 2022 | Nine Months Ended October 1, 2023 | Nine Months Ended October 2, 2022 |
|---|---|---|---|---|
| Revenues | $13,232 | $22,638 | $44,247 | $76,040 |
| Costs and expenses: |  |  |  |  |
| Cost of sales(a), (b) | 9,269 | 6,063 | 17,391 | 24,696 |
| Selling, informational and administrative expenses(a) | 3,281 | 3,391 | 10,196 | 9,032 |
| Research and development expenses(a) | 2,711 | 2,696 | 7,864 | 7,813 |
| Acquired in-process research and development expenses | 67 | 524 | 122 | 880 |
| Amortization of intangible assets | 1,179 | 822 | 3,466 | 2,478 |
| Restructuring charges and certain acquisition-related costs | 155 | 199 | 377 | 580 |
| Other (income)/deductions––net | (79) | (59) | (356) | 1,063 |
| Income/(loss) from continuing operations before provision/(benefit) for taxes on income/(loss) | (3,352) | 9,001 | 5,187 | 29,498 |
| Provision/(benefit) for taxes on income/(loss) | (964) | 356 | (320) | 3,098 |
| Income/(loss) from continuing operations | (2,388) | 8,645 | 5,507 | 26,400 |
| Discontinued operations––net of tax | 12 | (21) | 11 | 4 |
```

### 0000078003-24-000191:50.0:50.0

```
[PFIZER INC (PFE) | 10-Q | Q3 FY2024 | Part I, Item 1: FINANCIAL STATEMENTS]
[Table: CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS | PFIZER INC | Q3 FY2024 10-Q | Part I, Item 1 | in millions, USD]
|  | Three Months Ended September 29, 2024 | Three Months Ended October 1, 2023 | Nine Months Ended September 29, 2024 | Nine Months Ended October 1, 2023 |
|---|---|---|---|---|
| Revenues: |  |  |  |  |
| Product revenues(a) | $15,417 | $11,587 | $38,731 | $38,575 |
| Alliance revenues(a) | 1,900 | 1,645 | 6,140 | 5,672 |
| Royalty revenues(a) | 384 | 260 | 992 | 737 |
| Total revenues | 17,702 | 13,491 | 45,864 | 44,984 |
| Costs and expenses: |  |  |  |  |
| Cost of sales(b), (c) | 5,263 | 9,269 | 11,942 | 17,391 |
| Selling, informational and administrative expenses(b) | 3,244 | 3,281 | 10,456 | 10,196 |
| Research and development expenses(b) | 2,598 | 2,711 | 7,787 | 7,864 |
| Acquired in-process research and development expenses | 13 | 67 | 20 | 122 |
| Amortization of intangible assets | 1,312 | 1,179 | 3,927 | 3,466 |
| Restructuring charges and certain acquisition-related costs | 313 | 155 | 1,669 | 377 |
| Other (income)/deductions––net | 243 | 181 | 2,030 | 381 |
| Income/(loss) from continuing operations before provision/(benefit) for taxes on income/(loss) | 4,715 | (3,352) | 8,033 | 5,187 |
| Provision/(benefit) for taxes on income/(loss) | 234 | (964) | 393 | (320) |
```

## xbrl_0116

- Question: Pfizer payments for repurchases of common stock, fiscal 2024: what was the figure?
- Reference answer: $0 million for the fiscal year ended December 31, 2024.
- Accessions: 0000078003-25-000054
- xbrl_fact_id: 57303
- tags: PFE, share_repurchases, FY2024, 10-K, annual, template:dur_figure, unit_scale_millions

### 0000078003-25-000054:788.2:788.2

```
[PFIZER INC (PFE) | 10-K | FY2024 | Item 8: FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA]
[Table: Pfizer Inc. and Subsidiary Companies | PFIZER INC | FY2024 10-K | Item 8 | in millions, USD]
|  | Year Ended December 31, 2024 | Year Ended December 31, 2023 | Year Ended December 31, 2022 |
|---|---|---|---|
| Proceeds from short-term borrowings | 8,907 | 4,525 | 3,891 |
| Payments on short-term borrowings | (11,226) | (3) | (3,887) |
| Net (payments on)/proceeds from short-term borrowings with original maturities of three months or less | (2,590) | 3,161 | (222) |
| Proceeds from issuance of long-term debt | — | 30,831 | — |
| Payments on long-term debt | (2,250) | (2,569) | (3,298) |
| Purchases of common stock | — | — | (2,000) |
| Cash dividends paid | (9,512) | (9,247) | (8,983) |
| Other financing activities, net | (469) | (631) | (335) |
| Net cash provided by/(used in) financing activities | (17,140) | 26,066 | (14,834) |
| Effect of exchange-rate changes on cash and cash equivalents and restricted cash and cash equivalents | (66) | (40) | (165) |
| Net increase/(decrease) in cash and cash equivalents and restricted cash and cash equivalents | (1,810) | 2,448 | (1,515) |
| Cash and cash equivalents and restricted cash and cash equivalents, at beginning of period | 2,917 | 468 | 1,983 |
| Cash and cash equivalents and restricted cash and cash equivalents, at end of period | $1,107 | $2,917 | $468 |
|  | - Continued - |  |  |
```

## xbrl_0117

- Question: According to its 10-Q for the third quarter of fiscal 2023, what figure did Pfizer report for payments for repurchases of common stock in the nine months ended October 1, 2023?
- Reference answer: $0 million for the nine months ended October 1, 2023.
- Accessions: 0000078003-23-000115
- xbrl_fact_id: 57300
- tags: PFE, share_repurchases, FY2023, 10-Q, ytd, template:dur_filing, unit_scale_millions

### 0000078003-23-000115:77.1:77.1

```
[PFIZER INC (PFE) | 10-Q | Q3 FY2023 | Part I, Item 1: FINANCIAL STATEMENTS]
[Table: CONDENSED CONSOLIDATED STATEMENTS OF CASH FLOWS | PFIZER INC | Q3 FY2023 10-Q | Part I, Item 1 | in millions, USD]
|  | Nine Months Ended October 1, 2023 | Nine Months Ended October 2, 2022 |
|---|---|---|
| Purchases of long-term investments | (166) | (1,627) |
| Proceeds from redemptions/sales of long-term investments | 189 | 446 |
| Acquisitions of businesses, net of cash acquired | (25) | (6,225) |
| Dividend received from the Consumer Healthcare JV | — | 3,960 |
| Other investing activities, net | (193) | (200) |
| Net cash provided by/(used in) investing activities | (21,282) | (11,373) |
| Financing Activities |  |  |
| Proceeds from short-term borrowings | 14 | 3,887 |
| Payments on short-term borrowings | — | (3,887) |
| Net (payments on)/proceeds from short-term borrowings with original maturities of three months or less | (106) | 870 |
| Proceeds from issuance of long-term debt | 30,831 | — |
| Payments on long-term debt | (2,569) | (1,609) |
| Purchases of common stock | — | (2,000) |
| Cash dividends paid | (6,932) | (6,738) |
| Other financing activities, net | (613) | (342) |
| Net cash provided by/(used in) financing activities | 20,624 | (9,819) |
| Effect of exchange-rate changes on cash and cash equivalents and restricted cash and cash equivalents | (39) | (139) |
| Net increase/(decrease) in cash and cash equivalents and restricted cash and cash equivalents | 2,764 | (646) |
| Cash and cash equivalents and restricted cash and cash equivalents, at beginning of period | 468 | 1,983 |
```

## xbrl_0119

- Question: Pfizer income tax expense, fiscal 2024: what was the figure?
- Reference answer: -$28 million for the fiscal year ended December 31, 2024.
- Accessions: 0000078003-25-000054, 0000078003-26-000026
- xbrl_fact_id: 55185
- tags: PFE, income_tax, FY2024, 10-K, annual, template:dur_figure, unit_scale_millions

### 0000078003-25-000054:1070.0:1070.0

```
[PFIZER INC (PFE) | 10-K | FY2024 | Item 8: FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA]
[Table: Components of Provision/(benefit) for taxes on income based on the location of the taxing authorities include: | PFIZER INC | FY2024 10-K | Item 8 | in millions, USD]
|  | Year Ended December 31, 2024 | Year Ended December 31, 2023 | Year Ended December 31, 2022 |
|---|---|---|---|
| United States |  |  |  |
| Current income taxes: |  |  |  |
| Federal | $453 | $1,321 | $2,744 |
| State and local | 32 | (135) | (20) |
| Deferred income taxes: |  |  |  |
| Federal | (1,909) | (2,606) | (3,271) |
| State and local | (293) | (184) | (310) |
| Total U.S. tax provision/(benefit) | (1,717) | (1,605) | (857) |
| International |  |  |  |
| Current income taxes | 1,588 | 1,142 | 4,368 |
| Deferred income taxes | 100 | (652) | (183) |
| Total international tax provision/(benefit) | 1,689 | 490 | 4,185 |
| Provision/(benefit) for taxes on income | $(28) | $(1,115) | $3,328 |
```

### 0000078003-25-000054:1074.0:1080.0

```
[PFIZER INC (PFE) | 10-K | FY2024 | Item 8: FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA]
The changes in Provision/(benefit) for taxes on income impacting the effective tax rate year-over-year are summarized below:
The tax benefit of $28 million for 2024 compared to the tax benefit of $1.1 billion for 2023 was primarily a result of changes in the jurisdictional mix of earnings partially offset by a tax benefit related to the Transition Tax liability under the TCJA.
The tax benefit of $1.1 billion for 2023 compared to the tax provision of $3.3 billion for 2022 was primarily a result of changes in the jurisdictional mix of earnings and the resolution of uncertain tax positions in various markets. The 2023 pre-tax income included a greater percentage of expenses taxed at higher rates as compared to the 2022 pre-tax income, resulting in a 2023 tax benefit compared to the 2022 tax provision. These expenses included amortization expense, acquisition-related costs, restructuring charges and intangible asset impairment charges. The tax benefit for 2023 and the tax provision for 2022 included tax benefits related to global income tax resolutions in multiple tax jurisdictions spanning multiple tax years. The tax provision for 2022 also included the closing of U.S. IRS audits covering five tax years.
In all years, federal, state and international net tax liabilities assumed or established as part of a business acquisition are not included in Provision/(benefit) for taxes on income (see Note 2A).
We elected, with the filing of our 2018 U.S. Federal Consolidated Income Tax Return, to pay our initial estimated $15 billion repatriation tax liability on accumulated post-1986 foreign earnings (Transition Tax liability) over eight years through 2026. The sixth annual installment was paid by its April 15, 2024 due date. The seventh annual installment is due April 15, 2025 and is reported in current Income taxes payable as of December 31, 2024. The remaining liability is reported in noncurrent Other taxes payable. Our obligations may vary due to the availability of attributes such as foreign tax and other credit carryforwards or carrybacks.
```

### 0000078003-25-000054:763.0:763.0

```
[PFIZER INC (PFE) | 10-K | FY2024 | Item 8: FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA]
[Table: Pfizer Inc. and Subsidiary Companies | PFIZER INC | FY2024 10-K | Item 8 | in millions, USD]
|  | Year Ended December 31, 2024 | Year Ended December 31, 2023 | Year Ended December 31, 2022 |
|---|---|---|---|
| Revenues: |  |  |  |
| Product revenues | $53,816 | $50,914 | $91,793 |
| Alliance revenues | 8,388 | 7,582 | 8,537 |
| Royalty revenues(a) | 1,423 | 1,058 | 845 |
| Total revenues | 63,627 | 59,553 | 101,175 |
| Costs and expenses: |  |  |  |
| Cost of sales(b), (c) | 17,851 | 24,954 | 34,344 |
| Selling, informational and administrative expenses(b) | 14,730 | 14,771 | 13,677 |
| Research and development expenses(b) | 10,822 | 10,679 | 11,428 |
| Acquired in-process research and development expenses | 108 | 194 | 953 |
| Amortization of intangible assets | 5,286 | 4,733 | 3,609 |
| Restructuring charges and certain acquisition-related costs | 2,419 | 2,943 | 1,375 |
| Other (income)/deductions––net | 4,388 | 222 | 1,062 |
| Income from continuing operations before provision/(benefit) for taxes on income | 8,023 | 1,058 | 34,729 |
| Provision/(benefit) for taxes on income | (28) | (1,115) | 3,328 |
| Income from continuing operations | 8,051 | 2,172 | 31,401 |
| Discontinued operations––net of tax | 11 | (15) | 6 |
| Net income before allocation to noncontrolling interests | 8,062 | 2,158 | 31,407 |
```

### 0000078003-26-000026:1054.0:1054.0

```
[PFIZER INC (PFE) | 10-K | FY2025 | Item 8: FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA]
[Table: Components of Provision/(benefit) for taxes on income based on the location of the taxing authorities include: | PFIZER INC | FY2025 10-K | Item 8 | in millions, USD]
|  | Year Ended December 31, 2025 | Year Ended December 31, 2024 | Year Ended December 31, 2023 |
|---|---|---|---|
| Current tax expense (benefit): |  |  |  |
| U.S. Federal | $384 | $453 | $1,321 |
| U.S. State and local | 172 | 32 | (135) |
| Foreign | 1,310 | 1,588 | 1,142 |
| Total current tax expense (benefit) | $1,866 | $2,074 | $2,328 |
| Deferred tax expense (benefit): |  |  |  |
| U.S. Federal | $(1,826) | $(1,909) | $(2,606) |
| U.S. State and local | (61) | (293) | (184) |
| Foreign | (246) | 100 | (652) |
| Total deferred tax expense (benefit) | $(2,133) | $(2,102) | $(3,442) |
| Total income tax expense (benefit) |  |  |  |
| U.S. Federal | $(1,442) | $(1,456) | $(1,285) |
| U.S. State and local | 112 | (261) | (319) |
| Foreign | 1,064 | 1,689 | 490 |
| Provision/(benefit) for taxes on income | $(266) | $(28) | $(1,115) |
```

### 0000078003-26-000026:1058.0:1065.0

```
[PFIZER INC (PFE) | 10-K | FY2025 | Item 8: FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA]
The changes in Provision/(benefit) for taxes on income impacting the effective tax rate year-over-year are summarized below:
2025 v. 2024
The tax benefit of $266 million for 2025 compared to the tax benefit of $28 million for 2024 was primarily due to a favorable change in the jurisdictional mix of earnings, tax benefits related to global income tax resolutions in multiple tax jurisdictions spanning multiple tax years, and the remeasurement of deferred tax liabilities due to the enactment of the OBBBA on July 4, 2025.
2024 v. 2023
The tax benefit of $28 million for 2024 compared to the tax benefit of $1.1 billion for 2023 was primarily a result of changes in the jurisdictional mix of earnings partially offset by a tax benefit related to the Transition Tax liability under the TCJA.
In all years, federal, state and international net tax liabilities assumed or established as part of a business acquisition are not included in Provision/(benefit) for taxes on income (see Note 2A).
We elected, with the filing of our 2018 U.S. Federal Consolidated Income Tax Return, to pay our initial estimated $15 billion repatriation tax liability on accumulated post-1986 foreign earnings (Transition Tax liability) over eight years through 2026. The seventh annual installment was paid by its April 15, 2025 due date. The eighth and final annual installment is due April 15, 2026 and is reported in current Income taxes payable as of December 31, 2025. Our obligations may vary due to the availability of attributes such as foreign tax and other credit carryforwards or carrybacks.
Consistent with the disclosure requirements of ASU 2023-09, the table below summarizes income taxes paid (net of refunds received): Year Ended December 31, (MILLIONS) 2025 U.S. Federal taxes $ 2,729 U.S. State and local taxes 101 Foreign taxes Ireland 1,016 Other foreign jurisdictions 842 Total income taxes paid $ 4,688
```

### 0000078003-26-000026:760.0:760.0

```
[PFIZER INC (PFE) | 10-K | FY2025 | Item 8: FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA]
[Table: Pfizer Inc. and Subsidiary Companies | PFIZER INC | FY2025 10-K | Item 8 | in millions, USD]
|  | Year Ended December 31, 2025 | Year Ended December 31, 2024 | Year Ended December 31, 2023 |
|---|---|---|---|
| Revenues: |  |  |  |
| Product revenues | $51,663 | $53,816 | $50,914 |
| Alliance revenues | 9,266 | 8,388 | 7,582 |
| Royalty revenues | 1,650 | 1,423 | 1,058 |
| Total revenues | 62,579 | 63,627 | 59,553 |
| Costs and expenses: |  |  |  |
| Cost of sales(a), (b) | 16,067 | 17,851 | 24,954 |
| Selling, informational and administrative expenses(a) | 13,794 | 14,730 | 14,771 |
| Research and development expenses(a) | 10,437 | 10,822 | 10,679 |
| Acquired in-process research and development expenses | 1,613 | 108 | 194 |
| Amortization of intangible assets | 4,874 | 5,286 | 4,733 |
| Restructuring charges and certain acquisition-related costs | 1,550 | 2,419 | 2,943 |
| Other (income)/deductions––net | 6,724 | 4,388 | 222 |
| Income from continuing operations before provision/(benefit) for taxes on income | 7,520 | 8,023 | 1,058 |
| Provision/(benefit) for taxes on income | (266) | (28) | (1,115) |
| Income from continuing operations | 7,787 | 8,051 | 2,172 |
| Discontinued operations––net of tax | 25 | 11 | (15) |
| Net income before allocation to noncontrolling interests | 7,812 | 8,062 | 2,158 |
```

# Flagged: figure printed in a retrieved non-gold chunk (F-100)

From dev run(s) 19693d4aa874 (`python -m scripts.f100_check`): the item was numerically correct with no gold set in the top 10, and a retrieved chunk outside gold prints the reference figure. Should that chunk be an alternative evidence set? Gold is unchanged until the owner decides.

## xbrl_0008

- Question: How much selling, general and administrative expense did Apple report for the three months ended June 28, 2025?
- Reference answer: $6,650 million for the three months ended June 28, 2025.
- Accessions: 0000320193-25-000073, 0000320193-26-000020
- xbrl_fact_id: 43669
- tags: AAPL, sga, FY2025, 10-Q, quarter, template:dur_how_much, unit_scale_millions

### 0000320193-25-000073:38.0:38.0

```
[Apple Inc. (AAPL) | 10-Q | Q3 FY2025 | Part I, Item 1: Financial Statements]
[Table: CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS (Unaudited) | Apple Inc. | Q3 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | Three Months Ended June 28, 2025 | Three Months Ended June 29, 2024 | Nine Months Ended June 28, 2025 | Nine Months Ended June 29, 2024 |
|---|---|---|---|---|
| Net sales: |  |  |  |  |
| Products | $66,613 | $61,564 | $233,287 | $224,908 |
| Services | 27,423 | 24,213 | 80,408 | 71,197 |
| Total net sales | 94,036 | 85,777 | 313,695 | 296,105 |
| Cost of sales: |  |  |  |  |
| Products | 43,620 | 39,803 | 147,097 | 140,667 |
| Services | 6,698 | 6,296 | 19,738 | 18,634 |
| Total cost of sales | 50,318 | 46,099 | 166,835 | 159,301 |
| Gross margin | 43,718 | 39,678 | 146,860 | 136,804 |
| Operating expenses: |  |  |  |  |
| Research and development | 8,866 | 8,006 | 25,684 | 23,605 |
| Selling, general and administrative | 6,650 | 6,320 | 20,553 | 19,574 |
| Total operating expenses | 15,516 | 14,326 | 46,237 | 43,179 |
| Operating income | 28,202 | 25,352 | 100,623 | 93,625 |
| Other income/(expense), net | (171) | 142 | (698) | 250 |
| Income before provision for income taxes | 28,031 | 25,494 | 99,925 | 93,875 |
| Provision for income taxes | 4,597 | 4,046 | 15,381 | 14,875 |
```

### 0000320193-26-000020:38.0:38.0

```
[Apple Inc. (AAPL) | 10-Q | Q3 FY2026 | Part I, Item 1: Financial Statements]
[Table: CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS (Unaudited) | Apple Inc. | Q3 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Three Months Ended June 27, 2026 | Three Months Ended June 28, 2025 | Nine Months Ended June 27, 2026 | Nine Months Ended June 28, 2025 |
|---|---|---|---|---|
| Net sales: |  |  |  |  |
| Products | $78,678 | $66,613 | $272,629 | $233,287 |
| Services | 30,739 | 27,423 | 91,728 | 80,408 |
| Total net sales | 109,417 | 94,036 | 364,357 | 313,695 |
| Cost of sales: |  |  |  |  |
| Products | 47,153 | 43,620 | 163,810 | 147,097 |
| Services | 7,494 | 6,698 | 21,765 | 19,738 |
| Total cost of sales | 54,647 | 50,318 | 185,575 | 166,835 |
| Gross margin | 54,770 | 43,718 | 178,782 | 146,860 |
| Operating expenses: |  |  |  |  |
| Research and development | 11,729 | 8,866 | 34,035 | 25,684 |
| Selling, general and administrative | 7,346 | 6,650 | 22,315 | 20,553 |
| Total operating expenses | 19,075 | 15,516 | 56,350 | 46,237 |
| Operating income | 35,695 | 28,202 | 122,432 | 100,623 |
| Other income/(expense), net | 572 | (171) | 670 | (698) |
| Income before provision for income taxes | 36,267 | 28,031 | 123,102 | 99,925 |
| Provision for income taxes | 6,478 | 4,597 | 21,638 | 15,381 |
```

- xbrl_0008: 6650 in non-gold 0000320193-25-000073:198.0:198.0 [Apple Inc. (AAPL) | 10-Q | Q3 FY2025 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations] | | Selling, general and administrative | $6,650 | $6,320 | $20,553 | $19,574 |
- xbrl_0008: 6650 in non-gold 0000320193-26-000020:201.0:201.0 [Apple Inc. (AAPL) | 10-Q | Q3 FY2026 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations] | | Selling, general and administrative | $7,346 | $6,650 | 10% | $22,315 | $20,553 | 9% |

## xbrl_0017

- Question: According to its fiscal 2024 10-K, what figure did Apple report for cash and cash equivalents as of September 28, 2024?
- Reference answer: $29,943 million as of September 28, 2024.
- Accessions: 0000320193-24-000123
- xbrl_fact_id: 40960
- tags: AAPL, cash_and_equivalents, FY2024, 10-K, instant, template:ins_filing, unit_scale_millions

### 0000320193-24-000123:416.0:416.0

```
[Apple Inc. (AAPL) | 10-K | FY2024 | Item 8: Financial Statements and Supplementary Data]
[Table: CONSOLIDATED BALANCE SHEETS | Apple Inc. | FY2024 10-K | Item 8 | in millions, USD]
|  | September 28, 2024 | September 30, 2023 |
|---|---|---|
|  | ASSETS: |  |
| Current assets: |  |  |
| Cash and cash equivalents | $29,943 | $29,965 |
| Marketable securities | 35,228 | 31,590 |
| Accounts receivable, net | 33,410 | 29,508 |
| Vendor non-trade receivables | 32,833 | 31,477 |
| Inventories | 7,286 | 6,331 |
| Other current assets | 14,287 | 14,695 |
| Total current assets | 152,987 | 143,566 |
| Non-current assets: |  |  |
| Marketable securities | 91,479 | 100,544 |
| Property, plant and equipment, net | 45,680 | 43,715 |
| Other non-current assets | 74,834 | 64,758 |
| Total non-current assets | 211,993 | 209,017 |
| Total assets | $364,980 | $352,583 |
|  | LIABILITIES AND SHAREHOLDERS’ EQUITY: |  |
| Current liabilities: |  |  |
| Accounts payable | $68,960 | $62,611 |
| Other current liabilities | 78,304 | 58,829 |
| Deferred revenue | 8,249 | 8,061 |
| Commercial paper | 9,967 | 5,985 |
| Term debt | 10,912 | 9,822 |
| Total current liabilities | 176,392 | 145,308 |
| Non-current liabilities: |  |  |
| Term debt | 85,750 | 95,281 |
| Other non-current liabilities | 45,888 | 49,848 |
| Total non-current liabilities | 131,638 | 145,129 |
| Total liabilities | 308,030 | 290,437 |
| Commitments and contingencies |  |  |
| Shareholders’ equity: |  |  |
```

### 0000320193-24-000123:477.1:477.1

```
[Apple Inc. (AAPL) | 10-K | FY2024 | Item 8: Financial Statements and Supplementary Data]
[Table: Cash, Cash Equivalents and Marketable Securities | Apple Inc. | FY2024 10-K | Item 8 | in millions, USD]
|  | 2024 Adjusted Cost | 2024 Unrealized Gains | 2024 Unrealized Losses | 2024 Fair Value | 2024 Cash and Cash Equivalents | 2024 Current Marketable Securities | 2024 Non-Current Marketable Securities |
|---|---|---|---|---|---|---|---|
| Mortgage- and asset-backed securities | 24,595 | 175 | (1,403) | 23,367 | — | 1,278 | 22,089 |
| Subtotal | 132,108 | 583 | (4,635) | 128,056 | 1,966 | 34,611 | 91,479 |
| Total (2)(3) | $160,600 | $688 | $(4,638) | $156,650 | $29,943 | $35,228 | $91,479 |
```

- xbrl_0017: 29943 in non-gold 0000320193-24-000123:428.2:428.2 [Apple Inc. (AAPL) | 10-K | FY2024 | Item 8: Financial Statements and Supplementary Data] | | Cash, cash equivalents, and restricted cash and cash equivalents, ending balances | $29,943 | $30,737 | $24,977 |

## xbrl_0029

- Question: Bank of America payments for repurchases of common stock, fiscal 2024: what was the figure?
- Reference answer: $13,104 million for the fiscal year ended December 31, 2024.
- Accessions: 0000070858-25-000139, 0000070858-26-000157
- xbrl_fact_id: 38658
- tags: BAC, share_repurchases, FY2024, 10-K, annual, template:dur_figure, unit_scale_millions

### 0000070858-25-000139:1245.2:1245.2

```
[Bank of America Corporation (BAC) | 10-K | FY2024 | Item 8: Financial Statements and Supplementary Data Table of Contents]
[Table: Consolidated Statement of Cash Flows | Bank of America Corporation | FY2024 10-K | Item 8 | in millions, USD]
|  | 2024 | 2023 | 2022 |
|---|---|---|---|
| Federal funds purchased and securities loaned or sold under agreements to repurchase | 47,871 | 88,252 | 3,306 |
| Short-term borrowings | 12,574 | 5,162 | 3,179 |
| Long-term debt: |  |  |  |
| Proceeds from issuance | 56,683 | 65,396 | 65,910 |
| Retirement | (70,411) | (44,571) | (34,055) |
| Preferred stock: |  |  |  |
| Proceeds from issuance | — | — | 4,426 |
| Redemption | (5,254) | — | (654) |
| Common stock repurchased | (13,104) | (4,576) | (5,073) |
| Cash dividends paid | (9,503) | (9,087) | (8,576) |
| Other financing activities, net | (127) | (717) | (312) |
| Net cash provided by (used in) financing activities | 60,369 | 93,345 | (106,039) |
| Effect of exchange rate changes on cash and cash equivalents | (3,830) | (70) | (3,123) |
| Net increase (decrease) in cash and cash equivalents | (42,959) | 102,870 | (118,018) |
| Cash and cash equivalents at January 1 | 333,073 | 230,203 | 348,221 |
| Cash and cash equivalents at December 31 | $290,114 | $333,073 | $230,203 |
| Supplemental cash flow disclosures |  |  |  |
| Interest paid | $89,687 | $69,604 | $18,526 |
| Income taxes paid, net | 3,822 | 3,405 | 2,288 |
```

### 0000070858-26-000157:1230.2:1230.2

```
[Bank of America Corporation (BAC) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data Table of Contents]
[Table: Consolidated Statement of Cash Flows | Bank of America Corporation | FY2025 10-K | Item 8 | in millions, USD]
|  | 2025 | 2024 | 2023 |
|---|---|---|---|
| Proceeds from issuance | 99,867 | 56,683 | 65,396 |
| Retirement | (76,031) | (70,411) | (44,571) |
| Preferred stock: |  |  |  |
| Proceeds from issuance | 5,493 | — | — |
| Redemption | (2,669) | (5,254) | — |
| Common stock repurchased | (21,433) | (13,104) | (4,576) |
| Cash dividends paid | (9,563) | (9,503) | (9,087) |
| Other financing activities, net | (613) | (127) | (717) |
| Net cash provided by financing activities | 69,948 | 60,369 | 93,345 |
| Effect of exchange rate changes on cash and cash equivalents | 4,327 | (3,830) | (70) |
| Net increase (decrease) in cash and cash equivalents | (58,269) | (42,959) | 102,870 |
| Cash and cash equivalents at January 1 | 290,114 | 333,073 | 230,203 |
| Cash and cash equivalents at December 31 | $231,845 | $290,114 | $333,073 |
| Supplemental cash flow disclosures |  |  |  |
| Interest paid | $79,065 | $89,687 | $69,604 |
```

- xbrl_0029: 13104 in non-gold 0000070858-25-000139:1856.0:1856.0 [Bank of America Corporation (BAC) | 10-K | FY2024 | Item 8: Financial Statements and Supplementary Data Table of Contents] | | Purchase price of shares repurchased and retired (1) | $13,104 | $4,576 | $5,073 |
- xbrl_0029: 13104 in non-gold 0000070858-26-000157:1842.0:1842.0 [Bank of America Corporation (BAC) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data Table of Contents] | | Purchase price of shares repurchased and retired (1) | $21,433 | $13,104 | $4,576 |

## xbrl_0038

- Question: How much did Bank of America carry in total stockholders' equity at the end of the first quarter of fiscal 2026?
- Reference answer: $300,668 million as of March 31, 2026.
- Accessions: 0000070858-26-000249, 0000070858-26-000394
- xbrl_fact_id: 39544
- tags: BAC, stockholders_equity, FY2026, 10-Q, instant, template:ins_carry, unit_scale_millions

### 0000070858-26-000249:600.2:600.2

```
[Bank of America Corporation (BAC) | 10-Q | Q1 FY2026 | Part I, Item 1: Financial Statements]
[Table: Consolidated Balance Sheet | Bank of America Corporation | Q1 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  |  | March 31 2026 | December 31 2025 |
|---|---|---|---|
|  | Accrued expenses and other liabilities (includes $10,825 and $8,996 measured at fair value and $1,161 and $1,177 of reserve for unfunded lending commitments) | 247,470 | 231,074 |
|  | Long-term debt (includes $79,274 and $72,591 measured at fair value) | 325,964 | 317,816 |
|  | Total liabilities | 3,195,518 | 3,108,495 |
|  | Commitments and contingencies (Note 6 – Securitizations and Other Variable Interest Entities and Note 10 – Commitments and Contingencies) |  |  |
|  | Shareholders’ equity |  |  |
|  | Preferred stock, $0.01 par value; authorized – 100,000,000 shares; issued and outstanding – 3,951,164 and 3,991,164 shares | 24,996 | 25,992 |
|  | Common stock and additional paid-in capital, $0.01 par value; authorized – 12,800,000,000 shares; issued and outstanding – 7,129,908,032 and 7,212,464,345 shares | 18,885 | 26,084 |
|  | Retained earnings | 267,765 | 261,693 |
|  | Accumulated other comprehensive income (loss) | (10,978) | (10,526) |
|  | Total shareholders’ equity | 300,668 | 303,243 |
|  | Total liabilities and shareholders’ equity | $3,496,186 | $3,411,738 |
|  | Assets of consolidated variable interest entities included in total assets above (isolated to settle the liabilities of the variable interest entities) |  |  |
|  | Trading account assets | $7,184 | $7,139 |
|  | Loans and leases | 16,936 | 17,875 |
```

### 0000070858-26-000249:603.1:603.1

```
[Bank of America Corporation (BAC) | 10-Q | Q1 FY2026 | Part I, Item 1: Financial Statements]
[Table: Consolidated Statement of Changes in Shareholders’ Equity | Bank of America Corporation | Q1 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Preferred Stock | Common Stock and Additional Paid-in Capital Shares | Common Stock and Additional Paid-in Capital Amount | Retained Earnings | Accumulated Other Comprehensive Income (Loss) | Total Shareholders’ Equity |
|---|---|---|---|---|---|---|
| Balance, December 31, 2025 | $25,992 | 7,212.5 | $26,084 | $261,693 | $(10,526) | $303,243 |
| Net income |  |  |  | 8,584 |  | 8,584 |
| Net change in debt securities |  |  |  |  | (529) | (529) |
| Net change in debit valuation adjustments |  |  |  |  | 660 | 660 |
| Net change in derivatives |  |  |  |  | (627) | (627) |
| Employee benefit plan adjustments |  |  |  |  | 35 | 35 |
| Net change in foreign currency translation adjustments |  |  |  |  | 9 | 9 |
| Dividends declared: |  |  |  |  |  |  |
| Common |  |  |  | (2,023) |  | (2,023) |
| Preferred |  |  |  | (425) |  | (425) |
| Redemption of preferred stock | (996) |  |  | (4) |  | (1,000) |
| Common stock issued under employee plans, net, and other |  | 57.2 | 41 | (60) |  | (19) |
| Common stock repurchased |  | (139.8) | (7,240) |  |  | (7,240) |
| Balance, March 31, 2026 | $24,996 | 7,129.9 | $18,885 | $267,765 | $(10,978) | $300,668 |
```

### 0000070858-26-000394:657.0:657.0

```
[Bank of America Corporation (BAC) | 10-Q | Q2 FY2026 | Part I, Item 1: Financial Statements]
[Table: Consolidated Statement of Changes in Shareholders’ Equity | Bank of America Corporation | Q2 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Preferred Stock | Common Stock and Additional Paid-in Capital Shares | Common Stock and Additional Paid-in Capital Amount | Retained Earnings | Accumulated Other Comprehensive Income (Loss) | Total Shareholders’ Equity |
|---|---|---|---|---|---|---|
| Balance, March 31, 2026 | $24,996 | 7,129.9 | $18,885 | $267,765 | $(10,978) | $300,668 |
| Net income |  |  |  | 9,074 |  | 9,074 |
| Net change in debt securities |  |  |  |  | 52 | 52 |
| Net change in debit valuation adjustments |  |  |  |  | (401) | (401) |
| Net change in derivatives |  |  |  |  | (751) | (751) |
| Employee benefit plan adjustments |  |  |  |  | 36 | 36 |
| Net change in foreign currency translation adjustments |  |  |  |  | 9 | 9 |
| Dividends declared: |  |  |  |  |  |  |
| Common |  |  |  | (1,993) |  | (1,993) |
| Preferred |  |  |  | (326) |  | (326) |
| Common stock issued under employee plans, net, and other |  | 0.3 | 732 |  |  | 732 |
| Common stock repurchased |  | (112.2) | (6,006) |  |  | (6,006) |
| Balance, June 30, 2026 | $24,996 | 7,018.0 | $13,611 | $274,520 | $(12,033) | $301,094 |
| Balance, December 31, 2025 | $25,992 | 7,212.5 | $26,084 | $261,693 | $(10,526) | $303,243 |
```

- xbrl_0038: 300668 in non-gold 0000070858-26-000249:68.1:68.1 [Bank of America Corporation (BAC) | 10-Q | Q1 FY2026 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations] | | Total shareholders’ equity | 300,668 | 303,243 |

## xbrl_0039

- Question: What was the balance of Bank of America's allowance for credit losses on loans on December 31, 2025?
- Reference answer: $13,203 million as of December 31, 2025.
- Accessions: 0000070858-26-000157, 0000070858-26-000249, 0000070858-26-000394
- xbrl_fact_id: 40203
- tags: BAC, credit_loss_allowance, FY2025, 10-K, instant, template:ins_balance, unit_scale_millions

### 0000070858-26-000157:1223.0:1223.0

```
[Bank of America Corporation (BAC) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data Table of Contents]
[Table: Consolidated Balance Sheet | Bank of America Corporation | FY2025 10-K | Item 8 | in millions, USD]
|  |  | December 31 2025 | December 31 2024 |
|---|---|---|---|
|  | Assets |  |  |
|  | Cash and due from banks | $28,595 | $26,003 |
|  | Interest-bearing deposits with the Federal Reserve, non-U.S. central banks and other banks | 203,250 | 264,111 |
|  | Cash and cash equivalents | 231,845 | 290,114 |
|  | Time deposits placed and other short-term investments | 7,474 | 6,372 |
|  | Federal funds sold and securities borrowed or purchased under agreements to resell (includes $185,491 and $144,501 measured at fair value) | 316,578 | 274,709 |
|  | Trading account assets (includes $185,869 and $170,328 pledged as collateral) | 366,954 | 314,460 |
|  | Derivative assets | 40,881 | 40,948 |
|  | Debt securities: |  |  |
|  | Carried at fair value | 402,975 | 358,607 |
|  | Held-to-maturity, at cost (fair value $442,430 and $450,548) | 522,660 | 558,677 |
|  | Total debt securities | 925,635 | 917,284 |
|  | Loans and leases (includes $3,498 and $4,249 measured at fair value) | 1,185,700 | 1,095,835 |
|  | Allowance for loan and lease losses | (13,203) | (13,240) |
|  | Loans and leases, net of allowance | 1,172,497 | 1,082,595 |
|  | Premises and equipment, net | 12,516 | 12,168 |
|  | Goodwill | 69,021 | 69,021 |
```

### 0000070858-26-000157:1617.0:1617.0

```
[Bank of America Corporation (BAC) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data Table of Contents]
[Table | Bank of America Corporation | FY2025 10-K | Item 8 | in millions, USD]
|  | Consumer Real Estate Credit Card and Other Consumer Commercial Total 2025 |
|---|---|
| Allowance for loan and lease losses, January 1 | $293 $8,277 $4,670 $13,240 |
| Loans and leases charged off | (40) (5,127) (1,684) (6,851) |
| Recoveries of loans and leases previously charged off | 82 937 201 1,220 |
| Net charge-offs | 42 (4,190) (1,483) (5,631) |
| Provision for loan and lease losses | 77 3,879 1,639 5,595 |
| Other | 4 (2) (3) (1) |
| Allowance for loan and lease losses, December 31 | 416 7,964 4,823 13,203 |
| Reserve for unfunded lending commitments, January 1 | 57 — 1,039 1,096 |
| Provision for unfunded lending commitments | 5 — 75 80 |
| Other | — — 1 1 |
| Reserve for unfunded lending commitments, December 31 | 62 — 1,115 1,177 |
| Allowance for credit losses, December 31 | $478 $7,964 $5,938 $14,380 |
|  | 2024 |
| Allowance for loan and lease losses, January 1 | $386 $8,134 $4,822 $13,342 |
| Loans and leases charged off | (42) (5,077) (1,935) (7,054) |
| Recoveries of loans and leases previously charged off | 83 798 142 1,023 |
| Net charge-offs | 41 (4,279) (1,793) (6,031) |
| Provision for loan and lease losses | (135) 4,421 1,649 5,935 |
| Other | 1 1 (8) (6) |
| Allowance for loan and lease losses, December 31 | 293 8,277 4,670 13,240 |
```

### 0000070858-26-000249:600.0:600.0

```
[Bank of America Corporation (BAC) | 10-Q | Q1 FY2026 | Part I, Item 1: Financial Statements]
[Table: Consolidated Balance Sheet | Bank of America Corporation | Q1 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  |  | March 31 2026 | December 31 2025 |
|---|---|---|---|
|  | Assets |  |  |
|  | Cash and due from banks | $27,125 | $28,595 |
|  | Interest-bearing deposits with the Federal Reserve, non-U.S. central banks and other banks | 215,354 | 203,250 |
|  | Cash and cash equivalents | 242,479 | 231,845 |
|  | Time deposits placed and other short-term investments | 7,386 | 7,474 |
|  | Federal funds sold and securities borrowed or purchased under agreements to resell (includes $228,013 and $185,491 measured at fair value) | 383,264 | 316,578 |
|  | Trading account assets (includes $185,980 and $185,869 pledged as collateral) | 364,221 | 366,954 |
|  | Derivative assets | 48,315 | 40,881 |
|  | Debt securities: |  |  |
|  | Carried at fair value | 386,389 | 402,975 |
|  | Held-to-maturity, at amortized cost (fair value $433,611 and $442,430) | 514,738 | 522,660 |
|  | Total debt securities | 901,127 | 925,635 |
|  | Loans and leases (includes $3,757 and $3,498 measured at fair value) | 1,205,035 | 1,185,700 |
|  | Allowance for loan and lease losses | (13,148) | (13,203) |
|  | Loans and leases, net of allowance | 1,191,887 | 1,172,497 |
|  | Premises and equipment, net | 12,539 | 12,516 |
|  | Goodwill | 69,021 | 69,021 |
```

### 0000070858-26-000249:838.0:838.0

```
[Bank of America Corporation (BAC) | 10-Q | Q1 FY2026 | Part I, Item 1: Financial Statements]
[Table | Bank of America Corporation | Q1 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Consumer Real Estate Three Months Ended March 31, 2026 | Credit Card and Other Consumer Three Months Ended March 31, 2026 | Commercial Three Months Ended March 31, 2026 | Total Three Months Ended March 31, 2026 |
|---|---|---|---|---|
| Allowance for loan and lease losses, January 1 | $416 | $7,964 | $4,823 | $13,203 |
| Loans and leases charged off | (16) | (1,316) | (405) | (1,737) |
| Recoveries of loans and leases previously charged off | 18 | 255 | 55 | 328 |
| Net charge-offs | 2 | (1,061) | (350) | (1,409) |
| Provision for loan and lease losses | (1) | 950 | 404 | 1,353 |
| Other | — | 1 | — | 1 |
| Allowance for loan and lease losses, March 31 | 417 | 7,854 | 4,877 | 13,148 |
| Reserve for unfunded lending commitments, January 1 | 62 | — | 1,115 | 1,177 |
| Provision for unfunded lending commitments | 13 | — | (29) | (16) |
| Reserve for unfunded lending commitments, March 31 | 75 | — | 1,086 | 1,161 |
| Allowance for credit losses, March 31 | $492 | $7,854 | $5,963 | $14,309 |
|  | Three Months Ended March 31, 2025 |  |  |  |
| Allowance for loan and lease losses, January 1 | $293 | $8,277 | $4,670 | $13,240 |
| Loans and leases charged off | (6) | (1,349) | (378) | (1,733) |
| Recoveries of loans and leases previously charged off | 18 | 218 | 45 | 281 |
```

### 0000070858-26-000394:653.0:653.0

```
[Bank of America Corporation (BAC) | 10-Q | Q2 FY2026 | Part I, Item 1: Financial Statements]
[Table: Consolidated Balance Sheet | Bank of America Corporation | Q2 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  |  | June 30 2026 | December 31 2025 |
|---|---|---|---|
|  | Assets |  |  |
|  | Cash and due from banks | $28,100 | $28,595 |
|  | Interest-bearing deposits with the Federal Reserve, non-U.S. central banks and other banks | 201,645 | 203,250 |
|  | Cash and cash equivalents | 229,745 | 231,845 |
|  | Time deposits placed and other short-term investments | 9,447 | 7,474 |
|  | Federal funds sold and securities borrowed or purchased under agreements to resell (includes $217,206 and $185,491 measured at fair value) | 412,415 | 316,578 |
|  | Trading account assets (includes $178,949 and $185,869 pledged as collateral) | 358,748 | 366,954 |
|  | Derivative assets | 45,336 | 40,881 |
|  | Debt securities: |  |  |
|  | Carried at fair value | 363,419 | 402,975 |
|  | Held-to-maturity, at amortized cost (fair value $423,734 and $442,430) | 505,799 | 522,660 |
|  | Total debt securities | 869,218 | 925,635 |
|  | Loans and leases (includes $3,359 and $3,498 measured at fair value) | 1,217,619 | 1,185,700 |
|  | Allowance for loan and lease losses | (13,114) | (13,203) |
|  | Loans and leases, net of allowance | 1,204,505 | 1,172,497 |
|  | Premises and equipment, net | 12,788 | 12,516 |
|  | Goodwill | 69,021 | 69,021 |
```

### 0000070858-26-000394:894.1:894.1

```
[Bank of America Corporation (BAC) | 10-Q | Q2 FY2026 | Part I, Item 1: Financial Statements]
[Table | Bank of America Corporation | Q2 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Consumer Real Estate Three Months Ended June 30, 2026 | Credit Card and Other Consumer Three Months Ended June 30, 2026 | Commercial Three Months Ended June 30, 2026 | Total Three Months Ended June 30, 2026 |
|---|---|---|---|---|
| Net charge-offs | 8 | (1,067) | (466) | (1,525) |
| Provision for loan and lease losses | (3) | 1,087 | 476 | 1,560 |
| Other | 1 | — | (1) | — |
| Allowance for loan and lease losses, June 30 | 346 | 8,232 | 4,713 | 13,291 |
| Reserve for unfunded lending commitments, April 1 | 57 | — | 1,053 | 1,110 |
| Provision for unfunded lending commitments | 1 | — | 31 | 32 |
| Other | — | — | 1 | 1 |
| Reserve for unfunded lending commitments, June 30 | 58 | — | 1,085 | 1,143 |
| Allowance for credit losses, June 30 | $404 | $8,232 | $5,798 | $14,434 |
| (Dollars in millions) | Six Months Ended June 30, 2026 |  |  |  |
| Allowance for loan and lease losses, January 1 | $416 | $7,964 | $4,823 | $13,203 |
| Loans and leases charged off | (32) | (2,630) | (815) | (3,477) |
| Recoveries of loans and leases previously charged off | 39 | 524 | 93 | 656 |
| Net charge-offs | 7 | (2,106) | (722) | (2,821) |
| Provision for loan and lease losses | 19 | 1,946 | 765 | 2,730 |
| Other | (1) | 1 | 2 | 2 |
```

- xbrl_0039: 13203 in non-gold 0000070858-26-000157:1002.1:1002.1 [Bank of America Corporation (BAC) | 10-K | FY2025 | Item 7: Bank of America Corporation and Subsidiaries Management's Discussion and Analysis of Financial Condition and Results of Operations Table of Contents] | | Allowance for loan and lease losses | 13,203 | 100.00% | 1.12 | 13,240 | 100.00% | 1.21 |
- xbrl_0039: 13203 in non-gold 0000070858-26-000157:1010.1:1010.1 [Bank of America Corporation (BAC) | 10-K | FY2025 | Item 7: Bank of America Corporation and Subsidiaries Management's Discussion and Analysis of Financial Condition and Results of Operations Table of Contents] | | Allowance for loan and lease losses, December 31 | 13,203 | 13,240 |

## xbrl_0048

- Question: Costco net cash provided by operating activities, fiscal 2023: what was the figure?
- Reference answer: $11,068 million for the fiscal year ended September 3, 2023.
- Accessions: 0000909832-23-000042, 0000909832-24-000049, 0000909832-25-000101
- xbrl_fact_id: 9757
- tags: COST, operating_cash_flow, FY2023, 10-K, annual, template:dur_figure, unit_scale_millions

### 0000909832-23-000042:439.0:439.0

```
[COSTCO WHOLESALE CORP /NEW (COST) | 10-K | FY2023 | Item 8: Financial Statements and Supplementary Data]
[Table: CONSOLIDATED STATEMENTS OF CASH FLOWS | COSTCO WHOLESALE CORP /NEW | FY2023 10-K | Item 8 | in millions, USD]
|  | 53 Weeks Ended September 3, 2023 | 52 Weeks Ended August 28, 2022 | 52 Weeks Ended August 29, 2021 |
|---|---|---|---|
| CASH FLOWS FROM OPERATING ACTIVITIES |  |  |  |
| Net income including noncontrolling interests | $6,292 | $5,915 | $5,079 |
| Adjustments to reconcile net income including noncontrolling interests to net cash provided by operating activities: |  |  |  |
| Depreciation and amortization | 2,077 | 1,900 | 1,781 |
| Non-cash lease expense | 412 | 377 | 286 |
| Stock-based compensation | 774 | 724 | 665 |
| Impairment of assets and other non-cash operating activities, net | 495 | 39 | 144 |
| Changes in operating assets and liabilities: |  |  |  |
| Merchandise inventories | 1,228 | (4,003) | (1,892) |
| Accounts payable | (382) | 1,891 | 1,838 |
| Other operating assets and liabilities, net | 172 | 549 | 1,057 |
| Net cash provided by operating activities | 11,068 | 7,392 | 8,958 |
| CASH FLOWS FROM INVESTING ACTIVITIES |  |  |  |
| Purchases of short-term investments | (1,622) | (1,121) | (1,331) |
| Maturities and sales of short-term investments | 937 | 1,145 | 1,446 |
| Additions to property and equipment | (4,323) | (3,891) | (3,588) |
| Other investing activities, net | 36 | (48) | (62) |
| Net cash used in investing activities | (4,972) | (3,915) | (3,535) |
| CASH FLOWS FROM FINANCING ACTIVITIES |  |  |  |
```

### 0000909832-24-000049:458.0:458.0

```
[COSTCO WHOLESALE CORP /NEW (COST) | 10-K | FY2024 | Item 8: Financial Statements and Supplementary Data]
[Table: CONSOLIDATED STATEMENTS OF CASH FLOWS | COSTCO WHOLESALE CORP /NEW | FY2024 10-K | Item 8 | in millions, USD]
|  | 52 Weeks Ended September 1, 2024 | 53 Weeks Ended September 3, 2023 | 52 Weeks Ended August 28, 2022 |
|---|---|---|---|
| CASH FLOWS FROM OPERATING ACTIVITIES |  |  |  |
| Net income including noncontrolling interests | $7,367 | $6,292 | $5,915 |
| Adjustments to reconcile net income including noncontrolling interests to net cash provided by operating activities: |  |  |  |
| Depreciation and amortization | 2,237 | 2,077 | 1,900 |
| Non-cash lease expense | 315 | 412 | 377 |
| Stock-based compensation | 818 | 774 | 724 |
| Impairment of assets and other non-cash operating activities, net | (9) | 495 | 39 |
| Changes in operating assets and liabilities: |  |  |  |
| Merchandise inventories | (2,068) | 1,228 | (4,003) |
| Accounts payable | 1,938 | (382) | 1,891 |
| Other operating assets and liabilities, net | 741 | 172 | 549 |
| Net cash provided by operating activities | 11,339 | 11,068 | 7,392 |
| CASH FLOWS FROM INVESTING ACTIVITIES |  |  |  |
| Purchases of short-term investments | (1,470) | (1,622) | (1,121) |
| Maturities and sales of short-term investments | 1,790 | 937 | 1,145 |
| Additions to property and equipment | (4,710) | (4,323) | (3,891) |
| Other investing activities, net | (19) | 36 | (48) |
| Net cash used in investing activities | (4,409) | (4,972) | (3,915) |
| CASH FLOWS FROM FINANCING ACTIVITIES |  |  |  |
```

### 0000909832-25-000101:467.0:467.0

```
[COSTCO WHOLESALE CORP /NEW (COST) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data]
[Table: CONSOLIDATED STATEMENTS OF CASH FLOWS | COSTCO WHOLESALE CORP /NEW | FY2025 10-K | Item 8 | in millions, USD]
|  | 52 Weeks Ended August 31, 2025 | 52 Weeks Ended September 1, 2024 | 53 Weeks Ended September 3, 2023 |
|---|---|---|---|
| CASH FLOWS FROM OPERATING ACTIVITIES |  |  |  |
| Net income | $8,099 | $7,367 | $6,292 |
| Adjustments to reconcile net income to net cash provided by operating activities: |  |  |  |
| Depreciation and amortization | 2,426 | 2,237 | 2,077 |
| Non-cash lease expense | 303 | 315 | 412 |
| Stock-based compensation | 860 | 818 | 774 |
| Impairment of assets and other non-cash operating activities, net | (117) | (9) | 495 |
| Changes in operating assets and liabilities: |  |  |  |
| Merchandise inventories | 559 | (2,068) | 1,228 |
| Accounts payable | 404 | 1,938 | (382) |
| Other operating assets and liabilities, net | 801 | 741 | 172 |
| Net cash provided by operating activities | 13,335 | 11,339 | 11,068 |
| CASH FLOWS FROM INVESTING ACTIVITIES |  |  |  |
| Additions to property and equipment | (5,498) | (4,710) | (4,323) |
| Purchases of short-term investments | (1,028) | (1,470) | (1,622) |
| Maturities of short-term investments | 1,141 | 1,790 | 937 |
| Other investing activities, net | 74 | (19) | 36 |
| Net cash used in investing activities | (5,311) | (4,409) | (4,972) |
| CASH FLOWS FROM FINANCING ACTIVITIES |  |  |  |
| Repayments of short-term borrowings | (862) | (920) | (935) |
```

- xbrl_0048: 11068 in non-gold 0000909832-25-000101:336.0:336.0 [COSTCO WHOLESALE CORP /NEW (COST) | 10-K | FY2025 | Item 7: Management's Discussion and Analysis of Financial Condition and Results of Operations (amounts in millions, except per share, share, percentages and warehouse count data)] | | Net cash provided by operating activities | $13,335 | $11,339 | $11,068 |
- xbrl_0048: 11068 in non-gold 0000909832-23-000042:307.0:307.0 [COSTCO WHOLESALE CORP /NEW (COST) | 10-K | FY2023 | Item 7: Management's Discussion and Analysis of Financial Conditions and Results of Operations (amounts in millions, except per share, share, membership fee, and warehouse count data)] | | Net cash provided by operating activities | $11,068 | $7,392 | $8,958 |
- xbrl_0048: 11068 in non-gold 0000909832-24-000049:329.0:329.0 [COSTCO WHOLESALE CORP /NEW (COST) | 10-K | FY2024 | Item 7: Management's Discussion and Analysis of Financial Conditions and Results of Operations (amounts in millions, except per share, share, membership fee, and warehouse count data)] | | Net cash provided by operating activities | $11,339 | $11,068 | $7,392 |

## xbrl_0063

- Question: According to its 10-Q for the second quarter of fiscal 2026, what figure did JPMorgan Chase report for noninterest expense in the three months ended June 30, 2026?
- Reference answer: $27,316 million for the three months ended June 30, 2026.
- Accessions: 0001628280-26-054343
- xbrl_fact_id: 29515
- tags: JPM, noninterest_expense, FY2026, 10-Q, quarter, template:dur_filing, unit_scale_millions

### 0001628280-26-054343:1146.1:1146.1

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q2 FY2026 | Part I, Item 1: Financial Statements]
[Table: Consolidated statements of income (unaudited) | JPMorgan Chase & Co | Q2 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Three months ended June 30, 2026 | Three months ended June 30, 2025 | Six months ended June 30, 2026 | Six months ended June 30, 2025 |
|---|---|---|---|---|
| Noninterest expense |  |  |  |  |
| Compensation expense | 15,159 | 13,710 | 30,498 | 27,803 |
| Occupancy expense | 1,482 | 1,264 | 2,929 | 2,566 |
| Technology, communications and equipment expense | 3,107 | 2,704 | 6,128 | 5,282 |
| Professional and outside services | 3,855 | 3,006 | 7,338 | 5,845 |
| Marketing | 1,670 | 1,279 | 3,274 | 2,583 |
| Other expense | 2,043 | 1,816 | 3,999 | 3,297 |
| Total noninterest expense | 27,316 | 23,779 | 54,166 | 47,376 |
| Income before income tax expense | 27,516 | 18,284 | 47,995 | 36,692 |
| Income tax expense | 6,361 | 3,297 | 10,346 | 7,062 |
| Net income | $21,155 | $14,987 | $37,649 | $29,630 |
| Net income applicable to common stockholders | $20,752 | $14,630 | $36,901 | $28,948 |
| Net income per common share data |  |  |  |  |
| Basic earnings per share | $7.71 | $5.25 | $13.65 | $10.32 |
| Diluted earnings per share | 7.70 | 5.24 | 13.63 | 10.31 |
```

### 0001628280-26-054343:2102.0:2102.0

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q2 FY2026 | Part I, Item 1: Financial Statements]
[Table: As of or for the three months ended June 30, | JPMorgan Chase & Co | Q2 FY2026 10-Q | Part I, Item 1 | in millions, USD]
| As of or for the three months ended June 30, (in millions, except ratios) | Corporate 2026 | Corporate | Corporate 2025 |  | Reconciling Items(a) 2026 | Reconciling Items(a) 2025 | Total 2026 | Total 2025 |
|---|---|---|---|---|---|---|---|---|
| Noninterest revenue | $5,224 | (e) | $49 |  | $(564) | $(663) | $31,836 | $21,703 |
| Net interest income | 822 |  | 1,489 |  | (111) | (105) | 25,511 | 23,209 |
| Total net revenue | 6,046 |  | 1,538 |  | (675) | (768) | 57,347 | 44,912 |
| Provision for credit losses | (10) |  | 25 |  | — | — | 2,515 | 2,849 |
| Total noninterest expense(d) | 611 |  | 547 | (f) | — | — | 27,316 | 23,779 |
| Income/(loss) before income tax expense/(benefit) | 5,445 |  | 966 |  | (675) | (768) | 27,516 | 18,284 |
| Income tax expense/(benefit) | 1,236 |  | (729) |  | (675) | (768) | 6,361 | 3,297 |
| Net income | $4,209 |  | $1,695 |  | $— | $— | $21,155 | $14,987 |
| Average equity | $93,448 |  | $108,297 |  | NA | NA | $343,146 | $329,797 |
```

- xbrl_0063: 27316 in non-gold 0001628280-26-054343:189.0:189.0 [JPMorgan Chase & Co (JPM) | 10-Q | Q2 FY2026 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations.] | | Total noninterest expense | $27,316 | $23,779 | 15% | $54,166 | $47,376 | 14% |

## xbrl_0066

- Question: How much net interest income did JPMorgan Chase report for the three months ended June 30, 2026?
- Reference answer: $25,511 million for the three months ended June 30, 2026.
- Accessions: 0001628280-26-054343
- xbrl_fact_id: 28611
- tags: JPM, net_interest_income, FY2026, 10-Q, quarter, template:dur_how_much, unit_scale_millions

### 0001628280-26-054343:1146.0:1146.0

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q2 FY2026 | Part I, Item 1: Financial Statements]
[Table: Consolidated statements of income (unaudited) | JPMorgan Chase & Co | Q2 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Three months ended June 30, 2026 | Three months ended June 30, 2025 | Six months ended June 30, 2026 | Six months ended June 30, 2025 |
|---|---|---|---|---|
| Revenue |  |  |  |  |
| Investment banking fees | $3,208 | $2,499 | $6,066 | $4,677 |
| Principal transactions | 9,007 | 7,149 | 16,994 | 14,763 |
| Lending- and deposit-related fees | 2,511 | 2,248 | 4,905 | 4,380 |
| Asset management fees | 5,658 | 4,806 | 11,173 | 9,506 |
| Commissions and other fees | 2,614 | 2,194 | 5,096 | 4,227 |
| Investment securities losses | (395) | (54) | (331) | (91) |
| Mortgage fees and related income | 336 | 363 | 645 | 641 |
| Card income | 1,348 | 1,344 | 2,538 | 2,560 |
| Other income | 7,549 | 1,154 | 9,220 | 3,077 |
| Noninterest revenue | 31,836 | 21,703 | 56,306 | 43,740 |
| Interest income | 50,624 | 48,241 | 99,815 | 95,094 |
| Interest expense | 25,113 | 25,032 | 48,938 | 48,612 |
| Net interest income | 25,511 | 23,209 | 50,877 | 46,482 |
| Total net revenue | 57,347 | 44,912 | 107,183 | 90,222 |
| Provision for credit losses | 2,515 | 2,849 | 5,022 | 6,154 |
```

### 0001628280-26-054343:1505.1:1505.1

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q2 FY2026 | Part I, Item 1: Financial Statements]
[Table | JPMorgan Chase & Co | Q2 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Three months ended June 30, 2026 | Three months ended June 30, 2025 | Six months ended June 30, 2026 | Six months ended June 30, 2025 |
|---|---|---|---|---|
| Trading liabilities – debt and all other interest-bearing liabilities(d) | 2,415 | 2,278 | 4,678 | 4,369 |
| Long-term debt | 4,468 | 4,484 | 8,810 | 8,876 |
| Beneficial interest issued by consolidated VIEs | 275 | 297 | 541 | 593 |
| Total interest expense | $25,113 | $25,032 | $48,938 | $48,612 |
| Net interest income | $25,511 | $23,209 | $50,877 | $46,482 |
| Provision for credit losses | 2,515 | 2,849 | 5,022 | 6,154 |
| Net interest income after provision for credit losses | $22,996 | $20,360 | $45,855 | $40,328 |
```

### 0001628280-26-054343:2102.0:2102.0

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q2 FY2026 | Part I, Item 1: Financial Statements]
[Table: As of or for the three months ended June 30, | JPMorgan Chase & Co | Q2 FY2026 10-Q | Part I, Item 1 | in millions, USD]
| As of or for the three months ended June 30, (in millions, except ratios) | Corporate 2026 | Corporate | Corporate 2025 |  | Reconciling Items(a) 2026 | Reconciling Items(a) 2025 | Total 2026 | Total 2025 |
|---|---|---|---|---|---|---|---|---|
| Noninterest revenue | $5,224 | (e) | $49 |  | $(564) | $(663) | $31,836 | $21,703 |
| Net interest income | 822 |  | 1,489 |  | (111) | (105) | 25,511 | 23,209 |
| Total net revenue | 6,046 |  | 1,538 |  | (675) | (768) | 57,347 | 44,912 |
| Provision for credit losses | (10) |  | 25 |  | — | — | 2,515 | 2,849 |
| Total noninterest expense(d) | 611 |  | 547 | (f) | — | — | 27,316 | 23,779 |
| Income/(loss) before income tax expense/(benefit) | 5,445 |  | 966 |  | (675) | (768) | 27,516 | 18,284 |
| Income tax expense/(benefit) | 1,236 |  | (729) |  | (675) | (768) | 6,361 | 3,297 |
| Net income | $4,209 |  | $1,695 |  | $— | $— | $21,155 | $14,987 |
| Average equity | $93,448 |  | $108,297 |  | NA | NA | $343,146 | $329,797 |
```

- xbrl_0066: 25511 in non-gold 0001628280-26-054343:114.1:114.1 [JPMorgan Chase & Co (JPM) | 10-Q | Q2 FY2026 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations.] | | Net interest income | 25,511 |  | 23,209 | 10 | 50,877 |  | 46,482 | 9 |

## xbrl_0069

- Question: How much income tax expense did JPMorgan Chase report for the three months ended September 30, 2024?
- Reference answer: $4,080 million for the three months ended September 30, 2024.
- Accessions: 0000019617-24-000611, 0001628280-25-048859
- xbrl_fact_id: 27918
- tags: JPM, income_tax, FY2024, 10-Q, quarter, template:dur_how_much, unit_scale_millions

### 0000019617-24-000611:1259.1:1259.1

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2024 | Part I, Item 1: Financial Statements.]
[Table: Consolidated statements of income (unaudited) | JPMorgan Chase & Co | Q3 FY2024 10-Q | Part I, Item 1 | in millions, USD]
|  | Three months ended September 30, 2024 | Three months ended September 30, 2023 | Nine months ended September 30, 2024 | Nine months ended September 30, 2023 |
|---|---|---|---|---|
| Noninterest expense |  |  |  |  |
| Compensation expense | 12,817 | 11,726 | 38,888 | 34,618 |
| Occupancy expense | 1,258 | 1,197 | 3,717 | 3,382 |
| Technology, communications and equipment expense | 2,447 | 2,386 | 7,315 | 6,837 |
| Professional and outside services | 2,780 | 2,620 | 8,050 | 7,629 |
| Marketing | 1,258 | 1,126 | 3,639 | 3,293 |
| Other expense | 2,005 | 2,702 | 7,426 | 6,927 |
| Total noninterest expense | 22,565 | 21,757 | 69,035 | 62,686 |
| Income before income tax expense | 16,978 | 16,733 | 57,706 | 50,286 |
| Income tax expense | 4,080 | 3,582 | 13,240 | 10,041 |
| Net income | $12,898 | $13,151 | $44,466 | $40,245 |
| Net income applicable to common stockholders | $12,537 | $12,685 | $43,199 | $38,889 |
| Net income per common share data |  |  |  |  |
| Basic earnings per share | $4.38 | $4.33 | $14.97 | $13.20 |
| Diluted earnings per share | 4.37 | 4.33 | 14.94 | 13.18 |
```

### 0000019617-24-000611:2236.0:2236.0

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2024 | Part I, Item 1: Financial Statements.]
[Table: As of or for the three months ended September 30, | JPMorgan Chase & Co | Q3 FY2024 10-Q | Part I, Item 1 | in millions, USD]
| As of or for the three months ended September 30, (in millions, except ratios) | Corporate 2024 | Corporate 2023 | Reconciling Items(a) 2024 | Reconciling Items(a) 2023 | Total 2024 | Total 2023 |
|---|---|---|---|---|---|---|
| Noninterest revenue | $155 | $(425) | $(541) | $(682) | $19,249 | $17,148 |
| Net interest income | 2,915 | 1,983 | (120) | (130) | 23,405 | 22,726 |
| Total net revenue | 3,070 | 1,558 | (661) | (812) | 42,654 | 39,874 |
| Provision for credit losses | (4) | 46 | — | — | 3,111 | 1,384 |
| Noninterest expense | 589 | 696 | — | — | 22,565 | 21,757 |
| Income/(loss) before income tax expense/(benefit) | 2,485 | 816 | (661) | (812) | 16,978 | 16,733 |
| Income tax expense/(benefit) | 675 | 4 | (661) | (812) | 4,080 | 3,582 |
| Net income/(loss) | $1,810 | $812 | $— | $— | $12,898 | $13,151 |
| Average equity | $119,894 | $74,298 | $— | $— | $321,894 | $284,798 |
| Total assets | 1,276,238 | 1,275,673 | NA | NA | 4,210,048 | 3,898,333 |
```

### 0001628280-25-048859:1192.1:1192.1

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2025 | Part I, Item 1: Financial Statements]
[Table: Consolidated statements of income (unaudited) | JPMorgan Chase & Co | Q3 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | Three months ended September 30, 2025 | Three months ended September 30, 2024 | Nine months ended September 30, 2025 | Nine months ended September 30, 2024 |
|---|---|---|---|---|
| Noninterest expense |  |  |  |  |
| Compensation expense | 13,566 | 12,817 | 41,369 | 38,888 |
| Occupancy expense | 1,420 | 1,258 | 3,986 | 3,717 |
| Technology, communications and equipment expense | 2,839 | 2,447 | 8,121 | 7,315 |
| Professional and outside services | 3,173 | 2,780 | 9,018 | 8,050 |
| Marketing | 1,480 | 1,258 | 4,063 | 3,639 |
| Other expense | 1,803 | 2,005 | 5,100 | 7,426 |
| Total noninterest expense | 24,281 | 22,565 | 71,657 | 69,035 |
| Income before income tax expense | 18,743 | 16,978 | 55,435 | 57,706 |
| Income tax expense | 4,350 | 4,080 | 11,412 | 13,240 |
| Net income | $14,393 | $12,898 | $44,023 | $44,466 |
| Net income applicable to common stockholders | $14,043 | $12,537 | $42,991 | $43,199 |
| Net income per common share data |  |  |  |  |
| Basic earnings per share | $5.08 | $4.38 | $15.41 | $14.97 |
| Diluted earnings per share | 5.07 | 4.37 | 15.38 | 14.94 |
```

### 0001628280-25-048859:2170.0:2170.0

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2025 | Part I, Item 1: Financial Statements]
[Table: As of or for the three months ended September 30, | JPMorgan Chase & Co | Q3 FY2025 10-Q | Part I, Item 1 | in millions, USD]
| As of or for the three months ended September 30, (in millions, except ratios) | Corporate 2025 | Corporate 2024 | Reconciling Items(a) 2025 | Reconciling Items(a) 2024 | Total 2025 | Total 2024 |
|---|---|---|---|---|---|---|
| Noninterest revenue | $297 | $155 | $(588) | $(541) | $22,461 | $19,249 |
| Net interest income | 1,406 | 2,915 | (105) | (120) | 23,966 | 23,405 |
| Total net revenue | 1,703 | 3,070 | (693) | (661) | 46,427 | 42,654 |
| Provision for credit losses | (3) | (4) | — | — | 3,403 | 3,111 |
| Total noninterest expense(d) | 445 | 589 | — | — | 24,281 | 22,565 |
| Income/(loss) before income tax expense/(benefit) | 1,261 | 2,485 | (693) | (661) | 18,743 | 16,978 |
| Income tax expense/(benefit) | 436 | 675 | (693) | (661) | 4,350 | 4,080 |
| Net income | $825 | $1,810 | $— | $— | $14,393 | $12,898 |
| Average equity | $114,835 | $119,894 | NA | NA | $336,335 | $321,894 |
| Total assets | 1,297,608 | 1,276,238 | NA | NA | 4,560,205 | 4,210,048 |
```

- xbrl_0069: 4080 in non-gold 0000019617-24-000611:237.0:237.0 [JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2024 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations.] | | Income tax expense | 4,080 (a) | 3,582 | 14 | 13,240 (a) | 10,041 | 32 |
- xbrl_0069: 4080 in non-gold 0001628280-25-048859:222.0:222.0 [JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2025 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations.] | | Income tax expense | 4,350 | 4,080 | 7 | 11,412 | 13,240 | (14) |

## xbrl_0072

- Question: How much income before income taxes did JPMorgan Chase report for the nine months ended September 30, 2025?
- Reference answer: $55,435 million for the nine months ended September 30, 2025.
- Accessions: 0001628280-25-048859
- xbrl_fact_id: 27865
- tags: JPM, pretax_income, FY2025, 10-Q, ytd, template:dur_how_much, unit_scale_millions

### 0001628280-25-048859:1192.1:1192.1

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2025 | Part I, Item 1: Financial Statements]
[Table: Consolidated statements of income (unaudited) | JPMorgan Chase & Co | Q3 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | Three months ended September 30, 2025 | Three months ended September 30, 2024 | Nine months ended September 30, 2025 | Nine months ended September 30, 2024 |
|---|---|---|---|---|
| Noninterest expense |  |  |  |  |
| Compensation expense | 13,566 | 12,817 | 41,369 | 38,888 |
| Occupancy expense | 1,420 | 1,258 | 3,986 | 3,717 |
| Technology, communications and equipment expense | 2,839 | 2,447 | 8,121 | 7,315 |
| Professional and outside services | 3,173 | 2,780 | 9,018 | 8,050 |
| Marketing | 1,480 | 1,258 | 4,063 | 3,639 |
| Other expense | 1,803 | 2,005 | 5,100 | 7,426 |
| Total noninterest expense | 24,281 | 22,565 | 71,657 | 69,035 |
| Income before income tax expense | 18,743 | 16,978 | 55,435 | 57,706 |
| Income tax expense | 4,350 | 4,080 | 11,412 | 13,240 |
| Net income | $14,393 | $12,898 | $44,023 | $44,466 |
| Net income applicable to common stockholders | $14,043 | $12,537 | $42,991 | $43,199 |
| Net income per common share data |  |  |  |  |
| Basic earnings per share | $5.08 | $4.38 | $15.41 | $14.97 |
| Diluted earnings per share | 5.07 | 4.37 | 15.38 | 14.94 |
```

### 0001628280-25-048859:2173.0:2173.0

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2025 | Part I, Item 1: Financial Statements]
[Table: As of or for the nine months ended September 30, | JPMorgan Chase & Co | Q3 FY2025 10-Q | Part I, Item 1 | in millions, USD]
| As of or for the nine months ended September 30, (in millions, except ratios) | Corporate 2025 | Corporate | Corporate 2024 |  | Reconciling Items(a) 2025 | Reconciling Items(a) 2024 | Total 2025 | Total 2024 |  |
|---|---|---|---|---|---|---|---|---|---|
| Noninterest revenue | $999 |  | $7,638 | (f) | $(1,853) | $(1,711) | $66,201 | $65,555 | (f) |
| Net interest income | 4,546 |  | 7,756 |  | (312) | (356) | 70,448 | 69,233 |  |
| Total net revenue | 5,545 |  | 15,394 |  | (2,165) | (2,067) | 136,649 | 134,788 |  |
| Provision for credit losses | 3 |  | 28 |  | — | — | 9,557 | 8,047 |  |
| Noninterest expense | 1,177 |  | 3,444 | (g) | — | — | 71,657 | 69,035 | (g) |
| Income/(loss) before income tax expense/(benefit) | 4,365 |  | 11,922 |  | (2,165) | (2,067) | 55,435 | 57,706 |  |
| Income tax expense/(benefit) | 152 | (e) | 2,657 |  | (2,165) | (2,067) | 11,412 | 13,240 |  |
| Net income | $4,213 |  | $9,265 |  | $— | $— | $44,023 | $44,466 |  |
```

- xbrl_0072: 55435 in non-gold 0001628280-25-048859:222.0:222.0 [JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2025 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations.] | | Income before income tax expense | $18,743 | $16,978 | 10% | $55,435 | $57,706 | (4)% |

## xbrl_0075

- Question: What did JPMorgan Chase report as its total assets as of September 30, 2024?
- Reference answer: $4,210,048 million as of September 30, 2024.
- Accessions: 0000019617-24-000611, 0001628280-25-048859
- xbrl_fact_id: 24177
- tags: JPM, total_assets, FY2024, 10-Q, instant, template:ins_report, unit_scale_millions

### 0000019617-24-000611:1269.1:1269.1

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2024 | Part I, Item 1: Financial Statements.]
[Table: Consolidated balance sheets (unaudited) | JPMorgan Chase & Co | Q3 FY2024 10-Q | Part I, Item 1 | in millions, USD]
|  | September 30, 2024 | December 31, 2023 |
|---|---|---|
| Other assets (included $14,169 and $12,306 at fair value and assets pledged of $6,994 and $6,764) | 175,935 | 159,308 |
| Total assets(a) | $4,210,048 | $3,875,393 |
| Liabilities |  |  |
| Deposits (included $51,284 and $78,384 at fair value) | $2,430,772 | $2,400,688 |
| Federal funds purchased and securities loaned or sold under repurchase agreements (included $320,406 and $169,003 at fair value) | 389,337 | 216,535 |
| Short-term borrowings (included $28,307 and $20,042 at fair value) | 50,638 | 44,712 |
| Trading liabilities | 243,258 | 180,428 |
| Accounts payable and other liabilities (included $5,865 and $5,637 at fair value) | 314,356 | 290,307 |
| Beneficial interests issued by consolidated VIEs (included $1 and $1 at fair value) | 25,694 | 23,020 |
| Long-term debt (included $102,129 and $87,924 at fair value) | 410,157 | 391,825 |
| Total liabilities(a) | 3,864,212 | 3,547,515 |
| Commitments and contingencies (refer to Notes 22, 23 and 24) |  |  |
| Stockholders’ equity |  |  |
| Preferred stock ($1 par value; authorized 200,000,000 shares; issued 2,165,375 and 2,740,375 shares) | 21,650 | 27,404 |
```

### 0000019617-24-000611:2236.0:2236.0

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2024 | Part I, Item 1: Financial Statements.]
[Table: As of or for the three months ended September 30, | JPMorgan Chase & Co | Q3 FY2024 10-Q | Part I, Item 1 | in millions, USD]
| As of or for the three months ended September 30, (in millions, except ratios) | Corporate 2024 | Corporate 2023 | Reconciling Items(a) 2024 | Reconciling Items(a) 2023 | Total 2024 | Total 2023 |
|---|---|---|---|---|---|---|
| Noninterest revenue | $155 | $(425) | $(541) | $(682) | $19,249 | $17,148 |
| Net interest income | 2,915 | 1,983 | (120) | (130) | 23,405 | 22,726 |
| Total net revenue | 3,070 | 1,558 | (661) | (812) | 42,654 | 39,874 |
| Provision for credit losses | (4) | 46 | — | — | 3,111 | 1,384 |
| Noninterest expense | 589 | 696 | — | — | 22,565 | 21,757 |
| Income/(loss) before income tax expense/(benefit) | 2,485 | 816 | (661) | (812) | 16,978 | 16,733 |
| Income tax expense/(benefit) | 675 | 4 | (661) | (812) | 4,080 | 3,582 |
| Net income/(loss) | $1,810 | $812 | $— | $— | $12,898 | $13,151 |
| Average equity | $119,894 | $74,298 | $— | $— | $321,894 | $284,798 |
| Total assets | 1,276,238 | 1,275,673 | NA | NA | 4,210,048 | 3,898,333 |
```

### 0000019617-24-000611:2240.1:2240.1

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2024 | Part I, Item 1: Financial Statements.]
[Table: As of or for the nine months ended September 30, | JPMorgan Chase & Co | Q3 FY2024 10-Q | Part I, Item 1 | in millions, USD]
| As of or for the nine months ended September 30, (in millions, except ratios) | Corporate 2024 | Corporate | Corporate 2023 | Reconciling Items(a) 2024 | Reconciling Items(a) 2023 | Total 2024 | Total | Total 2023 |
|---|---|---|---|---|---|---|---|---|
| Average equity | $108,353 |  | $70,147 | $— | $— | $310,353 |  | $278,010 |
| Total assets | 1,276,238 |  | 1,275,673 | NA | NA | 4,210,048 |  | 3,898,333 |
| ROE | NM |  | NM | NM | NM | 19% |  | 19% |
| Overhead ratio | NM |  | NM | NM | NM | 51 |  | 52 |
```

### 0001628280-25-048859:2170.0:2170.0

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2025 | Part I, Item 1: Financial Statements]
[Table: As of or for the three months ended September 30, | JPMorgan Chase & Co | Q3 FY2025 10-Q | Part I, Item 1 | in millions, USD]
| As of or for the three months ended September 30, (in millions, except ratios) | Corporate 2025 | Corporate 2024 | Reconciling Items(a) 2025 | Reconciling Items(a) 2024 | Total 2025 | Total 2024 |
|---|---|---|---|---|---|---|
| Noninterest revenue | $297 | $155 | $(588) | $(541) | $22,461 | $19,249 |
| Net interest income | 1,406 | 2,915 | (105) | (120) | 23,966 | 23,405 |
| Total net revenue | 1,703 | 3,070 | (693) | (661) | 46,427 | 42,654 |
| Provision for credit losses | (3) | (4) | — | — | 3,403 | 3,111 |
| Total noninterest expense(d) | 445 | 589 | — | — | 24,281 | 22,565 |
| Income/(loss) before income tax expense/(benefit) | 1,261 | 2,485 | (693) | (661) | 18,743 | 16,978 |
| Income tax expense/(benefit) | 436 | 675 | (693) | (661) | 4,350 | 4,080 |
| Net income | $825 | $1,810 | $— | $— | $14,393 | $12,898 |
| Average equity | $114,835 | $119,894 | NA | NA | $336,335 | $321,894 |
| Total assets | 1,297,608 | 1,276,238 | NA | NA | 4,560,205 | 4,210,048 |
```

### 0001628280-25-048859:2173.1:2173.1

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2025 | Part I, Item 1: Financial Statements]
[Table: As of or for the nine months ended September 30, | JPMorgan Chase & Co | Q3 FY2025 10-Q | Part I, Item 1 | in millions, USD]
| As of or for the nine months ended September 30, (in millions, except ratios) | Corporate 2025 | Corporate | Corporate 2024 |  | Reconciling Items(a) 2025 | Reconciling Items(a) 2024 | Total 2025 | Total 2024 |  |
|---|---|---|---|---|---|---|---|---|---|
| Average equity | $108,703 |  | $108,353 |  | NA | NA | $330,203 | $310,353 |  |
| Total assets | 1,297,608 |  | 1,276,238 |  | NA | NA | 4,560,205 | 4,210,048 |  |
| ROE | NM |  | NM |  | NM | NM | 17% | 19% |  |
| Overhead ratio | NM |  | NM |  | NM | NM | 52 | 51 |  |
```

- xbrl_0075: 4210048 in non-gold 0000019617-24-000611:250.0:250.0 [JPMorgan Chase & Co (JPM) | 10-Q | Q3 FY2024 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations.] | | Total assets | $4,210,048 | $3,875,393 | 9% |

## xbrl_0079

- Question: JPMorgan Chase net interest income, the second quarter of fiscal 2025: what was the figure?
- Reference answer: $23,209 million for the three months ended June 30, 2025.
- Accessions: 0000019617-25-000615, 0001628280-26-054343
- xbrl_fact_id: 28604
- tags: JPM, net_interest_income, FY2025, 10-Q, quarter, template:dur_figure, unit_scale_millions

### 0000019617-25-000615:1187.0:1187.0

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q2 FY2025 | Part I, Item 1: Financial Statements]
[Table: Consolidated statements of income (unaudited) | JPMorgan Chase & Co | Q2 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | Three months ended June 30, 2025 | Three months ended June 30, 2024 | Six months ended June 30, 2025 | Six months ended June 30, 2024 |
|---|---|---|---|---|
| Revenue |  |  |  |  |
| Investment banking fees | $2,499 | $2,304 | $4,677 | $4,258 |
| Principal transactions | 7,149 | 6,814 | 14,763 | 13,604 |
| Lending- and deposit-related fees | 2,248 | 1,828 | 4,380 | 3,730 |
| Asset management fees | 4,806 | 4,302 | 9,506 | 8,448 |
| Commissions and other fees | 2,194 | 1,924 | 4,227 | 3,729 |
| Investment securities losses | (54) | (547) | (91) | (913) |
| Mortgage fees and related income | 363 | 348 | 641 | 623 |
| Card income | 1,344 | 1,332 | 2,560 | 2,550 |
| Other income | 1,154 | 9,149 | 3,077 | 10,277 |
| Noninterest revenue | 21,703 | 27,454 | 43,740 | 46,306 |
| Interest income | 48,241 | 48,513 | 95,094 | 95,951 |
| Interest expense | 25,032 | 25,767 | 48,612 | 50,123 |
| Net interest income | 23,209 | 22,746 | 46,482 | 45,828 |
| Total net revenue | 44,912 | 50,200 | 90,222 | 92,134 |
| Provision for credit losses | 2,849 | 3,052 | 6,154 | 4,936 |
```

### 0000019617-25-000615:1541.1:1541.1

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q2 FY2025 | Part I, Item 1: Financial Statements]
[Table | JPMorgan Chase & Co | Q2 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | Three months ended June 30, 2025 | Three months ended June 30, 2024 | Six months ended June 30, 2025 | Six months ended June 30, 2024 |
|---|---|---|---|---|
| Trading liabilities – debt and all other interest-bearing liabilities(d) | 2,278 | 2,604 | 4,369 | 5,240 |
| Long-term debt | 4,484 | 4,780 | 8,876 | 9,398 |
| Beneficial interest issued by consolidated VIEs | 297 | 352 | 593 | 716 |
| Total interest expense | $25,032 | $25,767 | $48,612 | $50,123 |
| Net interest income | $23,209 | $22,746 | $46,482 | $45,828 |
| Provision for credit losses | 2,849 | 3,052 | 6,154 | 4,936 |
| Net interest income after provision for credit losses | $20,360 | $19,694 | $40,328 | $40,892 |
```

### 0000019617-25-000615:2151.0:2151.0

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q2 FY2025 | Part I, Item 1: Financial Statements]
[Table: As of or for the three months ended June 30, | JPMorgan Chase & Co | Q2 FY2025 10-Q | Part I, Item 1 | in millions, USD]
| As of or for the three months ended June 30, (in millions, except ratios) | Corporate 2025 | Corporate | Corporate 2024 |  | Reconciling Items(a) 2025 | Reconciling Items(a) 2024 | Total 2025 | Total | Total 2024 |
|---|---|---|---|---|---|---|---|---|---|
| Noninterest revenue | $49 |  | $7,758 | (f) | $(663) | $(677) | $21,703 | (f) | $27,454 |
| Net interest income | 1,489 |  | 2,364 |  | (105) | (115) | 23,209 |  | 22,746 |
| Total net revenue | 1,538 |  | 10,122 |  | (768) | (792) | 44,912 |  | 50,200 |
| Provision for credit losses | 25 |  | 5 |  | — | — | 2,849 |  | 3,052 |
| Total noninterest expense(d) | 547 |  | 1,579 | (g) | — | — | 23,779 | (g) | 23,713 |
| Income/(loss) before income tax expense/(benefit) | 966 |  | 8,538 |  | (768) | (792) | 18,284 |  | 23,435 |
| Income tax expense/(benefit) | (729) | (e) | 1,759 |  | (768) | (792) | 3,297 |  | 5,286 |
| Net income | $1,695 |  | $6,779 |  | $— | $— | $14,987 |  | $18,149 |
```

### 0001628280-26-054343:1146.0:1146.0

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q2 FY2026 | Part I, Item 1: Financial Statements]
[Table: Consolidated statements of income (unaudited) | JPMorgan Chase & Co | Q2 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Three months ended June 30, 2026 | Three months ended June 30, 2025 | Six months ended June 30, 2026 | Six months ended June 30, 2025 |
|---|---|---|---|---|
| Revenue |  |  |  |  |
| Investment banking fees | $3,208 | $2,499 | $6,066 | $4,677 |
| Principal transactions | 9,007 | 7,149 | 16,994 | 14,763 |
| Lending- and deposit-related fees | 2,511 | 2,248 | 4,905 | 4,380 |
| Asset management fees | 5,658 | 4,806 | 11,173 | 9,506 |
| Commissions and other fees | 2,614 | 2,194 | 5,096 | 4,227 |
| Investment securities losses | (395) | (54) | (331) | (91) |
| Mortgage fees and related income | 336 | 363 | 645 | 641 |
| Card income | 1,348 | 1,344 | 2,538 | 2,560 |
| Other income | 7,549 | 1,154 | 9,220 | 3,077 |
| Noninterest revenue | 31,836 | 21,703 | 56,306 | 43,740 |
| Interest income | 50,624 | 48,241 | 99,815 | 95,094 |
| Interest expense | 25,113 | 25,032 | 48,938 | 48,612 |
| Net interest income | 25,511 | 23,209 | 50,877 | 46,482 |
| Total net revenue | 57,347 | 44,912 | 107,183 | 90,222 |
| Provision for credit losses | 2,515 | 2,849 | 5,022 | 6,154 |
```

### 0001628280-26-054343:1505.1:1505.1

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q2 FY2026 | Part I, Item 1: Financial Statements]
[Table | JPMorgan Chase & Co | Q2 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Three months ended June 30, 2026 | Three months ended June 30, 2025 | Six months ended June 30, 2026 | Six months ended June 30, 2025 |
|---|---|---|---|---|
| Trading liabilities – debt and all other interest-bearing liabilities(d) | 2,415 | 2,278 | 4,678 | 4,369 |
| Long-term debt | 4,468 | 4,484 | 8,810 | 8,876 |
| Beneficial interest issued by consolidated VIEs | 275 | 297 | 541 | 593 |
| Total interest expense | $25,113 | $25,032 | $48,938 | $48,612 |
| Net interest income | $25,511 | $23,209 | $50,877 | $46,482 |
| Provision for credit losses | 2,515 | 2,849 | 5,022 | 6,154 |
| Net interest income after provision for credit losses | $22,996 | $20,360 | $45,855 | $40,328 |
```

### 0001628280-26-054343:2102.0:2102.0

```
[JPMorgan Chase & Co (JPM) | 10-Q | Q2 FY2026 | Part I, Item 1: Financial Statements]
[Table: As of or for the three months ended June 30, | JPMorgan Chase & Co | Q2 FY2026 10-Q | Part I, Item 1 | in millions, USD]
| As of or for the three months ended June 30, (in millions, except ratios) | Corporate 2026 | Corporate | Corporate 2025 |  | Reconciling Items(a) 2026 | Reconciling Items(a) 2025 | Total 2026 | Total 2025 |
|---|---|---|---|---|---|---|---|---|
| Noninterest revenue | $5,224 | (e) | $49 |  | $(564) | $(663) | $31,836 | $21,703 |
| Net interest income | 822 |  | 1,489 |  | (111) | (105) | 25,511 | 23,209 |
| Total net revenue | 6,046 |  | 1,538 |  | (675) | (768) | 57,347 | 44,912 |
| Provision for credit losses | (10) |  | 25 |  | — | — | 2,515 | 2,849 |
| Total noninterest expense(d) | 611 |  | 547 | (f) | — | — | 27,316 | 23,779 |
| Income/(loss) before income tax expense/(benefit) | 5,445 |  | 966 |  | (675) | (768) | 27,516 | 18,284 |
| Income tax expense/(benefit) | 1,236 |  | (729) |  | (675) | (768) | 6,361 | 3,297 |
| Net income | $4,209 |  | $1,695 |  | $— | $— | $21,155 | $14,987 |
| Average equity | $93,448 |  | $108,297 |  | NA | NA | $343,146 | $329,797 |
```

- xbrl_0079: 23209 in non-gold 0000019617-25-000615:112.1:112.1 [JPMorgan Chase & Co (JPM) | 10-Q | Q2 FY2025 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations.] | | Net interest income | 23,209 | 22,746 |  | 2 | 46,482 | 45,828 |  | 1 |
- xbrl_0079: 23209 in non-gold 0000019617-25-000615:47.0:47.0 [JPMorgan Chase & Co (JPM) | 10-Q | Q2 FY2025 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations.] | | Net interest income | 23,209 | 22,746 | 2 | 46,482 | 45,828 | 1 |

## xbrl_0084

- Question: NVIDIA selling, general and administrative expense, fiscal 2025: what was the figure?
- Reference answer: $3,491 million for the fiscal year ended January 26, 2025.
- Accessions: 0001045810-25-000023, 0001045810-26-000021
- xbrl_fact_id: 48260
- tags: NVDA, sga, FY2025, 10-K, annual, template:dur_figure, unit_scale_millions

### 0001045810-25-000023:768.0:768.0

```
[NVIDIA CORP (NVDA) | 10-K | FY2025 | Item 15: Exhibits and Financial Statement Schedules]
[Table: Consolidated Statements of Income | NVIDIA CORP | FY2025 10-K | Item 15 | in millions, USD]
|  | Year Ended Jan 26, 2025 | Year Ended Jan 28, 2024 | Year Ended Jan 29, 2023 |
|---|---|---|---|
| Revenue | $130,497 | $60,922 | $26,974 |
| Cost of revenue | 32,639 | 16,621 | 11,618 |
| Gross profit | 97,858 | 44,301 | 15,356 |
| Operating expenses |  |  |  |
| Research and development | 12,914 | 8,675 | 7,339 |
| Sales, general and administrative | 3,491 | 2,654 | 2,440 |
| Acquisition termination cost | — | — | 1,353 |
| Total operating expenses | 16,405 | 11,329 | 11,132 |
| Operating income | 81,453 | 32,972 | 4,224 |
| Interest income | 1,786 | 866 | 267 |
| Interest expense | (247) | (257) | (262) |
| Other, net | 1,034 | 237 | (48) |
| Other income (expense), net | 2,573 | 846 | (43) |
| Income before income tax | 84,026 | 33,818 | 4,181 |
| Income tax expense (benefit) | 11,146 | 4,058 | (187) |
| Net income | $72,880 | $29,760 | $4,368 |
| Net income per share: |  |  |  |
| Basic | $2.97 | $1.21 | $0.18 |
| Diluted | $2.94 | $1.19 | $0.17 |
| Weighted average shares used in per share computation: |  |  |  |
| Basic | 24,555 | 24,690 | 24,870 |
| Diluted | 24,804 | 24,940 | 25,070 |
```

### 0001045810-26-000021:751.0:751.0

```
[NVIDIA CORP (NVDA) | 10-K | FY2026 | Item 15: Exhibits and Financial Statement Schedules]
[Table: Consolidated Statements of Income | NVIDIA CORP | FY2026 10-K | Item 15 | in millions, USD]
|  | Year Ended Jan 25, 2026 | Year Ended Jan 26, 2025 | Year Ended Jan 28, 2024 |
|---|---|---|---|
| Revenue | $215,938 | $130,497 | $60,922 |
| Cost of revenue | 62,475 | 32,639 | 16,621 |
| Gross profit | 153,463 | 97,858 | 44,301 |
| Operating expenses |  |  |  |
| Research and development | 18,497 | 12,914 | 8,675 |
| Sales, general and administrative | 4,579 | 3,491 | 2,654 |
| Total operating expenses | 23,076 | 16,405 | 11,329 |
| Operating income | 130,387 | 81,453 | 32,972 |
| Interest income | 2,300 | 1,786 | 866 |
| Interest expense | (259) | (247) | (257) |
| Other income, net | 9,022 | 1,034 | 237 |
| Total other income, net | 11,063 | 2,573 | 846 |
| Income before income tax | 141,450 | 84,026 | 33,818 |
| Income tax expense | 21,383 | 11,146 | 4,058 |
| Net income | $120,067 | $72,880 | $29,760 |
| Net income per share: |  |  |  |
| Basic | $4.93 | $2.97 | $1.21 |
| Diluted | $4.90 | $2.94 | $1.19 |
| Weighted average shares used in per share computation: |  |  |  |
| Basic | 24,359 | 24,555 | 24,690 |
| Diluted | 24,514 | 24,804 | 24,940 |
```

- xbrl_0084: 3491 in non-gold 0001045810-25-000023:617.0:617.0 [NVIDIA CORP (NVDA) | 10-K | FY2025 | Item 7: Management's Discussion and Analysis of Financial Condition and Results of Operations] | | Sales, general and administrative expenses | 3,491 | 2,654 | 837 | 32% |

## xbrl_0090

- Question: How much did NVIDIA carry in cash and cash equivalents at the end of fiscal 2025?
- Reference answer: $8,589 million as of January 26, 2025.
- Accessions: 0001045810-25-000023, 0001045810-25-000116, 0001045810-25-000209, 0001045810-25-000230, 0001045810-26-000021
- xbrl_fact_id: 44729
- tags: NVDA, cash_and_equivalents, FY2025, 10-K, instant, template:ins_carry, unit_scale_millions

### 0001045810-25-000023:782.0:782.0

```
[NVIDIA CORP (NVDA) | 10-K | FY2025 | Item 15: Exhibits and Financial Statement Schedules]
[Table: Consolidated Balance Sheets | NVIDIA CORP | FY2025 10-K | Item 15 | in millions, USD]
|  | Jan 26, 2025 | Jan 28, 2024 |
|---|---|---|
| Assets |  |  |
| Current assets: |  |  |
| Cash and cash equivalents | $8,589 | $7,280 |
| Marketable securities | 34,621 | 18,704 |
| Accounts receivable, net | 23,065 | 9,999 |
| Inventories | 10,080 | 5,282 |
| Prepaid expenses and other current assets | 3,771 | 3,080 |
| Total current assets | 80,126 | 44,345 |
| Property and equipment, net | 6,283 | 3,914 |
| Operating lease assets | 1,793 | 1,346 |
| Goodwill | 5,188 | 4,430 |
| Intangible assets, net | 807 | 1,112 |
| Deferred income tax assets | 10,979 | 6,081 |
| Other assets | 6,425 | 4,500 |
| Total assets | $111,601 | $65,728 |
| Liabilities and Shareholders' Equity |  |  |
| Current liabilities: |  |  |
| Accounts payable | $6,310 | $2,699 |
| Accrued and other current liabilities | 11,737 | 6,682 |
| Short-term debt | — | 1,250 |
| Total current liabilities | 18,047 | 10,631 |
| Long-term debt | 8,463 | 8,459 |
| Long-term operating lease liabilities | 1,519 | 1,119 |
| Other long-term liabilities | 4,245 | 2,541 |
| Total liabilities | 32,274 | 22,750 |
| Commitments and contingencies - see Note 12 | — | — |
| Shareholders’ equity: |  |  |
| Preferred stock, $0.001 par value; 20 shares authorized; none issued | — | — |
```

### 0001045810-25-000116:57.0:57.0

```
[NVIDIA CORP (NVDA) | 10-Q | Q1 FY2026 | Part I, Item 1: Financial Statements (Unaudited)]
[Table: Condensed Consolidated Balance Sheets | NVIDIA CORP | Q1 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Apr 27, 2025 | Jan 26, 2025 |
|---|---|---|
| Assets |  |  |
| Current assets: |  |  |
| Cash and cash equivalents | $15,234 | $8,589 |
| Marketable securities | 38,457 | 34,621 |
| Accounts receivable, net | 22,132 | 23,065 |
| Inventories | 11,333 | 10,080 |
| Prepaid expenses and other current assets | 2,779 | 3,771 |
| Total current assets | 89,935 | 80,126 |
| Property and equipment, net | 7,136 | 6,283 |
| Operating lease assets | 1,810 | 1,793 |
| Goodwill | 5,498 | 5,188 |
| Intangible assets, net | 769 | 807 |
| Deferred income tax assets | 13,318 | 10,979 |
| Other assets | 6,788 | 6,425 |
| Total assets | $125,254 | $111,601 |
| Liabilities and Shareholders' Equity |  |  |
| Current liabilities: |  |  |
| Accounts payable | $7,331 | $6,310 |
| Accrued and other current liabilities | 19,211 | 11,737 |
| Total current liabilities | 26,542 | 18,047 |
| Long-term debt | 8,464 | 8,463 |
| Long-term operating lease liabilities | 1,521 | 1,519 |
| Other long-term liabilities | 4,884 | 4,245 |
| Total liabilities | 41,411 | 32,274 |
| Commitments and contingencies - see Note 11 |  |  |
| Shareholders’ equity: |  |  |
| Preferred stock | — | — |
| Common stock | 24 | 24 |
| Additional paid-in capital | 11,475 | 11,237 |
| Accumulated other comprehensive income | 186 | 28 |
```

### 0001045810-25-000209:58.0:58.0

```
[NVIDIA CORP (NVDA) | 10-Q | Q2 FY2026 | Part I, Item 1: Financial Statements (Unaudited)]
[Table: Condensed Consolidated Balance Sheets | NVIDIA CORP | Q2 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Jul 27, 2025 | Jan 26, 2025 |
|---|---|---|
| Assets |  |  |
| Current assets: |  |  |
| Cash and cash equivalents | $11,639 | $8,589 |
| Marketable securities | 45,152 | 34,621 |
| Accounts receivable, net | 27,808 | 23,065 |
| Inventories | 14,962 | 10,080 |
| Prepaid expenses and other current assets | 2,658 | 3,771 |
| Total current assets | 102,219 | 80,126 |
| Property and equipment, net | 9,141 | 6,283 |
| Operating lease assets | 2,084 | 1,793 |
| Goodwill | 5,755 | 5,188 |
| Intangible assets, net | 755 | 807 |
| Deferred income tax assets | 13,570 | 10,979 |
| Other assets | 7,216 | 6,425 |
| Total assets | $140,740 | $111,601 |
| Liabilities and Shareholders' Equity |  |  |
| Current liabilities: |  |  |
| Accounts payable | $9,064 | $6,310 |
| Accrued and other current liabilities | 15,193 | 11,737 |
| Total current liabilities | 24,257 | 18,047 |
| Long-term debt | 8,466 | 8,463 |
| Long-term operating lease liabilities | 1,831 | 1,519 |
| Other long-term liabilities | 6,055 | 4,245 |
| Total liabilities | 40,609 | 32,274 |
| Commitments and contingencies - see Note 11 |  |  |
| Shareholders’ equity: |  |  |
| Preferred stock | — | — |
| Common stock | 24 | 24 |
| Additional paid-in capital | 11,200 | 11,237 |
```

### 0001045810-25-000230:59.0:59.0

```
[NVIDIA CORP (NVDA) | 10-Q | Q3 FY2026 | Part I, Item 1: Financial Statements (Unaudited)]
[Table: Condensed Consolidated Balance Sheets | NVIDIA CORP | Q3 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Oct 26, 2025 | Jan 26, 2025 |
|---|---|---|
| Assets |  |  |
| Current assets: |  |  |
| Cash and cash equivalents | $11,486 | $8,589 |
| Marketable securities | 49,122 | 34,621 |
| Accounts receivable, net | 33,391 | 23,065 |
| Inventories | 19,784 | 10,080 |
| Prepaid expenses and other current assets | 2,709 | 3,771 |
| Total current assets | 116,492 | 80,126 |
| Property and equipment, net | 9,780 | 6,283 |
| Operating lease assets | 2,281 | 1,793 |
| Goodwill | 6,261 | 5,188 |
| Intangible assets, net | 936 | 807 |
| Deferred income tax assets | 13,674 | 10,979 |
| Other assets | 11,724 | 6,425 |
| Total assets | $161,148 | $111,601 |
| Liabilities and Shareholders' Equity |  |  |
| Current liabilities: |  |  |
| Accounts payable | $8,624 | $6,310 |
| Accrued and other current liabilities | 16,452 | 11,737 |
| Short-term debt | 999 | — |
| Total current liabilities | 26,075 | 18,047 |
| Long-term debt | 7,468 | 8,463 |
| Long-term operating lease liabilities | 2,014 | 1,519 |
| Other long-term liabilities | 6,694 | 4,245 |
| Total liabilities | 42,251 | 32,274 |
| Commitments and contingencies - see Note 11 |  |  |
| Shareholders’ equity: |  |  |
| Preferred stock | — | — |
| Common stock | 24 | 24 |
```

### 0001045810-26-000021:765.0:765.0

```
[NVIDIA CORP (NVDA) | 10-K | FY2026 | Item 15: Exhibits and Financial Statement Schedules]
[Table: Consolidated Balance Sheets | NVIDIA CORP | FY2026 10-K | Item 15 | in millions, USD]
|  | Jan 25, 2026 | Jan 26, 2025 |
|---|---|---|
| Assets |  |  |
| Current assets: |  |  |
| Cash and cash equivalents | $10,605 | $8,589 |
| Marketable securities | 51,951 | 34,621 |
| Accounts receivable, net | 38,466 | 23,065 |
| Inventories | 21,403 | 10,080 |
| Prepaid expenses and other current assets | 3,180 | 3,771 |
| Total current assets | 125,605 | 80,126 |
| Property and equipment, net | 10,383 | 6,283 |
| Operating lease assets | 2,867 | 1,793 |
| Goodwill | 20,832 | 5,188 |
| Intangible assets, net | 3,306 | 807 |
| Deferred income tax assets | 13,258 | 10,979 |
| Non-marketable equity securities | 22,251 | 3,387 |
| Other assets | 8,301 | 3,038 |
| Total assets | $206,803 | $111,601 |
| Liabilities and Shareholders' Equity |  |  |
| Current liabilities: |  |  |
| Accounts payable | $9,812 | $6,310 |
| Accrued and other current liabilities | 21,352 | 11,737 |
| Short-term debt | 999 | — |
| Total current liabilities | 32,163 | 18,047 |
| Long-term debt | 7,469 | 8,463 |
| Long-term operating lease liabilities | 2,572 | 1,519 |
| Other long-term liabilities | 7,306 | 4,245 |
| Total liabilities | 49,510 | 32,274 |
| Commitments and contingencies - see Note 12 | — | — |
| Shareholders’ equity: |  |  |
```

- xbrl_0090: 8589 in non-gold 0001045810-26-000021:778.2:778.2 [NVIDIA CORP (NVDA) | 10-K | FY2026 | Item 15: Exhibits and Financial Statement Schedules] | | Cash and cash equivalents at beginning of period | 8,589 | 7,280 | 3,389 |
- xbrl_0090: 8589 in non-gold 0001045810-25-000023:795.2:795.2 [NVIDIA CORP (NVDA) | 10-K | FY2025 | Item 15: Exhibits and Financial Statement Schedules] | | Cash and cash equivalents at end of period | $8,589 | $7,280 | $3,389 |
- xbrl_0090: 8589 in non-gold 0001045810-25-000209:375.0:375.0 [NVIDIA CORP (NVDA) | 10-Q | Q2 FY2026 | Part I, Item 2: Management's Discussion and Analysis of Financial Condition and Results of Operations] | | Cash and cash equivalents | $11,639 | $8,589 |
- xbrl_0090: 8589 in non-gold 0001045810-25-000023:634.0:634.0 [NVIDIA CORP (NVDA) | 10-K | FY2025 | Item 7: Management's Discussion and Analysis of Financial Condition and Results of Operations] | | Cash and cash equivalents | $8,589 | $7,280 |
- xbrl_0090: 8589 in non-gold 0001045810-25-000116:362.0:362.0 [NVIDIA CORP (NVDA) | 10-Q | Q1 FY2026 | Part I, Item 2: Management's Discussion and Analysis of Financial Condition and Results of Operations] | | Cash and cash equivalents | $15,234 | $8,589 |

## xbrl_0096

- Question: What was the balance of NVIDIA's cash and cash equivalents on October 26, 2025?
- Reference answer: $11,486 million as of October 26, 2025.
- Accessions: 0001045810-25-000230
- xbrl_fact_id: 44736
- tags: NVDA, cash_and_equivalents, FY2026, 10-Q, instant, template:ins_balance, unit_scale_millions

### 0001045810-25-000230:59.0:59.0

```
[NVIDIA CORP (NVDA) | 10-Q | Q3 FY2026 | Part I, Item 1: Financial Statements (Unaudited)]
[Table: Condensed Consolidated Balance Sheets | NVIDIA CORP | Q3 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Oct 26, 2025 | Jan 26, 2025 |
|---|---|---|
| Assets |  |  |
| Current assets: |  |  |
| Cash and cash equivalents | $11,486 | $8,589 |
| Marketable securities | 49,122 | 34,621 |
| Accounts receivable, net | 33,391 | 23,065 |
| Inventories | 19,784 | 10,080 |
| Prepaid expenses and other current assets | 2,709 | 3,771 |
| Total current assets | 116,492 | 80,126 |
| Property and equipment, net | 9,780 | 6,283 |
| Operating lease assets | 2,281 | 1,793 |
| Goodwill | 6,261 | 5,188 |
| Intangible assets, net | 936 | 807 |
| Deferred income tax assets | 13,674 | 10,979 |
| Other assets | 11,724 | 6,425 |
| Total assets | $161,148 | $111,601 |
| Liabilities and Shareholders' Equity |  |  |
| Current liabilities: |  |  |
| Accounts payable | $8,624 | $6,310 |
| Accrued and other current liabilities | 16,452 | 11,737 |
| Short-term debt | 999 | — |
| Total current liabilities | 26,075 | 18,047 |
| Long-term debt | 7,468 | 8,463 |
| Long-term operating lease liabilities | 2,014 | 1,519 |
| Other long-term liabilities | 6,694 | 4,245 |
| Total liabilities | 42,251 | 32,274 |
| Commitments and contingencies - see Note 11 |  |  |
| Shareholders’ equity: |  |  |
| Preferred stock | — | — |
| Common stock | 24 | 24 |
```

- xbrl_0096: 11486 in non-gold 0001045810-25-000230:383.0:383.0 [NVIDIA CORP (NVDA) | 10-Q | Q3 FY2026 | Part I, Item 2: Management's Discussion and Analysis of Financial Condition and Results of Operations] | | Cash and cash equivalents | $11,486 | $8,589 |

## xbrl_0100

- Question: NVIDIA operating income, the third quarter of fiscal 2026: what was the figure?
- Reference answer: $36,010 million for the three months ended October 26, 2025.
- Accessions: 0001045810-25-000230
- xbrl_fact_id: 46972
- tags: NVDA, operating_income, FY2026, 10-Q, quarter, template:dur_figure, unit_scale_millions

### 0001045810-25-000230:45.0:45.0

```
[NVIDIA CORP (NVDA) | 10-Q | Q3 FY2026 | Part I, Item 1: Financial Statements (Unaudited)]
[Table: Condensed Consolidated Statements of Income | NVIDIA CORP | Q3 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Three Months Ended Oct 26, 2025 | Three Months Ended Oct 27, 2024 | Nine Months Ended Oct 26, 2025 | Nine Months Ended Oct 27, 2024 |
|---|---|---|---|---|
| Revenue | $57,006 | $35,082 | $147,811 | $91,166 |
| Cost of revenue | 15,157 | 8,926 | 45,441 | 22,031 |
| Gross profit | 41,849 | 26,156 | 102,370 | 69,135 |
| Operating expenses |  |  |  |  |
| Research and development | 4,705 | 3,390 | 12,985 | 9,200 |
| Sales, general and administrative | 1,134 | 897 | 3,297 | 2,516 |
| Total operating expenses | 5,839 | 4,287 | 16,282 | 11,716 |
| Operating income | 36,010 | 21,869 | 86,088 | 57,419 |
| Interest income | 624 | 472 | 1,732 | 1,275 |
| Interest expense | (61) | (61) | (186) | (186) |
| Other income, net | 1,363 | 36 | 3,418 | 301 |
| Total other income, net | 1,926 | 447 | 4,964 | 1,390 |
| Income before income tax | 37,936 | 22,316 | 91,052 | 58,809 |
| Income tax expense | 6,026 | 3,007 | 13,945 | 8,020 |
| Net income | $31,910 | $19,309 | $77,107 | $50,789 |
| Net income per share: |  |  |  |  |
| Basic | $1.31 | $0.79 | $3.16 | $2.07 |
```

- xbrl_0100: 36010 in non-gold 0001045810-25-000230:326.0:326.0 [NVIDIA CORP (NVDA) | 10-Q | Q3 FY2026 | Part I, Item 2: Management's Discussion and Analysis of Financial Condition and Results of Operations] | | Operating income | $36,010 | $28,440 | $21,869 | 27% | 65% |

## xbrl_0102

- Question: According to its fiscal 2023 10-K, what figure did Pfizer report for cost of revenue in the fiscal year ended December 31, 2023?
- Reference answer: $24,954 million for the fiscal year ended December 31, 2023.
- Accessions: 0000078003-24-000039
- xbrl_fact_id: 53671
- tags: PFE, cost_of_revenue, FY2023, 10-K, annual, template:dur_filing, unit_scale_millions

### 0000078003-24-000039:823.0:823.0

```
[PFIZER INC (PFE) | 10-K | FY2023 | Item 8: FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA]
[Table: Pfizer Inc. and Subsidiary Companies | PFIZER INC | FY2023 10-K | Item 8 | in millions, USD]
|  | Year Ended December 31, 2023 | Year Ended December 31, 2022 | Year Ended December 31, 2021 |
|---|---|---|---|
| Revenues: |  |  |  |
| Product revenues(a) | $50,914 | $91,793 | $73,636 |
| Alliance revenues(a) | 7,582 | 8,537 | 7,652 |
| Total revenues | 58,496 | 100,330 | 81,288 |
| Costs and expenses: |  |  |  |
| Cost of sales(b), (c) | 24,954 | 34,344 | 30,821 |
| Selling, informational and administrative expenses(b) | 14,771 | 13,677 | 12,703 |
| Research and development expenses(b) | 10,679 | 11,428 | 10,360 |
| Acquired in-process research and development expenses | 194 | 953 | 3,469 |
| Amortization of intangible assets | 4,733 | 3,609 | 3,700 |
| Restructuring charges and certain acquisition-related costs | 2,943 | 1,375 | 802 |
| Other (income)/deductions––net | (835) | 217 | (4,878) |
| Income from continuing operations before provision/(benefit) for taxes on income | 1,058 | 34,729 | 24,311 |
| Provision/(benefit) for taxes on income | (1,115) | 3,328 | 1,852 |
| Income from continuing operations | 2,172 | 31,401 | 22,459 |
| Discontinued operations––net of tax | (15) | 6 | (434) |
| Net income before allocation to noncontrolling interests | 2,158 | 31,407 | 22,025 |
| Less: Net income attributable to noncontrolling interests | 39 | 35 | 45 |
```

- xbrl_0102: 24954 in non-gold 0000078003-24-000039:623.0:623.0 [PFIZER INC (PFE) | 10-K | FY2023 | Item 7: MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS] | | Cost of sales | $24,954 | $34,344 | $30,821 | (27) | 11 |
- xbrl_0102: 24954 in non-gold 0000078003-25-000054:576.0:576.0 [PFIZER INC (PFE) | 10-K | FY2024 | Item 7: MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS] | | Cost of sales | $17,851 | $24,954 | $34,344 | (28) | (27) |
- xbrl_0102: 24954 in non-gold 0000078003-26-000026:591.0:591.0 [PFIZER INC (PFE) | 10-K | FY2025 | Item 7: MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS] | | Cost of sales | $16,067 | $17,851 | $24,954 | (10) | (28) |

- xbrl_0104: 57639 in non-gold 0000078003-25-000114:195.0:195.0 [PFIZER INC (PFE) | 10-Q | Q1 FY2025 | Part I, Item 1: FINANCIAL STATEMENTS] | | Total long-term debt, carried at historical proceeds, as adjusted | $57,639 | $57,405 |

## xbrl_0111

- Question: What did Pfizer report as its total stockholders' equity as of June 30, 2024?
- Reference answer: $87,700 million as of June 30, 2024.
- Accessions: 0000078003-24-000166
- xbrl_fact_id: 58096
- tags: PFE, stockholders_equity, FY2024, 10-Q, instant, template:ins_report, unit_scale_millions

### 0000078003-24-000166:65.1:65.1

```
[PFIZER INC (PFE) | 10-Q | Q2 FY2024 | Part I, Item 1: FINANCIAL STATEMENTS]
[Table: CONDENSED CONSOLIDATED BALANCE SHEETS | PFIZER INC | Q2 FY2024 10-Q | Part I, Item 1 | in millions, USD]
|  | June 30, 2024 (Unaudited) | December 31, 2023 |
|---|---|---|
| Accrued compensation and related items | 2,566 | 2,776 |
| Deferred revenues | 2,528 | 2,700 |
| Other current liabilities | 16,410 | 20,537 |
| Total current liabilities | 43,819 | 47,794 |
| Long-term debt | 57,506 | 61,538 |
| Pension and postretirement benefit obligations | 2,040 | 2,167 |
| Noncurrent deferred tax liabilities | 2,227 | 640 |
| Other taxes payable | 6,532 | 8,534 |
| Other noncurrent liabilities | 16,095 | 16,539 |
| Total liabilities | 128,218 | 137,213 |
| Commitments and Contingencies |  |  |
| Common stock | 480 | 478 |
| Additional paid-in capital | 93,197 | 92,631 |
| Treasury stock | (114,757) | (114,487) |
| Retained earnings | 116,596 | 118,353 |
| Accumulated other comprehensive loss | (7,816) | (7,961) |
| Total Pfizer Inc. shareholders’ equity | 87,700 | 89,014 |
| Equity attributable to noncontrolling interests | 275 | 274 |
| Total equity | 87,975 | 89,288 |
| Total liabilities and equity | $216,193 | $226,501 |
```

- xbrl_0111: 87700 in non-gold 0000078003-24-000191:72.0:72.0 [PFIZER INC (PFE) | 10-Q | Q3 FY2024 | Part I, Item 1: FINANCIAL STATEMENTS] | | Balance, June 30, 2024 | 9,592 | $480 | $93,197 | (3,925) | $(114,757) | $116,596 | $(7,816) | $87,700 | $275 | $87,975 |
- xbrl_0111: 87700 in non-gold 0000078003-24-000166:71.1:71.1 [PFIZER INC (PFE) | 10-Q | Q2 FY2024 | Part I, Item 1: FINANCIAL STATEMENTS] | | Balance, June 30, 2024 | 9,592 | $480 | $93,197 | (3,925) | $(114,757) | $116,596 | $(7,816) | $87,700 | $275 | $87,975 |

## xbrl_0123

- Question: What did Target report as its net income for the third quarter of fiscal 2025?
- Reference answer: $689 million for the three months ended November 1, 2025.
- Accessions: 0000027419-25-000126, 0000027419-26-000022, 0000027419-26-000042
- xbrl_fact_id: 3282
- tags: TGT, net_income, FY2025, 10-Q, quarter, template:dur_report, unit_scale_millions

### 0000027419-25-000126:36.0:36.0

```
[TARGET CORPORATION (TGT) | 10-Q | Q3 FY2025 | Part I, Item 1: Financial Statements]
[Table: Consolidated Statements of Operations | TARGET CORPORATION | Q3 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | Three Months Ended November 1, 2025 | Three Months Ended November 2, 2024 | Nine Months Ended November 1, 2025 | Nine Months Ended November 2, 2024 |
|---|---|---|---|---|
| Net sales | $25,270 | $25,668 | $74,327 | $75,651 |
| Cost of sales | 18,137 | 18,402 | 53,168 | 53,700 |
| Selling, general, and administrative expenses | 5,536 | 5,459 | 15,486 | 15,969 |
| Depreciation and amortization (exclusive of depreciation included in cost of sales) | 649 | 639 | 1,936 | 1,883 |
| Operating income | 948 | 1,168 | 3,737 | 4,099 |
| Net interest expense | 115 | 105 | 346 | 321 |
| Net other income | (26) | (28) | (68) | (77) |
| Earnings before income taxes | 859 | 1,091 | 3,459 | 3,855 |
| Provision for income taxes | 170 | 237 | 799 | 867 |
| Net earnings | $689 | $854 | $2,660 | $2,988 |
| Basic earnings per share | $1.52 | $1.86 | $5.85 | $6.47 |
| Diluted earnings per share | $1.51 | $1.85 | $5.84 | $6.45 |
| Weighted average common shares outstanding |  |  |  |  |
| Basic | 453.7 | 460.1 | 454.4 | 461.6 |
| Diluted | 455.1 | 461.5 | 455.7 | 462.9 |
| Antidilutive shares | 2.3 | 0.5 | 2.3 | 0.5 |
```

### 0000027419-25-000126:40.0:40.0

```
[TARGET CORPORATION (TGT) | 10-Q | Q3 FY2025 | Part I, Item 1: Financial Statements]
[Table: Consolidated Statements of Comprehensive Income | TARGET CORPORATION | Q3 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | Three Months Ended November 1, 2025 | Three Months Ended November 2, 2024 | Nine Months Ended November 1, 2025 | Nine Months Ended November 2, 2024 |
|---|---|---|---|---|
| Net earnings | $689 | $854 | $2,660 | $2,988 |
| Other comprehensive (loss) / income, net of tax |  |  |  |  |
| Cash flow hedges and currency translation adjustment | (3) | (4) | (13) | (14) |
| Other comprehensive loss | (3) | (4) | (13) | (14) |
| Comprehensive income | $686 | $850 | $2,647 | $2,974 |
```

### 0000027419-25-000126:57.0:57.0

```
[TARGET CORPORATION (TGT) | 10-Q | Q3 FY2025 | Part I, Item 1: Financial Statements]
[Table: Consolidated Statements of Shareholders’ Investment | TARGET CORPORATION | Q3 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | Common Stock Shares | Stock Par Value | Additional Paid-in Capital | Retained Earnings | Accumulated Other Comprehensive Loss | Total |
|---|---|---|---|---|---|---|
| February 1, 2025 | 455.6 | $38 | $6,996 | $8,090 | $(458) | $14,666 |
| Net earnings | — | — | — | 1,036 | — | 1,036 |
| Other comprehensive loss | — | — | — | — | (4) | (4) |
| Dividends declared, $1.12 per share | — | — | — | (515) | — | (515) |
| Repurchase of stock | (2.2) | — | — | (251) | — | (251) |
| Share-based compensation | 1.0 | — | 15 | — | — | 15 |
| May 3, 2025 | 454.4 | $38 | $7,011 | $8,360 | $(462) | $14,947 |
| Net earnings | — | — | — | 935 | — | 935 |
| Other comprehensive loss | — | — | — | — | (6) | (6) |
| Dividends declared, $1.14 per share | — | — | — | (529) | — | (529) |
| Share-based compensation | — | — | 73 | — | — | 73 |
| August 2, 2025 | 454.4 | $38 | $7,084 | $8,766 | $(468) | $15,420 |
| Net earnings | — | — | — | 689 | — | 689 |
| Other comprehensive loss | — | — | — | — | (3) | (3) |
```

### 0000027419-26-000022:54.0:54.0

```
[TARGET CORPORATION (TGT) | 10-Q | Q1 FY2026 | Part I, Item 1: Financial Statements]
[Table: Consolidated Statements of Shareholders’ Investment | TARGET CORPORATION | Q1 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Common Stock Shares | Stock Par Value | Additional Paid-in Capital | Retained Earnings | Accumulated Other Comprehensive Loss | Total |
|---|---|---|---|---|---|---|
| February 1, 2025 | 455.6 | $38 | $6,996 | $8,090 | $(458) | $14,666 |
| Net earnings | — | — | — | 1,036 | — | 1,036 |
| Other comprehensive loss | — | — | — | — | (4) | (4) |
| Dividends declared, $1.12 per share | — | — | — | (515) | — | (515) |
| Repurchase of stock | (2.2) | — | — | (251) | — | (251) |
| Share-based compensation | 1.0 | — | 15 | — | — | 15 |
| May 3, 2025 | 454.4 | $38 | $7,011 | $8,360 | $(462) | $14,947 |
| Net earnings | — | — | — | 935 | — | 935 |
| Other comprehensive loss | — | — | — | — | (6) | (6) |
| Dividends declared, $1.14 per share | — | — | — | (529) | — | (529) |
| Share-based compensation | — | — | 73 | — | — | 73 |
| August 2, 2025 | 454.4 | $38 | $7,084 | $8,766 | $(468) | $15,420 |
| Net earnings | — | — | — | 689 | — | 689 |
| Other comprehensive loss | — | — | — | — | (3) | (3) |
```

### 0000027419-26-000042:54.0:54.0

```
[TARGET CORPORATION (TGT) | 10-Q | Q2 FY2026 | Part I, Item 1: Financial Statements]
[Table: Consolidated Statements of Shareholders’ Investment | TARGET CORPORATION | Q2 FY2026 10-Q | Part I, Item 1 | in millions, USD]
|  | Common Stock Shares | Stock Par Value | Additional Paid-in Capital | Retained Earnings | Accumulated Other Comprehensive Loss | Total |
|---|---|---|---|---|---|---|
| February 1, 2025 | 455.6 | $38 | $6,996 | $8,090 | $(458) | $14,666 |
| Net earnings | — | — | — | 1,036 | — | 1,036 |
| Other comprehensive loss | — | — | — | — | (4) | (4) |
| Dividends declared, $1.12 per share | — | — | — | (515) | — | (515) |
| Repurchase of stock | (2.2) | — | — | (251) | — | (251) |
| Share-based compensation | 1.0 | — | 15 | — | — | 15 |
| May 3, 2025 | 454.4 | $38 | $7,011 | $8,360 | $(462) | $14,947 |
| Net earnings | — | — | — | 935 | — | 935 |
| Other comprehensive loss | — | — | — | — | (6) | (6) |
| Dividends declared, $1.14 per share | — | — | — | (529) | — | (529) |
| Share-based compensation | — | — | 73 | — | — | 73 |
| August 2, 2025 | 454.4 | $38 | $7,084 | $8,766 | $(468) | $15,420 |
| Net earnings | — | — | — | 689 | — | 689 |
| Other comprehensive loss | — | — | — | — | (3) | (3) |
```

- xbrl_0123: 689 in non-gold 0000027419-25-000126:229.0:229.0 [TARGET CORPORATION (TGT) | 10-Q | Q3 FY2025 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations] | | Net earnings | $689 | $854 | (19.3)% | $2,660 | $2,988 | (11.0)% |

## xbrl_0124

- Question: According to its 10-Q for the second quarter of fiscal 2025, what figure did Target report for cost of revenue in the six months ended August 2, 2025?
- Reference answer: $35,031 million for the six months ended August 2, 2025.
- Accessions: 0000027419-25-000118
- xbrl_fact_id: 12515
- tags: TGT, cost_of_revenue, FY2025, 10-Q, ytd, template:dur_filing, unit_scale_millions

### 0000027419-25-000118:36.0:36.0

```
[TARGET CORPORATION (TGT) | 10-Q | Q2 FY2025 | Part I, Item 1: Financial Statements]
[Table: Consolidated Statements of Operations | TARGET CORPORATION | Q2 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | Three Months Ended August 2, 2025 | Three Months Ended August 3, 2024 | Six Months Ended August 2, 2025 | Six Months Ended August 3, 2024 |
|---|---|---|---|---|
| Net sales | $25,211 | $25,452 | $49,057 | $49,983 |
| Cost of sales | 17,903 | 17,826 | 35,031 | 35,297 |
| Selling, general, and administrative expenses | 5,359 | 5,365 | 9,950 | 10,511 |
| Depreciation and amortization (exclusive of depreciation included in cost of sales) | 632 | 626 | 1,287 | 1,244 |
| Operating income | 1,317 | 1,635 | 2,789 | 2,931 |
| Net interest expense | 116 | 110 | 232 | 216 |
| Net other income | (17) | (20) | (43) | (49) |
| Earnings before income taxes | 1,218 | 1,545 | 2,600 | 2,764 |
| Provision for income taxes | 283 | 353 | 629 | 630 |
| Net earnings | $935 | $1,192 | $1,971 | $2,134 |
| Basic earnings per share | $2.06 | $2.58 | $4.33 | $4.62 |
| Diluted earnings per share | $2.05 | $2.57 | $4.32 | $4.60 |
| Weighted average common shares outstanding |  |  |  |  |
| Basic | 454.6 | 462.5 | 454.8 | 462.4 |
| Diluted | 455.6 | 463.5 | 456.1 | 463.7 |
| Antidilutive shares | 5.0 | 2.3 | 2.3 | 1.8 |
```

- xbrl_0124: 35031 in non-gold 0000027419-25-000118:135.0:135.0 [TARGET CORPORATION (TGT) | 10-Q | Q2 FY2025 | Part I, Item 1: Financial Statements] | | Total cost of sales | 17,903 | 17,826 | 35,031 | 35,297 |
- xbrl_0124: 35031 in non-gold 0000027419-25-000118:158.0:158.0 [TARGET CORPORATION (TGT) | 10-Q | Q2 FY2025 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations] | | Cost of sales (a) | 17,903 | 17,826 | 0.4 | 35,031 | 35,297 | (0.8) |
- xbrl_0124: 35031 in non-gold 0000027419-26-000042:136.0:136.0 [TARGET CORPORATION (TGT) | 10-Q | Q2 FY2026 | Part I, Item 1: Financial Statements] | | Total cost of sales (a) | 17,603 | 17,903 | 35,664 | 35,031 |

## xbrl_0137

- Question: Target diluted earnings per share, the first three quarters of fiscal 2024: what was the figure?
- Reference answer: $6.45 for the nine months ended November 2, 2024.
- Accessions: 0000027419-24-000179, 0000027419-25-000126
- xbrl_fact_id: 13209
- tags: TGT, eps_diluted, FY2024, 10-Q, ytd, template:dur_figure, unit_scale_none

### 0000027419-24-000179:36.0:36.0

```
[TARGET CORPORATION (TGT) | 10-Q | Q3 FY2024 | Part I, Item 1: Financial Statements]
[Table: Consolidated Statements of Operations | TARGET CORPORATION | Q3 FY2024 10-Q | Part I, Item 1 | in millions, USD]
|  | Three Months Ended November 2, 2024 | Three Months Ended October 28, 2023 | Nine Months Ended November 2, 2024 | Nine Months Ended October 28, 2023 |
|---|---|---|---|---|
| Sales | $25,228 | $25,004 | $74,392 | $74,336 |
| Other revenue | 440 | 394 | 1,259 | 1,157 |
| Total revenue | 25,668 | 25,398 | 75,651 | 75,493 |
| Cost of sales | 18,375 | 18,149 | 53,623 | 54,333 |
| Selling, general and administrative expenses | 5,486 | 5,316 | 16,046 | 15,525 |
| Depreciation and amortization (exclusive of depreciation included in cost of sales) | 639 | 616 | 1,883 | 1,793 |
| Operating income | 1,168 | 1,317 | 4,099 | 3,842 |
| Net interest expense | 105 | 107 | 321 | 395 |
| Net other income | (28) | (25) | (77) | (64) |
| Earnings before income taxes | 1,091 | 1,235 | 3,855 | 3,511 |
| Provision for income taxes | 237 | 264 | 867 | 755 |
| Net earnings | $854 | $971 | $2,988 | $2,756 |
| Basic earnings per share | $1.86 | $2.10 | $6.47 | $5.97 |
| Diluted earnings per share | $1.85 | $2.10 | $6.45 | $5.96 |
| Weighted average common shares outstanding |  |  |  |  |
| Basic | 460.1 | 461.6 | 461.6 | 461.4 |
```

### 0000027419-25-000126:36.0:36.0

```
[TARGET CORPORATION (TGT) | 10-Q | Q3 FY2025 | Part I, Item 1: Financial Statements]
[Table: Consolidated Statements of Operations | TARGET CORPORATION | Q3 FY2025 10-Q | Part I, Item 1 | in millions, USD]
|  | Three Months Ended November 1, 2025 | Three Months Ended November 2, 2024 | Nine Months Ended November 1, 2025 | Nine Months Ended November 2, 2024 |
|---|---|---|---|---|
| Net sales | $25,270 | $25,668 | $74,327 | $75,651 |
| Cost of sales | 18,137 | 18,402 | 53,168 | 53,700 |
| Selling, general, and administrative expenses | 5,536 | 5,459 | 15,486 | 15,969 |
| Depreciation and amortization (exclusive of depreciation included in cost of sales) | 649 | 639 | 1,936 | 1,883 |
| Operating income | 948 | 1,168 | 3,737 | 4,099 |
| Net interest expense | 115 | 105 | 346 | 321 |
| Net other income | (26) | (28) | (68) | (77) |
| Earnings before income taxes | 859 | 1,091 | 3,459 | 3,855 |
| Provision for income taxes | 170 | 237 | 799 | 867 |
| Net earnings | $689 | $854 | $2,660 | $2,988 |
| Basic earnings per share | $1.52 | $1.86 | $5.85 | $6.47 |
| Diluted earnings per share | $1.51 | $1.85 | $5.84 | $6.45 |
| Weighted average common shares outstanding |  |  |  |  |
| Basic | 453.7 | 460.1 | 454.4 | 461.6 |
| Diluted | 455.1 | 461.5 | 455.7 | 462.9 |
| Antidilutive shares | 2.3 | 0.5 | 2.3 | 0.5 |
```

- xbrl_0137: 6.45 in non-gold 0000027419-24-000179:138.0:138.0 [TARGET CORPORATION (TGT) | 10-Q | Q3 FY2024 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations] | | GAAP and Adjusted EPS | $1.85 | $2.10 | (11.9)% | $6.45 | $5.96 | 8.3% |
- xbrl_0137: 6.45 in non-gold 0000027419-25-000126:155.0:155.0 [TARGET CORPORATION (TGT) | 10-Q | Q3 FY2025 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations] | | GAAP diluted earnings per share | $1.51 | $1.85 | (18.2)% | $5.84 | $6.45 | (9.6)% |

## xbrl_0138

- Question: How much operating income did Target report for the fiscal year ended February 3, 2024?
- Reference answer: $5,707 million for the fiscal year ended February 3, 2024.
- Accessions: 0000027419-24-000032, 0000027419-25-000018, 0000027419-26-000016
- xbrl_fact_id: 14117
- tags: TGT, operating_income, FY2023, 10-K, annual, template:dur_how_much, unit_scale_millions

### 0000027419-24-000032:468.0:468.0

```
[TARGET CORPORATION (TGT) | 10-K | FY2023 | Item 8: Financial Statements and Supplementary Data]
[Table: Consolidated Statements of Operations | TARGET CORPORATION | FY2023 10-K | Item 8 | in millions, USD]
|  | 2023 | 2022 | 2021 |
|---|---|---|---|
| Sales | $105,803 | $107,588 | $104,611 |
| Other revenue | 1,609 | 1,532 | 1,394 |
| Total revenue | 107,412 | 109,120 | 106,005 |
| Cost of sales | 77,736 | 82,229 | 74,963 |
| Selling, general and administrative expenses | 21,554 | 20,658 | 19,752 |
| Depreciation and amortization (exclusive of depreciation included in cost of sales) | 2,415 | 2,385 | 2,344 |
| Operating income | 5,707 | 3,848 | 8,946 |
| Net interest expense | 502 | 478 | 421 |
| Net other income | (92) | (48) | (382) |
| Earnings before income taxes | 5,297 | 3,418 | 8,907 |
| Provision for income taxes | 1,159 | 638 | 1,961 |
| Net earnings | $4,138 | $2,780 | $6,946 |
| Basic earnings per share | $8.96 | $6.02 | $14.23 |
| Diluted earnings per share | $8.94 | $5.98 | $14.10 |
| Weighted average common shares outstanding |  |  |  |
| Basic | 461.5 | 462.1 | 488.1 |
| Diluted | 462.8 | 464.7 | 492.7 |
| Antidilutive shares | 2.1 | 1.1 | — |
```

### 0000027419-25-000018:477.0:477.0

```
[TARGET CORPORATION (TGT) | 10-K | FY2024 | Item 8: Financial Statements and Supplementary Data]
[Table: Consolidated Statements of Operations | TARGET CORPORATION | FY2024 10-K | Item 8 | in millions, USD]
|  | 2024 | 2023 | 2022 |
|---|---|---|---|
| Net sales | $106,566 | $107,412 | $109,120 |
| Cost of sales | 76,502 | 77,828 | 82,306 |
| Selling, general, and administrative expenses | 21,969 | 21,462 | 20,581 |
| Depreciation and amortization (exclusive of depreciation included in cost of sales) | 2,529 | 2,415 | 2,385 |
| Operating income | 5,566 | 5,707 | 3,848 |
| Net interest expense | 411 | 502 | 478 |
| Net other income | (106) | (92) | (48) |
| Earnings before income taxes | 5,261 | 5,297 | 3,418 |
| Provision for income taxes | 1,170 | 1,159 | 638 |
| Net earnings | $4,091 | $4,138 | $2,780 |
| Basic earnings per share | $8.89 | $8.96 | $6.02 |
| Diluted earnings per share | $8.86 | $8.94 | $5.98 |
| Weighted average common shares outstanding |  |  |  |
| Basic | 460.4 | 461.5 | 462.1 |
| Diluted | 461.8 | 462.8 | 464.7 |
| Antidilutive shares | 0.5 | 2.1 | 1.1 |
```

### 0000027419-26-000016:494.0:494.0

```
[TARGET CORPORATION (TGT) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data]
[Table: Consolidated Statements of Operations | TARGET CORPORATION | FY2025 10-K | Item 8 | in millions, USD]
|  | 2025 | 2024 | 2023 |
|---|---|---|---|
| Net sales | $104,780 | $106,566 | $107,412 |
| Cost of sales | 75,511 | 76,502 | 77,828 |
| Selling, general, and administrative expenses | 21,535 | 21,969 | 21,462 |
| Depreciation and amortization (exclusive of depreciation included in cost of sales) | 2,617 | 2,529 | 2,415 |
| Operating income | 5,117 | 5,566 | 5,707 |
| Net interest expense | 445 | 411 | 502 |
| Net other income | (95) | (106) | (92) |
| Earnings before income taxes | 4,767 | 5,261 | 5,297 |
| Provision for income taxes | 1,062 | 1,170 | 1,159 |
| Net earnings | $3,705 | $4,091 | $4,138 |
| Basic earnings per share | $8.16 | $8.89 | $8.96 |
| Diluted earnings per share | $8.13 | $8.86 | $8.94 |
| Weighted average common shares outstanding |  |  |  |
| Basic | 454.1 | 460.4 | 461.5 |
| Diluted | 455.6 | 461.8 | 462.8 |
| Antidilutive shares | 2.1 | 0.5 | 2.1 |
```

### 0000027419-26-000016:761.0:761.0

```
[TARGET CORPORATION (TGT) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data]
[Table: Business Segment Results | TARGET CORPORATION | FY2025 10-K | Item 8 | in millions, USD]
|  | 2025 | 2024 | 2023 |
|---|---|---|---|
| Net sales | $104,780 | $106,566 | $107,412 |
| Cost of sales |  |  |  |
| Merchandising cost of sales (a) | 67,980 | 68,884 | 70,652 |
| Supply chain and digital fulfillment costs (a) | 7,531 | 7,618 | 7,176 |
| Total cost of sales | 75,511 | 76,502 | 77,828 |
| SG&A expenses (b) | 21,535 | 21,969 | 21,462 |
| Depreciation and amortization (exclusive of depreciation included in cost of sales) | 2,617 | 2,529 | 2,415 |
| Operating income | 5,117 | 5,566 | 5,707 |
| Net interest expense | 445 | 411 | 502 |
| Net other income | (95) | (106) | (92) |
| Earnings before income taxes | 4,767 | 5,261 | 5,297 |
| Provision for income taxes | 1,062 | 1,170 | 1,159 |
| Net earnings | $3,705 | $4,091 | $4,138 |
```

- xbrl_0138: 5707 in non-gold 0000027419-24-000032:338.0:338.0 [TARGET CORPORATION (TGT) | 10-K | FY2023 | Item 7: Management's Discussion and Analysis of Financial Condition and Results of Operations] | | Operating income | $5,707 | $3,848 |
- xbrl_0138: 5707 in non-gold 0000027419-25-000018:352.0:352.0 [TARGET CORPORATION (TGT) | 10-K | FY2024 | Item 7: Management's Discussion and Analysis of Financial Condition and Results of Operations] | | Operating income | $5,566 | $5,707 |

## xbrl_0145

- Question: According to its 10-Q for the second quarter of fiscal 2024, what figure did Exxon Mobil report for net cash provided by operating activities in the six months ended June 30, 2024?
- Reference answer: $25,224 million for the six months ended June 30, 2024.
- Accessions: 0000034088-24-000050
- xbrl_fact_id: 50938
- tags: XOM, operating_cash_flow, FY2024, 10-Q, ytd, template:dur_filing, unit_scale_millions

### 0000034088-24-000050:48.0:48.0

```
[Exxon Mobil Corporation (XOM) | 10-Q | Q2 FY2024 | Part I, Item 1: FINANCIAL STATEMENTS]
[Table | Exxon Mobil Corporation | Q2 FY2024 10-Q | Part I, Item 1 | in millions]
|  | Six Months Ended June 30, 2024 | Six Months Ended June 30, 2023 |
|---|---|---|
| CASH FLOWS FROM OPERATING ACTIVITIES |  |  |
| Net income (loss) including noncontrolling interests | 18,137 | 19,996 |
| Depreciation and depletion (includes impairments) | 10,599 | 8,486 |
| Changes in operational working capital, excluding cash and debt | (2,608) | (3,885) |
| All other items – net | (904) | 1,127 |
| Net cash provided by operating activities | 25,224 | 25,724 |
| CASH FLOWS FROM INVESTING ACTIVITIES |  |  |
| Additions to property, plant and equipment | (11,309) | (10,771) |
| Proceeds from asset sales and returns of investments | 1,629 | 2,141 |
| Additional investments and advances | (744) | (834) |
| Other investing activities including collection of advances | 224 | 183 |
| Cash acquired from mergers and acquisitions | 754 | 0 |
| Net cash used in investing activities | (9,446) | (9,281) |
| CASH FLOWS FROM FINANCING ACTIVITIES |  |  |
| Additions to long-term debt | 217 | 136 |
| Reductions in long-term debt | (1,142) | (6) |
| Reductions in short-term debt | (2,771) | (172) |
| Additions/(reductions) in debt with three months or less maturity | (6) | (172) |
| Contingent consideration payments | (27) | (68) |
| Cash dividends to ExxonMobil shareholders | (8,093) | (7,439) |
| Cash dividends to noncontrolling interests | (397) | (293) |
| Changes in noncontrolling interests | 16 | 11 |
| Common stock acquired | (8,337) | (8,680) |
```

- xbrl_0145: 25224 in non-gold 0000034088-24-000050:265.0:265.0 [Exxon Mobil Corporation (XOM) | 10-Q | Q2 FY2024 | Part I, Item 2: MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS] | | Operating activities |  |  | 25,224 | 25,724 |
- xbrl_0145: 25224 in non-gold 0000034088-25-000042:291.0:291.0 [Exxon Mobil Corporation (XOM) | 10-Q | Q2 FY2025 | Part I, Item 2: MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS] | | Operating activities |  |  | 24,503 | 25,224 |
