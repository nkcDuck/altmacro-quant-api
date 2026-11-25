# Data Governance, Provenance & Commercial Licensing

**API Product:** Alternative Macro & Economic Indices (`altmacro-quant-api` / RapidAPI v1.2.0)  
**Provider:** AltMacro Quant Data (engineered by stalter, <https://stalter.work>)  
**Public Gateway:** `https://alternative-macro-economic-indices.p.rapidapi.com`

---

## 1. Zero Synthetic Data Policy & Point-in-Time Integrity

All 15 quantitative indicators published by the Alternative Macro & Economic Indices API are built exclusively from **official institutional endpoints** (`FRED®`, Board of Governors of the Federal Reserve System H.10 FX, U.S. BLS / JOLTS, U.S. BEA, U.S. Census Bureau, U.S. EIA, U.S. DOT, U.S. SEC EDGAR XBRL, The Economist Big Mac Index dataset, and World Bank Pink Sheet Commodity Markets).

### Enforced Data-Integrity Controls
1. **Zero Synthetic / Placeholder Records:**
   - Every index in `ALT_INDICES_COMPLIANCE_REGISTRY` enforces `commercialApiReady: true` and `usesYahooFinance: false`.
   - Static compliance tests enforce zero `yahoo-finance2` dependencies and zero defunct London PM Fix (`GOLDAMGBD228NLBM`) references across all 15 fetchers; SEC EDGAR calls identify a valid institutional `User-Agent` (`help@stalter.work`).
2. **Legacy Unverified Gold Fallback Purge (`isLegacyUnverifiedGoldFallback`):**
   - Historical ingestion sanitization automatically discards unverified placeholder records before normalization or commercial delivery:
     - `gold-oil`: drops any record missing `goldSource` with the legacy placeholder gold price (`2750`)
     - `copper-gold`: drops any record missing `goldSource` with the legacy placeholder gold price (`2700`)
3. **Strict Non-Fallback Calendar Semantics (`month` vs. `asOf`):**
   - `month=YYYY-MM` performs an **exact calendar match**. When an index has no publication for that month, the API returns `null` / `[]` / `stance: "no-data"` — **never** silent carry-forward or synthetic interpolation.
   - `asOf=YYYY-MM` performs an **explicit point-in-time snapshot** (`dataMonth <= YYYY-MM`), selecting the newest verified observation published on or before the requested month (or empty if none exist).
   - `fromMonth=YYYY-MM` and `toMonth=YYYY-MM` select an inclusive monthly window (`fromMonth <= dataMonth <= toMonth`).

---

## 2. Four Analytical Dimensions & Categories

| Dimension | Category Slug | Dimension Name | Member Slugs |
|---:|---|---|---|
| 1 | `consumer` | Micro Consumer Psychology & Downward Substitution | `lipstick`, `underwear`, `rv-leisure`, `alcohol-scissors` |
| 2 | `manufacturing` | Physical Manufacturing, Packaging & Capex | `cardboard`, `heavy-truck`, `electricity-pulse`, `skyscraper` |
| 3 | `commodities` | Cross-Border PPP & Macro Commodity Pricing | `bigmac`, `copper-gold`, `gold-oil`, `breakfast-inflation` |
| 4 | `labor-credit` | Labor Psychology, Credit & Comfort Demand | `quits-confidence`, `vegas-credit`, `comfort-food` |

---

## 3. Complete 15-Index Upstream Source, License Class & Redaction Matrix

Every index enforces `commercialApiReady: true` and `usesYahooFinance: false`.

| Slug | Index Name (`nameEn`) | Dim | License Class | Upstream Source ID | Provider | Upstream License | Raw Redistribution | Upstream URL | Redacted Commercial Fields |
|---|---|---:|---|---|---|---|---|---|---|
| `bigmac` | Big Mac PPP Index | 3 | `CC_BY_4_0_DERIVED` | `big-mac-full-index.csv` | The Economist | CC BY 4.0 | `allowed-with-attribution` | <https://github.com/TheEconomist/big-mac-data> | `[]` |
| `bigmac` | Big Mac PPP Index | 3 | `CC_BY_4_0_DERIVED` | `FRED:H.10 (14 FX series)` | Board of Governors of the Federal Reserve System (US) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/categories/94> | `[]` |
| `lipstick` | Lipstick Index | 1 | `PUBLIC_DOMAIN_US_GOV` | `SEC_EDGAR_XBRL` | U.S. SEC (EDGAR) — CIK 0001001250 (EL), 0001024305 (COTY), 0001403568 (ULTA) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://www.sec.gov/edgar/sec-api-documentation> | `[]` |
| `lipstick` | Lipstick Index | 1 | `PUBLIC_DOMAIN_US_GOV` | `FRED:CPIAUCSL+GDPC1` | U.S. BLS & U.S. BEA (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/> | `[]` |
| `underwear` | Men's Underwear Index | 1 | `PUBLIC_DOMAIN_US_GOV` | `FRED:MRTSSM4481USS` | U.S. Census Bureau (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/MRTSSM4481USS> | `[]` |
| `underwear` | Men's Underwear Index | 1 | `PUBLIC_DOMAIN_US_GOV` | `FRED:CUSR0000SAA1` | U.S. BLS (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/CUSR0000SAA1> | `[]` |
| `cardboard` | Cardboard Box Index | 2 | `PUBLIC_DOMAIN_US_GOV` | `FRED:IPN32221S` | Board of Governors of the Federal Reserve System (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/IPN32221S> | `[]` |
| `cardboard` | Cardboard Box Index | 2 | `PUBLIC_DOMAIN_US_GOV` | `FRED:PCU322211322211` | U.S. BLS (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/PCU322211322211> | `[]` |
| `heavy-truck` | Heavy Truck & Freight Index | 2 | `PUBLIC_DOMAIN_US_GOV` | `FRED:HTRUCKSSAAR` | U.S. BEA (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/HTRUCKSSAAR> | `[]` |
| `heavy-truck` | Heavy Truck & Freight Index | 2 | `PUBLIC_DOMAIN_US_GOV` | `FRED:TSIFRGHT` | U.S. Bureau of Transportation Statistics (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/TSIFRGHT> | `[]` |
| `heavy-truck` | Heavy Truck & Freight Index | 2 | `PUBLIC_DOMAIN_US_GOV` | `FRED:GASDESW` | U.S. EIA (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/GASDESW> | `[]` |
| `copper-gold` | Copper-to-Gold Ratio Index | 3 | `MIXED_OPEN_DERIVED_ONLY` | `FRED:PCOPPUSDM` | International Monetary Fund / LME (via FRED) | IMF Open Data Terms (Derived Index Permissible; Raw Redacted in Commercial API) | `derived-only` | <https://fred.stlouisfed.org/series/PCOPPUSDM> | raw copper spot quote, raw gold spot quote |
| `copper-gold` | Copper-to-Gold Ratio Index | 3 | `MIXED_OPEN_DERIVED_ONLY` | `WB:PINK_SHEET_GOLD\|FRED:IQ12260` | World Bank Commodity Markets (Fallback: U.S. BLS) | CC BY 4.0 (World Bank) / U.S. Public Domain (BLS) | `allowed-with-attribution` | <https://www.worldbank.org/en/research/commodity-markets> | raw copper spot quote, raw gold spot quote |
| `copper-gold` | Copper-to-Gold Ratio Index | 3 | `MIXED_OPEN_DERIVED_ONLY` | `FRED:DGS10` | Board of Governors of the Federal Reserve System (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/DGS10> | raw copper spot quote, raw gold spot quote |
| `rv-leisure` | RV & Leisure Durable Index | 1 | `PUBLIC_DOMAIN_US_GOV` | `FRED:RSMVPD\|MRTSSM441USS` | U.S. Census Bureau (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/RSMVPD> | `[]` |
| `rv-leisure` | RV & Leisure Durable Index | 1 | `PUBLIC_DOMAIN_US_GOV` | `FRED:CUSR0000SAD` | U.S. BLS (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/CUSR0000SAD> | `[]` |
| `rv-leisure` | RV & Leisure Durable Index | 1 | `PUBLIC_DOMAIN_US_GOV` | `FRED:TERMCBAUTO48NS` | Board of Governors of the Federal Reserve System (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/TERMCBAUTO48NS> | `[]` |
| `alcohol-scissors` | Champagne & Alcohol Scissors Index | 1 | `PUBLIC_DOMAIN_US_GOV` | `FRED:MRTSSM4453USN` | U.S. Census Bureau (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/MRTSSM4453USN> | `[]` |
| `alcohol-scissors` | Champagne & Alcohol Scissors Index | 1 | `PUBLIC_DOMAIN_US_GOV` | `FRED:MRTSSM722USN` | U.S. Census Bureau (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/MRTSSM722USN> | `[]` |
| `alcohol-scissors` | Champagne & Alcohol Scissors Index | 1 | `PUBLIC_DOMAIN_US_GOV` | `FRED:CUSR0000SAF116` | U.S. BLS (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/CUSR0000SAF116> | `[]` |
| `electricity-pulse` | Industrial Electricity Pulse Index | 2 | `PUBLIC_DOMAIN_US_GOV` | `FRED:IPG2211S` | Board of Governors of the Federal Reserve System (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/IPG2211S> | `[]` |
| `electricity-pulse` | Industrial Electricity Pulse Index | 2 | `PUBLIC_DOMAIN_US_GOV` | `FRED:CAPUTLG2211S` | Board of Governors of the Federal Reserve System (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/CAPUTLG2211S> | `[]` |
| `electricity-pulse` | Industrial Electricity Pulse Index | 2 | `PUBLIC_DOMAIN_US_GOV` | `FRED:IPMAN` | Board of Governors of the Federal Reserve System (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/IPMAN> | `[]` |
| `skyscraper` | Skyscraper Capex Cycle Index | 2 | `PUBLIC_DOMAIN_US_GOV` | `FRED:TLCOMCONS` | U.S. Census Bureau (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/TLCOMCONS> | `[]` |
| `skyscraper` | Skyscraper Capex Cycle Index | 2 | `PUBLIC_DOMAIN_US_GOV` | `FRED:TTLCONS` | U.S. Census Bureau (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/TTLCONS> | `[]` |
| `skyscraper` | Skyscraper Capex Cycle Index | 2 | `PUBLIC_DOMAIN_US_GOV` | `FRED:DRCRELEXFACBS` | Board of Governors of the Federal Reserve System (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/DRCRELEXFACBS> | `[]` |
| `gold-oil` | Gold-to-Oil Ratio & Stagflation Radar | 3 | `MIXED_OPEN_DERIVED_ONLY` | `FRED:DCOILWTICO` | U.S. EIA (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/DCOILWTICO> | raw gold spot quote |
| `gold-oil` | Gold-to-Oil Ratio & Stagflation Radar | 3 | `MIXED_OPEN_DERIVED_ONLY` | `WB:PINK_SHEET_GOLD\|FRED:IQ12260` | World Bank Commodity Markets (Fallback: U.S. BLS) | CC BY 4.0 (World Bank) / U.S. Public Domain (BLS) | `allowed-with-attribution` | <https://www.worldbank.org/en/research/commodity-markets> | raw gold spot quote |
| `gold-oil` | Gold-to-Oil Ratio & Stagflation Radar | 3 | `MIXED_OPEN_DERIVED_ONLY` | `FRED:T10YIE` | Federal Reserve Bank of St. Louis (FRED) | U.S. Gov / Federal Reserve Open Statistical Data | `allowed` | <https://fred.stlouisfed.org/series/T10YIE> | raw gold spot quote |
| `breakfast-inflation` | Breakfast Table Inflation Basket | 3 | `PUBLIC_DOMAIN_US_GOV` | `FRED:APU0000708111` | U.S. BLS (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/APU0000708111> | `[]` |
| `breakfast-inflation` | Breakfast Table Inflation Basket | 3 | `PUBLIC_DOMAIN_US_GOV` | `FRED:APU0000717311` | U.S. BLS (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/APU0000717311> | `[]` |
| `breakfast-inflation` | Breakfast Table Inflation Basket | 3 | `PUBLIC_DOMAIN_US_GOV` | `FRED:APU0000704111` | U.S. BLS (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/APU0000704111> | `[]` |
| `quits-confidence` | JOLTS Quits Confidence Index | 4 | `PUBLIC_DOMAIN_US_GOV` | `FRED:JTSQUR` | U.S. BLS (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/JTSQUR> | `[]` |
| `quits-confidence` | JOLTS Quits Confidence Index | 4 | `PUBLIC_DOMAIN_US_GOV` | `FRED:JTSLDR` | U.S. BLS (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/JTSLDR> | `[]` |
| `quits-confidence` | JOLTS Quits Confidence Index | 4 | `PUBLIC_DOMAIN_US_GOV` | `FRED:JTSJOR` | U.S. BLS (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/JTSJOR> | `[]` |
| `vegas-credit` | Vegas Hospitality & Card Credit Stress | 4 | `PUBLIC_DOMAIN_US_GOV` | `FRED:LASV832LEIH` | U.S. BLS (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/LASV832LEIH> | `[]` |
| `vegas-credit` | Vegas Hospitality & Card Credit Stress | 4 | `PUBLIC_DOMAIN_US_GOV` | `FRED:DRCCLACBS` | Board of Governors of the Federal Reserve System (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/DRCCLACBS> | `[]` |
| `vegas-credit` | Vegas Hospitality & Card Credit Stress | 4 | `PUBLIC_DOMAIN_US_GOV` | `FRED:REVOLSL` | Board of Governors of the Federal Reserve System (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/REVOLSL> | `[]` |
| `comfort-food` | Cocoa & Comfort Food Resilience Index | 4 | `MIXED_OPEN_DERIVED_ONLY` | `FRED:PCOCOUSDM` | International Monetary Fund / ICCO (via FRED) | IMF Open Data Terms (Derived Index Permissible; Raw Redacted in Commercial API) | `derived-only` | <https://fred.stlouisfed.org/series/PCOCOUSDM> | raw cocoa spot quote |
| `comfort-food` | Cocoa & Comfort Food Resilience Index | 4 | `MIXED_OPEN_DERIVED_ONLY` | `FRED:CUSR0000SEFR` | U.S. BLS (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/CUSR0000SEFR> | raw cocoa spot quote |
| `comfort-food` | Cocoa & Comfort Food Resilience Index | 4 | `MIXED_OPEN_DERIVED_ONLY` | `FRED:IPG311S` | Board of Governors of the Federal Reserve System (via FRED) | U.S. Gov Public Domain (17 U.S.C. § 105) | `allowed` | <https://fred.stlouisfed.org/series/IPG311S> | raw cocoa spot quote |

---

## 4. Commercial Raw-Quote Sanitization (`sanitizeIndexRecordForCommercialApi`)

Before any observation leaves the commercial gateway, `sanitizeIndexRecordForCommercialApi(slug, record)` shallow-clones the observation and deletes restricted third-party spot-quote fields (`redactedRawFieldsForCommercialApi`) while preserving all derived macroeconomic signals, ratios, YoY deltas, Z-scores, and metadata:

| Index Slug | License Class | Stripped Raw Fields | Preserved Derived Commercial Fields |
|---|---|---|---|
| `copper-gold` | `MIXED_OPEN_DERIVED_ONLY` | raw copper spot quote, raw gold spot quote | `ratio`, `ratioYoY`, `treasury10Y`, `divergence`, `goldSource`, `indexValue`, `signal`, `trend`, `rawScore`, `zScore`, `dataMonth`, `formulaVersion`, `timestamp` |
| `gold-oil` | `MIXED_OPEN_DERIVED_ONLY` | raw gold spot quote | `goldOilRatio`, `goldOilRatioYoY`, `wtiOilPrice`, `breakeven10Y`, `goldSource`, `indexValue`, `signal`, `trend`, `rawScore`, `zScore`, `dataMonth`, `formulaVersion`, `timestamp` |
| `comfort-food` | `MIXED_OPEN_DERIVED_ONLY` | raw cocoa spot quote | `cocoaYoY`, `sweetsCpiYoY`, `foodProductionYoY`, `indexValue`, `signal`, `trend`, `rawScore`, `zScore`, `dataMonth`, `formulaVersion`, `timestamp` |
| Remaining 12 indices | `PUBLIC_DOMAIN_US_GOV` / `CC_BY_4_0_DERIVED` | None (`[]`) | All derived index fields, Z-scores, signals, trends, and Big Mac PPP country/FX metrics |

---

## 5. Mandatory Legal Attributions & Redistribution Policy

### Verbatim Upstream Attributions (`LEGAL_ATTRIBUTIONS`)

- **FRED_API_NOTICE:**
  > `This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis.`
- **ECONOMIST_BIGMAC_NOTICE:**
  > `Contains local price data adapted from The Economist Big Mac Index dataset (CC BY 4.0).`
- **WORLD_BANK_PINK_SHEET_NOTICE:**
  > `Contains commodity benchmark data adapted from World Bank Commodity Price Data (The Pink Sheet, CC BY 4.0).`
- **IMF_NON_ENDORSEMENT_NOTICE:**
  > `Derived indices incorporate IMF Primary Commodity Price System series retrieved via FRED; IMF does not endorse this product.`
- **SEC_EDGAR_NOTICE:**
  > `Corporate revenue fundamentals are parsed from public U.S. SEC EDGAR XBRL filings.`
- **NON_INVESTMENT_ADVICE_DISCLAIMER:**
  > `For macroeconomic, statistical, and quantitative research purposes only. Does not constitute investment advice, securities recommendations, or regulated advisory services.`

### API Output License & Redistribution Policy

- **API Output License:** `CC BY 4.0 (Stalter Derived Quantitative Output)` (<https://creativecommons.org/licenses/by/4.0/>)
- **Redistribution Policy:**
  > `Authorized for personal quantitative research, algorithmic backtesting, and internal AI agent workflows under RapidAPI Basic/Pro/Ultra plans. Commercial newsletter republication and raw upstream resale are prohibited.`
