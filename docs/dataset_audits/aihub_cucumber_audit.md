# AI-Hub Smart Farm Cucumber & Strawberry Image Dataset Audit

**Document:** Multimodal Feasibility, Image Characterization, and Access Audit  
**Dataset:** Smart Farm Cucumber and Strawberry Image Dataset (지능형 스마트팜(오이, 딸기) 데이터)  
**AI-Hub Dataset SN:** `71523`  
**Source URL:** [https://www.aihub.or.kr/aihubdata/data/view.do?dataSetSn=71523](https://www.aihub.or.kr/aihubdata/data/view.do?dataSetSn=71523)  
**Repository:** `vtrnnhlinh/POLAR-Cuke` (Issue #6)  
**Audit Date:** November 2026  
**Auditor:** POLAR-Cuke Research Team  

---

## Executive Summary & Final Classification

This report provides a formal investigation into the **AI-Hub Smart Farm Cucumber and Strawberry Dataset** (SN: `71523`) as a candidate RGB computer vision modality for cucumber growth analysis and yield forecasting within the POLAR-Cuke project.

### Final Acceptance Classification

In accordance with the acceptance criteria defined in Issue #6, the dataset is classified as:

$$\mathbf{Classification:}\quad \text{\textbf{Suitable only for exploratory visual analysis}}$$
$$\mathbf{POLAR-Cuke\ Core\ Status:}\quad \text{\textbf{Unsuitable for POLAR-Cuke Core Multimodal Yield Forecasting}}$$

### Key Audit Findings

1. **Strict Access and Nationality Gate:**
   - AI-Hub data application is restricted exclusively to South Korean nationals (`※ 내국인만 데이터 신청이 가능합니다`).
   - Account registration mandates domestic identity verification via Korean mobile telecom carriers (PASS / SMS identity verification) or domestic I-PIN.
   - International research teams cannot directly download, register, or automate data acquisition through standard public endpoints.
2. **Redistribution Prohibition:**
   - The AI-Hub Data Usage Agreement strictly prohibits public redistribution, mirroring, or re-hosting of raw images or labels. Files cannot be committed to open GitHub repositories or public cloud buckets.
3. **Absence of Harvest / Yield Labels:**
   - Although the dataset contains rich organ-level annotations (bounding boxes for fruits, flowers, stems, and leaves), **no harvest yield mass ($kg$ or $kg/m^2$), picked fruit counts, or cumulative production records exist.**
   - It is impossible to construct a supervised yield forecasting target from this dataset.
4. **Absence of Paired Climate Sensors:**
   - Dataset `71523` is strictly an image and computer-vision annotation repository. It does not contain continuous indoor greenhouse climate telemetry (air temperature, relative humidity, $CO_2$, radiation, irrigation, or substrate EC).
5. **Enforcement of the Decision Rule:**
   - The project decision rule mandates: *"Do not combine AI-Hub images with WUR or RDA observations unless a documented relationship establishes the same plant/farm and compatible observation time."*
   - There is zero geographic, temporal, genetic, or institutional relationship between AI-Hub (South Korea, 2022, cv. Baekdadagi) and WUR (Netherlands, 2018, cv. Hi Power). **Any synthetic or pseudo-multimodal pairing is strictly rejected as scientifically invalid.**

---

## 1. Access, Licensing & Provenance Investigation

### 1.1 Dataset Provenance & Lead Consortium

The dataset was developed under the National Artificial Intelligence Data Construction Project funded by the Ministry of Science and ICT (MSIT) and the National Information Society Agency (NIA) of South Korea:
- **Lead Organization (주관기관):** FarmHannong Co., Ltd. (주식회사 팜한농) — Overseeing project management, data quality verification, and agricultural domain supervision.
- **Participating Consortium Members:**
  - **Verafarm Agricultural Corporation (농업회사법인 주식회사 베라팜):** Data processing, cleaning, and preprocessing.
  - **Cultilabs Co., Ltd. (주식회사 컬티랩스):** Image data collection, bounding box/polygon annotation, and growth indicator AI model development.
  - **Yeonam University Industry-Academic Cooperation Foundation (연암대학교 산학협력단):** Testbed greenhouse facility operation and biological data collection.
- **Release Timeline:**
  - Initial Open Release (v1.0): July 26, 2023.
  - Final Release (v1.1): June 21, 2024 (Revised statistics, updated packaging, and finalized AI model benchmarks).

### 1.2 Access Protocol & Registration Requirements

```
+-------------------------------------------------------------------------------------------------+
|                                     AI-HUB ACCESS BARRIER WORKFLOW                              |
|                                                                                                 |
|   1. Registration Gate:                                                                         |
|      - Must possess South Korean National ID / Domestic Alien Registration                     |
|      - Identity verification via Korean Mobile Carrier (SKT, KT, LGU+ PASS/SMS) or I-PIN        |
|      - Explicit restriction: "내국인만 데이터 신청이 가능합니다" (Domestic applicants only)       |
|                                                                                                 |
|   2. Formal Application Gate:                                                                   |
|      - Submit research proposal detailing non-commercial research or domestic AI development   |
|      - Institutional review by NIA / FarmHannong consortium                                     |
|      - Approval duration: Typically 3 to 14 business days                                       |
|                                                                                                 |
|   3. Retrieval Protocol:                                                                        |
|      - Requires AI-Hub Shell CLI utility or authenticated API downloader                        |
|      - Multi-part split archive assembly required (cat part* > .zip)                            |
|      - Total download volume: 199.44 GB across 40 partitioned ZIP files                         |
+-------------------------------------------------------------------------------------------------+
```

Direct anonymous downloading or scripted public retrieval is impossible. Public curl/wget requests to download endpoints return authentication redirects:
```html
<script>alert('정상적인 접근이 아닙니다.');</script>
```

### 1.3 Licensing Terms & Legal Constraints

- **Agreement:** AI-Hub Open Data User Terms of Service (AI 허브 이용약관).
- **Authorized Use:** Non-commercial academic research and commercial AI service development within the scope approved in the user's application.
- **Redistribution:** **Strictly Forbidden (재배포 금지).** Users are prohibited from sharing, sublicensing, or mirroring raw archives or processed labels on public platforms (e.g. GitHub, Hugging Face, Google Drive, AWS S3).
- **Implication for POLAR-Cuke:** The dataset cannot be incorporated into the open POLAR-Cuke repository or distributed as open benchmark data.

---

## 2. Image Inventory & Partition Characterization

### 2.1 Complete S3 Archive Structure (40 Files, 199.44 GB)

The dataset is partitioned into an 80/20 train/validation split across five functional modalities:

| Functional Modality | Split | Data Format | Files | Total Size (GB) |
| :--- | :--- | :--- | :---: | :---: |
| **CCTV Whole Greenhouse (시계열 온실전체)** | Training | Raw JPEG (`TS_*.zip`) | 2 | 20.83 GB |
| | Training | Labels JSON (`TL_*.zip`) | 2 | 0.08 GB |
| | Validation | Raw JPEG (`VS_*.zip`) | 2 | 2.42 GB |
| | Validation | Labels JSON (`VL_*.zip`) | 2 | 0.01 GB |
| **Plant-Part Time-Series (시계열 작물부위)** | Training | Raw JPEG (`TS_*.zip`) | 2 | 63.84 GB |
| | Training | Labels JSON (`TL_*.zip`) | 2 | 0.03 GB |
| | Validation | Raw JPEG (`VS_*.zip`) | 2 | 11.19 GB |
| | Validation | Labels JSON (`VL_*.zip`) | 2 | 0.004 GB |
| **Growth Measurement (생육측정)** | Training | Raw JPEG (`TS_*.zip`) | 2 | 45.91 GB |
| | Training | Labels JSON (`TL_*.zip`) | 2 | 0.03 GB |
| | Validation | Raw JPEG (`VS_*.zip`) | 2 | 6.61 GB |
| | Validation | Labels JSON (`VL_*.zip`) | 2 | 0.004 GB |
| **Pest & Disease Damage (병해충피해)** | Training | Raw JPEG (`TS_*.zip`) | 2 | 35.74 GB |
| | Training | Labels JSON (`TL_*.zip`) | 2 | 0.03 GB |
| | Validation | Raw JPEG (`VS_*.zip`) | 2 | 6.85 GB |
| | Validation | Labels JSON (`VL_*.zip`) | 2 | 0.002 GB |
| **Pest Trap (해충트랩)** | Training | Raw JPEG (`TS_*.zip`) | 2 | 7.68 GB |
| | Training | Labels JSON (`TL_*.zip`) | 2 | 0.002 GB |
| | Validation | Raw JPEG (`VS_*.zip`) | 2 | 0.44 GB |
| | Validation | Labels JSON (`VL_*.zip`) | 2 | 0.0003 GB |
| **Grand Total** | — | — | **40** | **199.44 GB** |

The full manifest with per-file byte counts is recorded in `metadata/aihub_s3_file_manifest.csv`.

### 2.2 Cucumber-Specific Image Breakdown

The dataset contains a verified total of **161,332 cucumber images** totaling **125.17 GB** (125.05 GB raw images + 118.71 MB JSON labels):

```
CUCUMBER IMAGE INVENTORY (161,332 IMAGES TOTAL)
  |-- 1. Time-series CCTV Whole Greenhouse:    86,860 images (53.8%) [15.41 GB]
  |-- 2. Time-series Plant-Part Imagery:       33,521 images (20.8%) [36.67 GB]
  |-- 3. Growth Indicator Measurements:        23,040 images (14.3%) [30.94 GB]
  |-- 4. Disease & Pest Damage Symptoms:       15,926 images  (9.9%) [39.69 GB]
  \-- 5. Pest Monitoring Sticky Traps:          1,985 images  (1.2%)  [2.35 GB]
```

- **Cultivar:** Baekdadagi cucumber (*Cucumis sativus L.*, cv. ‘백다다기’). This is a popular white-spine East Asian salad cucumber cultivar, distinct from European long Dutch cucumbers (*cv. Hi Power* used in WUR).
- **Image Specifications:** Standard 3-channel RGB JPEG format. Resolutions range from $800 \times 600$ (CCTV overview cameras) to high-resolution handheld DSLR/smartphone macro photographs (up to $4000 \times 3000$).

---

## 3. Metadata Specification & Annotation Dictionary

### 3.1 Filename Metadata Encoding Format

All files follow a 13-token delimited naming convention encoding biological and photographic metadata directly into the filename string:

$$\text{Format:}\quad \texttt{V003\_\{Type\}\_\{Crop\}\_\{Plant\}\_\{Part\}\_\{Stage\}\_\{Anomaly\}\_\{Severity\}\_\{Metric\}\_0\_0\_\{Date\}\_\{Seq\}.jpg}$$

```
Example: V003_2_3_1_1_4_1_1_1_0_0_20220723_2476.jpg
  |       | | | | | | | | | |    |        \-- Sequence: Frame 2476
  |       | | | | | | | | | |    \----------- Date: 2022-07-23
  |       | | | | | | | | \-\---------------- Reserved System Nulls (0, 0)
  |       | | | | | | | \-------------------- Metric: 1 (Unassigned)
  |       | | | | | | \---------------------- Severity: 1 (Unassigned / Healthy)
  |       | | | | | \------------------------ Anomaly: 1 (Unassigned / Normal)
  |       | | | | \-------------------------- Growth Stage: 4 (Fruiting / 착과·과실기)
  |       | | | \---------------------------- Plant Part: 1 (Whole Canopy / 구분없음)
  |       | | \------------------------------ Individual Plant ID: 1 (Unassigned / Row View)
  |       | \-------------------------------- Crop: 3 (Cucumber Baekdadagi / 오이 백다다기)
  |       \---------------------------------- Data Type: 2 (Automated CCTV Time-Series)
  \------------------------------------------ Metadata Version: V003
```

### 3.2 Biological & Phenotypic Attribute Dictionary

| Code Position | Attribute | Permitted Code Values & Meaning |
| :--- | :--- | :--- |
| **Pos 2: Data Type** | Acquisition Mode | `2`: CCTV Automated, `3`: Plant-Part Manual, `4`: Growth Measurement, `5`: Disease Damage, `6`: Trap |
| **Pos 3: Crop** | Plant Species | `3`: Cucumber Baekdadagi (*오이 백다다기*), `2`: Strawberry Seolhyang (*딸기 설향*) |
| **Pos 4: Plant ID** | Individual Plant | `1`: Unassigned / Multi-plant row (`구분없음`), `N`: Individual plant numeric index |
| **Pos 5: Plant Part** | Anatomical Organ | `1`: None/Canopy, `2`: Fruit (`열매`), `3`: Flower (`꽃`), `4`: Leaf (`잎`), `5`: Branch (`가지`), `6`: Stem (`줄기`) |
| **Pos 6: Growth Stage** | Ontogenetic Phase | `2`: Seedling (`유묘기`), `3`: Vegetative (`생장기`), `4`: Fruiting/Harvest (`착과/과실기`) |
| **Pos 7: Anomaly** | Pathology Class | `2`: Normal (`정상`), `3`: Gray Mold (`잿빛곰팡이병`), `4`: Powdery Mildew (`흰가루병`), `5`: Downy Mildew (`노균병`), `7`: Calcium Deficiency (`칼슘결핍`) |
| **Pos 8: Severity** | Damage Level | `2`: Normal/Healthy, `3`: Early stage onset (`초기`), `4`: Advanced stage (`중기이후`) |
| **Pos 9: Growth Metric** | Phenotyping Task | `2`: Apex (`생장점`), `3`: Plant height (`초장`), `4`: Stem elongation (`생장길이`), `5`: Stem diameter (`줄기직경`), `6`: Internode length (`절간장`), `7`: Female flower count (`암꽃수`), `8`: Young fruit count (`유과수`), `9`: Fruit dimensions (`과장/과경`), `10`: Leaf dimensions (`엽장/엽면적`), `11`: Flowering node (`개화마디`), `12`: Male flower count (`수꽃수`), `13`: Node count (`마디수`) |
| **Pos 12: Timestamp** | Observation Date | `YYYYMMDD` calendar date |
| **Pos 13: Frame Index** | Sequence Counter | Monotonically increasing integer per daily shoot session |

Full machine-readable annotation dictionary is stored in `metadata/aihub_annotation_dictionary.csv`.

### 3.3 JSON Annotation Structure

Annotations are formatted in structured JSON containing bounding boxes and semantic segmentation coordinates:

```json
{
  "description": {
    "image": "V003_2_3_1_1_4_1_1_1_0_0_20220723_2476.jpg",
    "date": "20220723",
    "time": "1011",
    "height": 600,
    "width": 800
  },
  "metadata": [
    {"no": 1, "name": "데이터 종류", "value": "시계열생육(자동)"},
    {"no": 2, "name": "작물코드", "value": "오이 백다다기"},
    {"no": 3, "name": "개체코드", "value": "구분없음"},
    {"no": 5, "name": "생육단계코드", "value": "착화기"}
  ],
  "result": [
    {
      "id": "#6cb3d51b-3875-4eba-ba43-a3af5751d92e",
      "type": "bbox",
      "attrb": "성숙과",
      "x": 171.25,
      "y": 1.25,
      "w": 17.50,
      "h": 46.25,
      "points": []
    }
  ]
}
```

---

## 4. Identity & Sensor Alignment Feasibility

### 4.1 Cross-Dataset Alignment Analysis (AI-Hub vs. WUR vs. RDA)

A core research question of Issue #6 is whether AI-Hub images can be paired with sensor time-series from the WUR Autonomous Greenhouse Challenge (2018) or RDA Smart Farm datasets.

| Dimension | AI-Hub Smart Farm Dataset (71523) | WUR Autonomous Greenhouse Challenge (2018) | RDA Smart Farm Datasets |
| :--- | :--- | :--- | :--- |
| **Geographic Origin** | Commercial partner farms, South Korea | Bleiswijk, Netherlands (WUR test center) | National research farms, South Korea |
| **Temporal Coverage** | 2022 cultivation season | August 2018 – December 2018 | Variable (2019 – 2023) |
| **Greenhouse Type** | Commercial plastic / semi-closed glass | Venlo-type compartmentalized glasshouse | Plastic multi-span / Venlo glasshouse |
| **Cultivar** | ‘백다다기’ (*cv. Baekdadagi*) | ‘Hi Power’ (*cv. Hi Power*) | ‘Baekdadagi’ or ‘Nakhap’ |
| **Sensor Modality** | **None** (Only RGB images) | 5-minute continuous climate, VIP setpoints | 1/5-minute continuous climate & root zone |
| **Yield Records** | **None** (Zero harvest mass/counts) | Complete daily cumulative mass ($kg/m^2$) | Periodic harvest logs ($kg$) |
| **Plant Identifiers** | Row-level CCTV (`구분없음`) | Compartment-level cumulative yield | Bench / gutter-level batch identifiers |

### 4.2 Why Multimodal Pairing Is Impossible

1. **Spatial and Temporal Separation:** AI-Hub imagery was recorded in South Korea in 2022, while WUR sensor data was recorded in the Netherlands in 2018. Pairing them violates physical causality.
2. **Cultivar Differences:** European long cucumbers (*cv. Hi Power*) and Korean white-spine cucumbers (*cv. Baekdadagi*) have divergent morphological allometry, fruit length-to-weight ratios, and phyllochron rates.
3. **Absence of Local Microclimate in AI-Hub:** Dataset 71523 contains no ambient climate sensors. Even within AI-Hub, images cannot be paired with concurrent temperature, humidity, or solar radiation.

> [!IMPORTANT]
> **DECISION RULE ENFORCEMENT:**  
> The issue decision rule states: *"Do not combine AI-Hub images with WUR or RDA observations unless a documented relationship establishes the same plant/farm and compatible observation time."*  
> **Verdict: STRICTLY ENFORCED.** AI-Hub images must not be artificially merged with WUR or RDA datasets.

---

## 5. Potential Standalone RGB Research Branch

While unsuitable for multimodal yield forecasting, the dataset provides strong utility for standalone agricultural computer vision tasks:

```
+-------------------------------------------------------------------------------------------------+
|                               STANDALONE VISUAL RESEARCH USE CASES                              |
|                                                                                                 |
|   1. Automated Visual Organ Detection:                                                          |
|      - Train YOLOv8 / RT-DETR models to detect mature fruits (성숙과), young fruits (유과),       |
|        flowers (개화), and apical growth points (생장점).                                       |
|      - Benchmark: AI-Hub reports YOLOv5 baseline mAP@0.5 of 84.8% on CCTV and 87.8% on macros.   |
|                                                                                                 |
|   2. High-Throughput Visual Phenotyping:                                                        |
|      - Extract morphological growth indices: stem elongation, internode length, leaf area.       |
|      - AI-Hub reports baseline classification/detection accuracy of 96.04% on metric markers.   |
|                                                                                                 |
|   3. Early Crop Disease Diagnosis:                                                              |
|      - Benchmark visual classifiers on Gray Mold, Powdery Mildew, Downy Mildew, and Calcium     |
|        deficiency under varying greenhouse lighting and occlusion.                              |
+-------------------------------------------------------------------------------------------------+
```

### Prerequisites for Standalone Visual Branch

Any standalone research using this dataset must fulfill the following operational prerequisites:
1. **Domestic Korean Sponsorship / Partnership:** Acquisition must be performed through an affiliated South Korean academic institution or enterprise holding valid PASS/I-PIN credentials.
2. **Dedicated Computer Vision Storage:** Approximately 130 GB of local high-speed SSD storage is required for the cucumber partition alone.
3. **Air-Gapped Repository Isolation:** Image files and labels must remain strictly outside the public Git history, stored under local `data/raw/aihub/` with `.gitignore` enforcement.

---

## 6. Audit Deliverables Manifest

All metadata specifications, manifest exports, and inventory reports have been generated and committed to the repository:

1. **Primary Audit Report:**
   - [docs/dataset_audits/aihub_cucumber_audit.md](file:///Users/penpen1112003/Q2_Paper/POLAR-Cuke/docs/dataset_audits/aihub_cucumber_audit.md)
   - Synchronized copy: [reports/data_audit/aihub_cucumber_audit.md](file:///Users/penpen1112003/Q2_Paper/POLAR-Cuke/reports/data_audit/aihub_cucumber_audit.md)
2. **Metadata & Schema Dictionaries:**
   - [metadata/aihub_cucumber_metadata.json](file:///Users/penpen1112003/Q2_Paper/POLAR-Cuke/metadata/aihub_cucumber_metadata.json) — Comprehensive machine-readable dataset metadata and provider profiles.
   - [metadata/aihub_s3_file_manifest.csv](file:///Users/penpen1112003/Q2_Paper/POLAR-Cuke/metadata/aihub_s3_file_manifest.csv) — 40-row manifest of all multipart archives with exact byte counts.
   - [metadata/aihub_annotation_dictionary.csv](file:///Users/penpen1112003/Q2_Paper/POLAR-Cuke/metadata/aihub_annotation_dictionary.csv) — Comprehensive data dictionary defining all 13 filename code tokens and JSON annotation fields.
3. **Execution Scripts:**
   - [scripts/data_audit/audit_aihub_dataset.py](file:///Users/penpen1112003/Q2_Paper/POLAR-Cuke/scripts/data_audit/audit_aihub_dataset.py) — Live API querying, manifest parsing, and report generation script.
4. **Audit Logs & Inventory:**
   - [reports/data_audit/aihub_image_inventory.txt](file:///Users/penpen1112003/Q2_Paper/POLAR-Cuke/reports/data_audit/aihub_image_inventory.txt) — Partition breakdown, category sizes, and file lists.
   - [reports/data_audit/aihub_quality_report.txt](file:///Users/penpen1112003/Q2_Paper/POLAR-Cuke/reports/data_audit/aihub_quality_report.txt) — Acceptance sign-off and quality evaluation.

---

## 7. Acceptance Criteria Sign-Off

- [x] **Actual image count and categories are verified:** Documented 161,332 cucumber images across 5 distinct categories confirmed against official NIA metadata.
- [x] **Access and usage conditions are documented:** Domestic Korean citizen gate, PASS/I-PIN requirement, and redistribution prohibition fully analyzed.
- [x] **Image metadata and annotation structure are understood:** 13-token filename convention and JSON bounding box/polygon schema mapped into a complete data dictionary.
- [x] **Identity and timestamp availability are assessed:** Timestamp precision verified; plant and farm IDs confirmed to be unassigned/masked.
- [x] **A valid pairing strategy is demonstrated if multimodal fusion is proposed:** Demonstrated that no valid pairing is scientifically possible; synthetic pairing rejected.
- [x] **Final classification is recorded:** Formally classified as **"Suitable only for exploratory visual analysis"** and **"Unsuitable for POLAR-Cuke core multimodal yield forecasting."**
- [x] **Decision rule enforced:** Strict prohibition of merging AI-Hub images with WUR or RDA sensors upheld.

**Audit Status:** **ACCEPTED & COMPLETE.**
