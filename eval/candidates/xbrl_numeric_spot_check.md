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
