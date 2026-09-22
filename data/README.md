# MedGuard Local Datasets

This directory contains the local, offline datasets utilized by MedGuard for medicine identification, brand normalization, and drug-drug interaction screening.

---

## 1. Prototype Dataset Disclaimer & Scope

> **CLINICAL NOTICE & DISCLAIMER**
> 
> The data files contained here represent a **curated prototype dataset** assembled for demonstration and competition evaluation in the **iQOO Hackathon 2026 HealthTech track**.
> 
> - This is **NOT** an exhaustive or comprehensive clinical pharmacology database.
> - Absence of an interaction in this dataset does **NOT** imply that a combination is safe.
> - MedGuard is a screening prototype, not a medical device or diagnostic system.
> - Patients and caregivers must always confirm medication plans with a qualified doctor or pharmacist.

---

## 2. Files Overview

### `interactions.json`
Contains 25 clinically documented, high-risk drug interaction pairs.
Each record follows a strict schema:

```json
{
  "drug_a": "canonical generic name (lowercase)",
  "drug_b": "canonical generic name (lowercase)",
  "severity": "high | moderate",
  "mechanism": "Pharmacological / pharmacokinetic / pharmacodynamic mechanism",
  "plain_language": "Clear, accessible explanation written for patients and caregivers",
  "source": "Traceable clinical reference (e.g., BNF 84 / FDA Package Insert / Stockley's Drug Interactions)"
}
```

#### Order Independence
MedGuard matches pairs symmetrically. A query for `(drug_a, drug_b)` produces the identical result as `(drug_b, drug_a)`.

#### Provenance
Every record has been cross-referenced against established drug references:
- **British National Formulary (BNF 84)**
- **FDA Drug Safety Communications & Official Package Inserts**
- **Stockley's Drug Interactions**
- **American Heart Association (AHA) Clinical Guidelines**

No records use unverified or fabricated citations.

---

### `brand_generic_map.json`
Contains over 60 mappings connecting common Indian and global commercial brand names to canonical, lowercase generic active ingredients.

Examples:
- `Crocin`, `Dolo 650`, `Calpol` &rarr; `paracetamol`
- `Combiflam`, `Brufen`, `Advil` &rarr; `ibuprofen`
- `Ecosprin`, `Disprin` &rarr; `aspirin`
- `Lipitor`, `Atorva`, `Storvas` &rarr; `atorvastatin`
- `Pan-D`, `Pantocid` &rarr; `pantoprazole`
- `Augmentin`, `Moxikind-CV` &rarr; `amoxicillin-clavulanate`
- `Cetzine`, `Zyrtec` &rarr; `cetirizine`
- `Glycomet`, `Glucophage` &rarr; `metformin`

---

## 3. Data Integrity & Validation

To verify the syntax, deduplication, schema completeness, and mapping validity of these files, run:

```bash
python scripts/validate_data.py
```
