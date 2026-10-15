# Data sources

The advisor needs two kinds of knowledge:

1. **Science:** what the studies say about an ingredient.
2. **Products:** which ingredients a product contains, and how much of each.

They have very different answers.

---

## 1. Scientific context

**What:** fetch studies about an active ingredient, keep the useful metadata, and give the model only the relevant parts, with citations.

**Free sources (official APIs, no scraping):**

| Source | What you get | Notes |
|---|---|---|
| **PubMed E-utilities** (NCBI) | Abstracts, title, journal, year, **publication type** (RCT, meta-analysis, review) | Free. 3 requests/s without a key, 10/s with a free key |
| **Europe PMC REST API** | Same papers plus **full text for the open-access subset** | Free, no key |
| **CosIng** (EU) | Regulatory status and **maximum allowed concentrations** (e.g. preservatives, UV filters, salicylic acid) | Good for safety guardrails |

**Two ways to use them** (agentic RAG):

- **Pre-built index:** for the ~15 core actives (retinoids, vitamin C, niacinamide, azelaic acid, AHAs/BHAs, SPF filters, ceramides...), fetch the studies once, **grade the evidence** (meta-analysis > RCT > open-label > in vitro), chunk, embed, store. Fast, consistent and curated.
- **Live search tool:** a `search_studies(ingredient, concern)` tool the model calls for anything outside the index. Covers the long tail, but it is slower, rate-limited and ungraded.
- **Recommendation: both.** The index answers most questions well. The tool is the fallback. Which one to use is the agent's decision.

---

## 2. Product ingredients and percentages

**The honest answer: you can usually get the ingredient list, but rarely the percentages.**

- **The law helps with the list.** EU and UK rules (Regulation 1223/2009) require the full **INCI ingredient list** on the pack. Ingredients **above 1% are listed in descending order of concentration**, and those at **1% or less can follow in any order**. The US has similar labelling.
- **Percentages are usually trade secrets.** The exceptions are:
  - brands that state the active, e.g. "Niacinamide 10% + Zinc 1%" (The Ordinary, Paula's Choice, etc.);
  - regulated actives with legal caps (CosIng), which give an upper bound.
- So the product can show **"listed / estimated / stated by brand"**, never a made-up number. That honesty is part of the product, and a good interview talking point.

**Where to get the lists:**

| Source | Good | Bad |
|---|---|---|
| **Open Beauty Facts** (open database, sister of Open Food Facts) | Free API, ingredient lists by barcode, open licence | Patchy coverage, crowd-sourced |
| **User pastes the ingredient list, or a photo of the label** | Always available, legal, exactly their product | Needs a parser (and a vision model for photos) |
| **Amazon Product Advertising API** | Title, price, images, your affiliate link | Ingredients are not a reliable field. Access needs an approved affiliate account with some sales (from memory, to verify when we build it) |
| INCIDecoder / Skinsort / CosDNA | Great lists | No public API. Scraping is against their terms, so **don't** |

**Recommendation:** split the jobs.
- **Ingredients:** come from the user's paste (and later photo) and Open Beauty Facts.
- **The science:** comes from the index.
- **Amazon:** only provides the "buy" link and price, after the advice is made, with an affiliate disclosure.
