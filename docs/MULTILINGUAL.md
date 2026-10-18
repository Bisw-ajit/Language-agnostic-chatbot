# Multilingual Pipeline & Natural Language Processing

## Overview
The Language Agnostic Chatbot is specifically engineered to handle the linguistic realities of Indian e-governance:
1. **Odia (ଓଡ଼ିଆ)**: Native Odia script with complex inflectional morphology and postpositions.
2. **Hindi (हिन्दी)**: Formal standard Hindi in Devanagari script.
3. **Hinglish (hi-en)**: Colloquial Hindi transliterated in Latin script with high spelling variance.
4. **English (en)**: Official administrative English.

---

## 1. Script Analysis & Language Detection

Language identification (`backend/language/detector.py`) uses a two-tier approach:

### Tier 1: Unicode Script Classification
- Characters in `\u0b00-\u0b7f` directly identify **Odia** script.
- Characters in `\u0900-\u097f` directly identify **Devanagari** (Hindi).

### Tier 2: Latin Script Disambiguation (English vs Hinglish)
When Latin script is detected, the classifier scans for high-frequency Hinglish marker tokens:
- Pronouns & verbs: *aap*, *kya*, *kaise*, *chahiye*, *hoga*, *hai*, *nahi*, *karna*, *milta*, *yojana*, *paisa*, *batao*.
- Ratio heuristic: If Hinglish vocabulary exceeds 15% of content tokens, the language is identified as `hi-en` (Hinglish); otherwise `en` (English).

---

## 2. Odia Morphological Stemmer

Odia nouns frequently take case-marking suffixes and postpositions that impair exact keyword search. `backend/language/normalizer.py` implements an Odia suffix stemmer covering 14 common markers:

| Suffix (Odia) | Transliteration | Grammatical Meaning | Example Word → Stem |
|---|---|---|---|
| ରେ | -re | Locative / Instrumental ("in", "by") | କାଳିଆରେ → କାଳିଆ |
| କୁ / କୁଁ | -ku / -kum | Dative / Accusative ("to", "for") | ଚାଷୀଙ୍କୁ → ଚାଷୀ |
| ର / ଙ୍କର | -ra / -nkara | Genitive ("of") | ସରକାରଙ୍କର → ସରକାର |
| ଠାରୁ / ଠାରେ | -tharu / -thare | Ablative / Locative ("from", "at") | ପୋର୍ଟାଲଠାରୁ → ପୋର୍ଟାଲ |
| ମାନଙ୍କ | -mananka | Plural Genitive | ହିତାଧିକାରୀମାନଙ୍କ → ହିତାଧିକାରୀ |

During multilingual tokenization, both the original token and the stemmed lemma are indexed in BM25, significantly boosting recall for inflected forms.

---

## 3. Hinglish Canonical Normalization

Users spell Hinglish phonetically with extensive spelling variation. The pipeline normalizes non-standard transliterations to canonical forms prior to lexical search:

| User Variant | Canonical Form | Meaning |
|---|---|---|
| `kyaa`, `kia` | `kya` | what |
| `chaiye`, `chahiyea`, `chaheye` | `chahiye` | needed / required |
| `muje`, `muze`, `hmko` | `mujhe` | to me |
| `krna`, `karne` | `karna` | to do |
| `hogaa`, `hogi` | `hoga` | will happen / be |
| `kaise`, `kese` | `kaise` | how |
| `batao`, `btado`, `btao` | `batao` | tell |
| `aavedan`, `abedan` | `aavedan` | application |

---

## 4. Cross-Language Semantic Bridging

Because `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` embeds queries and documents into a shared multi-lingual latent space, an Odia or Hinglish query directly matches English official policy text chunks when semantic concepts align, eliminating the latency and error accumulation of machine translation pre-passes.
