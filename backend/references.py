"""TEa source reference index."""

REFERENCES: dict[str, dict] = {
    "CLIA": {
        "full_name": "Clinical Laboratory Improvement Amendments (CLIA '88)",
        "organization": "Centers for Medicare & Medicaid Services (CMS), USA",
        "description": (
            "US federal regulatory standards for clinical laboratory testing. "
            "CLIA '88 defines proficiency testing (PT) criteria for acceptable performance, "
            "used as TEa limits for a wide range of analytes."
        ),
        "url": "https://www.cms.gov/regulations-and-guidance/legislation/clia",
        "document": "42 CFR Part 493 — Laboratory Requirements",
        "year": "1988 (updated periodically)",
        "category": "Regulatory",
    },
    "BV": {
        "full_name": "Biological Variation (Desirable Analytical Quality Specifications)",
        "organization": "European Federation of Clinical Chemistry and Laboratory Medicine (EFLM)",
        "description": (
            "TEa derived from biological variation (BV) data. "
            "Desirable imprecision: CV ≤ 0.5 × CVi; desirable bias: |Bias| ≤ 0.25 × (CVi² + CVg²)^0.5; "
            "desirable TEa = bias + 1.65 × CV. "
            "Based on the Ricos et al. database, maintained by the EFLM Biological Variation Task Group."
        ),
        "url": "https://biologicalvariation.eu/",
        "document": "EFLM Biological Variation Database",
        "year": "Continuously updated",
        "category": "Biological Variation",
    },
    "NCEP": {
        "full_name": "National Cholesterol Education Program",
        "organization": "National Heart, Lung, and Blood Institute (NHLBI), USA",
        "description": (
            "Analytical performance goals for lipid testing published by NCEP. "
            "Defines TEa for Total Cholesterol (≤10%), HDL (≤13%), LDL (≤12%), and Triglycerides (≤15%). "
            "Widely adopted as the gold standard for lipid panel quality requirements."
        ),
        "url": "https://www.nhlbi.nih.gov/health-topics/blood-cholesterol",
        "document": "NCEP Recommendations for Measurement of Low-Density Lipoprotein Cholesterol",
        "year": "1995 (ATP III update 2002)",
        "category": "Clinical Guidelines",
    },
    "NGSP": {
        "full_name": "National Glycohemoglobin Standardization Program",
        "organization": "NGSP, USA (coordinated with IFCC)",
        "description": (
            "Standardization program for HbA1c measurement traceable to the DCCT reference method. "
            "Defines TEa of ≤6% for HbA1c to ensure consistent diagnosis and monitoring of diabetes. "
            "All certified instruments must demonstrate compliance with NGSP performance criteria."
        ),
        "url": "https://www.ngsp.org/",
        "document": "NGSP Network Performance Criteria",
        "year": "1996 (updated annually)",
        "category": "Standardization Program",
    },
    "RCPA": {
        "full_name": "Royal College of Pathologists of Australasia Quality Assurance Programs",
        "organization": "RCPA QAP, Australia",
        "description": (
            "Australian/New Zealand EQA program defining allowable limits of performance (ALP) "
            "for clinical chemistry, hematology, and immunology analytes. "
            "Values reflect consensus of analytical and clinical needs in the Australasian context."
        ),
        "url": "https://www.rcpaqap.com.au/",
        "document": "RCPA QAP Allowable Limits of Performance",
        "year": "Updated annually",
        "category": "EQA / Proficiency Testing",
    },
    "ESFEQA": {
        "full_name": "Spanish Society of Laboratory Medicine EQA Program",
        "organization": "Sociedad Española de Medicina de Laboratorio (SEQCML), Spain",
        "description": (
            "EQA-derived analytical quality specifications from the Spanish national EQA program. "
            "TEa values for hematology analytes (e.g. MCV) are commonly referenced from SEQCML "
            "publications and used across European laboratory networks."
        ),
        "url": "https://www.seqcml.com/",
        "document": "SEQCML EQA Performance Specifications",
        "year": "Updated periodically",
        "category": "EQA / Proficiency Testing",
    },
    "KDIGO": {
        "full_name": "Kidney Disease: Improving Global Outcomes",
        "organization": "KDIGO International",
        "description": (
            "International clinical practice guidelines for CKD evaluation and management. "
            "Defines analytical performance requirements for eGFR reporting, requiring "
            "serum creatinine assays traceable to IDMS reference method with TEa ≤±20%."
        ),
        "url": "https://kdigo.org/guidelines/ckd-evaluation-and-management/",
        "document": "KDIGO 2024 CKD Guideline",
        "year": "2024",
        "category": "Clinical Guidelines",
    },
    "CLIA 2024": {
        "full_name": "CLIA Proficiency Testing Criteria (2024 revision)",
        "organization": "Centers for Medicare & Medicaid Services (CMS), USA",
        "description": (
            "Updated 2024 revision of CLIA PT criteria, incorporating revised TEa values "
            "for hematology analytes including CBC parameters. "
            "Used as primary TEa source for hematology QC in this platform."
        ),
        "url": "https://www.ecfr.gov/current/title-42/chapter-IV/subchapter-G/part-493",
        "document": "42 CFR Part 493 Subpart H — Proficiency Testing Programs by Specialty and Subspecialty",
        "year": "2024",
        "category": "Regulatory",
    },
    "Westgard": {
        "full_name": "Westgard QC — Sigma Metric & Analytical Quality Resources",
        "organization": "Westgard QC, Inc., USA",
        "description": (
            "Comprehensive QC education and analytical quality resource by James O. Westgard. "
            "Provides TEa goals from Biological Variation (Ricos database), CLIA PT criteria, "
            "and Westgard's own recommendations for Sigma-metric QC planning. "
            "Includes the Sigma Metric QC database, OPSpecs charts, and Westgard Rules reference — "
            "used globally as the foundation for laboratory quality management."
        ),
        "url": "https://www.westgard.com",
        "document": "Westgard QC Online Resources (BV Database, Sigma Metric Tools, QC Rules)",
        "year": "Continuously updated",
        "category": "QC Resources / Education",
        "sub_links": [
            {"label": "Biological Variation Database", "url": "https://www.westgard.com/biodatabase1.htm"},
            {"label": "CLIA Analytical Quality Requirements", "url": "https://www.westgard.com/clia-requirements-for-analytical-quality.htm"},
            {"label": "Westgard Rules & Multirules", "url": "https://www.westgard.com/westgard-rules-and-multirules.htm"},
            {"label": "Sigma Metric QC Design", "url": "https://www.westgard.com/sigma-metric-qc-design.htm"},
            {"label": "OPSpecs Charts", "url": "https://www.westgard.com/opspecs-charts.htm"},
        ],
    },
}

CATEGORY_ORDER = [
    "Regulatory",
    "Biological Variation",
    "Clinical Guidelines",
    "Standardization Program",
    "EQA / Proficiency Testing",
    "QC Resources / Education",
]
