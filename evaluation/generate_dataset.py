import json
import os

def create_dataset():
    data = [
        # ==========================================
        # 1. ENGLISH QUERIES (25 Questions)
        # ==========================================
        {
            "id": "en_kalia_01",
            "language": "en",
            "question": "What is the financial assistance provided under KALIA Yojana?",
            "expected_intent": "benefits",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Financial Assistance & Support",
            "expected_answer_facts": ["10,000", "small farmers", "marginal farmers", "installments"],
            "should_answer": True,
            "equiv_group": "kalia_amount"
        },
        {
            "id": "en_kalia_02",
            "language": "en",
            "question": "Who is eligible for KALIA Yojana in Odisha?",
            "expected_intent": "eligibility",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["resident of Odisha", "small and marginal farmers", "landless agricultural laborers"],
            "should_answer": True,
            "equiv_group": "kalia_eligibility"
        },
        {
            "id": "en_kalia_03",
            "language": "en",
            "question": "What documents are required to apply for KALIA scheme?",
            "expected_intent": "documents",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Required Documents",
            "expected_answer_facts": ["Aadhaar card", "bank passbook", "land records"],
            "should_answer": True,
            "equiv_group": "kalia_docs"
        },
        {
            "id": "en_kalia_04",
            "language": "en",
            "question": "How to apply online for KALIA scheme?",
            "expected_intent": "procedure",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Application Process & Grievance",
            "expected_answer_facts": ["kalia.odisha.gov.in", "online portal", "Mo Seva Kendra"],
            "should_answer": True,
            "equiv_group": "kalia_apply"
        },
        {
            "id": "en_kalia_05",
            "language": "en",
            "question": "Can landless agricultural households get assistance under KALIA?",
            "expected_intent": "eligibility",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["landless", "livelihood support", "12,500"],
            "should_answer": True,
            "equiv_group": "kalia_landless"
        },
        {
            "id": "en_kalia_06",
            "language": "en",
            "question": "What is the official helpline number for KALIA yojana?",
            "expected_intent": "contact",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Application Process & Grievance",
            "expected_answer_facts": ["1800", "toll-free", "helpline"],
            "should_answer": True
        },
        {
            "id": "en_bsky_01",
            "language": "en",
            "question": "What is BSKY Health Card coverage limit?",
            "expected_intent": "benefits",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Financial Coverage & Entitlements",
            "expected_answer_facts": ["5 lakh", "10 lakh", "women family members"],
            "should_answer": True,
            "equiv_group": "bsky_coverage"
        },
        {
            "id": "en_bsky_02",
            "language": "en",
            "question": "Who is eligible for BSKY health benefits?",
            "expected_intent": "eligibility",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Eligibility & Beneficiary Criteria",
            "expected_answer_facts": ["NFSA", "SFSA", "ration card holders", "Odisha resident"],
            "should_answer": True,
            "equiv_group": "bsky_eligibility"
        },
        {
            "id": "en_bsky_03",
            "language": "en",
            "question": "Is treatment free in government hospitals under BSKY?",
            "expected_intent": "benefits",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Scope of Healthcare Coverage",
            "expected_answer_facts": ["free treatment", "all government hospitals", "cashless"],
            "should_answer": True
        },
        {
            "id": "en_bsky_04",
            "language": "en",
            "question": "What documents are needed for BSKY cashless hospital admission?",
            "expected_intent": "documents",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Required Documentation & Verification",
            "expected_answer_facts": ["BSKY Smart Card", "Aadhaar Card", "Ration Card"],
            "should_answer": True,
            "equiv_group": "bsky_docs"
        },
        {
            "id": "en_bsky_05",
            "language": "en",
            "question": "Are empanelled private hospitals covered under BSKY?",
            "expected_intent": "procedure",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Scope of Healthcare Coverage",
            "expected_answer_facts": ["empanelled private hospitals", "inside and outside Odisha", "cashless"],
            "should_answer": True
        },
        {
            "id": "en_mbpy_01",
            "language": "en",
            "question": "How much monthly pension is given under Madhu Babu Pension Yojana?",
            "expected_intent": "benefits",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Pension Rates & Financial Assistance",
            "expected_answer_facts": ["500", "700", "per month", "60 to 79 years", "80 years"],
            "should_answer": True,
            "equiv_group": "mbpy_amount"
        },
        {
            "id": "en_mbpy_02",
            "language": "en",
            "question": "What is the age requirement for Madhu Babu Pension Yojana?",
            "expected_intent": "eligibility",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["60 years or above", "destitute", "disability"],
            "should_answer": True,
            "equiv_group": "mbpy_age"
        },
        {
            "id": "en_mbpy_03",
            "language": "en",
            "question": "Who can get pension under MBPY besides elderly persons?",
            "expected_intent": "eligibility",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["widows", "persons with disabilities", "transgender persons", "unmarried women"],
            "should_answer": True
        },
        {
            "id": "en_mbpy_04",
            "language": "en",
            "question": "What documents are required to apply for MBPY pension?",
            "expected_intent": "documents",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Required Documents & Application",
            "expected_answer_facts": ["Age proof", "income certificate", "disability certificate", "Aadhaar"],
            "should_answer": True,
            "equiv_group": "mbpy_docs"
        },
        {
            "id": "en_mbpy_05",
            "language": "en",
            "question": "What is the maximum annual family income limit for MBPY eligibility?",
            "expected_intent": "eligibility",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["24,000", "annual income", "BPL"],
            "should_answer": True
        },
        {
            "id": "en_sch_01",
            "language": "en",
            "question": "What scholarships are provided under Odisha State Scholarship Portal?",
            "expected_intent": "benefits",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Scholarship Schemes & Financial Benefits",
            "expected_answer_facts": ["Post Matric Scholarship", "Pre Matric", "e-Medhabruti", "tuition assistance"],
            "should_answer": True,
            "equiv_group": "sch_types"
        },
        {
            "id": "en_sch_02",
            "language": "en",
            "question": "What are the eligibility criteria for Odisha Post-Matric Scholarship?",
            "expected_intent": "eligibility",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Eligibility Requirements",
            "expected_answer_facts": ["SC/ST/OBC/SEBC", "resident of Odisha", "family income limit"],
            "should_answer": True,
            "equiv_group": "sch_eligibility"
        },
        {
            "id": "en_sch_03",
            "language": "en",
            "question": "What documents are required on Odisha scholarship portal?",
            "expected_intent": "documents",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Required Documents & Portal Verification",
            "expected_answer_facts": ["Aadhaar", "caste certificate", "income certificate", "mark sheet", "bank account"],
            "should_answer": True,
            "equiv_group": "sch_docs"
        },
        {
            "id": "en_sch_04",
            "language": "en",
            "question": "How is scholarship money disbursed to students in Odisha?",
            "expected_intent": "procedure",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Disbursement & Direct Benefit Transfer",
            "expected_answer_facts": ["DBT", "Direct Benefit Transfer", "Aadhaar linked bank account"],
            "should_answer": True
        },
        {
            "id": "en_sch_05",
            "language": "en",
            "question": "What is the official website for applying to Odisha scholarships?",
            "expected_intent": "procedure",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Application Process",
            "expected_answer_facts": ["scholarship.odisha.gov.in", "State Scholarship Portal"],
            "should_answer": True
        },
        {
            "id": "en_ood_01",
            "language": "en",
            "question": "What is the syllabus for Harvard Computer Science CS50 course?",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        },
        {
            "id": "en_ood_02",
            "language": "en",
            "question": "What is the current estimated population of planet Mars?",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        },
        {
            "id": "en_ood_03",
            "language": "en",
            "question": "Can you write me a python script to play tic-tac-toe?",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        },
        {
            "id": "en_ood_04",
            "language": "en",
            "question": "Who scored the winning goal in yesterday's UEFA Champions League match?",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        },

        # ==========================================
        # 2. HINDI QUERIES (25 Questions)
        # ==========================================
        {
            "id": "hi_kalia_01",
            "language": "hi",
            "question": "कालिया योजना के तहत किसानों को कितनी वित्तीय सहायता मिलती है?",
            "expected_intent": "benefits",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Financial Assistance & Support",
            "expected_answer_facts": ["10,000", "छोटे और सीमांत किसान", "किस्तों"],
            "should_answer": True,
            "equiv_group": "kalia_amount"
        },
        {
            "id": "hi_kalia_02",
            "language": "hi",
            "question": "ओडिशा में कालिया योजना के लिए कौन पात्र है?",
            "expected_intent": "eligibility",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["ओडिशा का स्थायी निवासी", "छोटे और सीमांत किसान"],
            "should_answer": True,
            "equiv_group": "kalia_eligibility"
        },
        {
            "id": "hi_kalia_03",
            "language": "hi",
            "question": "कालिया योजना में आवेदन करने के लिए कौन से दस्तावेज आवश्यक हैं?",
            "expected_intent": "documents",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Required Documents",
            "expected_answer_facts": ["आधार कार्ड", "बैंक पासबुक", "जमीन के कागजात"],
            "should_answer": True,
            "equiv_group": "kalia_docs"
        },
        {
            "id": "hi_kalia_04",
            "language": "hi",
            "question": "कालिया योजना के लिए ऑनलाइन आवेदन कैसे करें?",
            "expected_intent": "procedure",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Application Process & Grievance",
            "expected_answer_facts": ["kalia.odisha.gov.in", "ऑनलाइन पोर्टल", "मो सेवा केंद्र"],
            "should_answer": True,
            "equiv_group": "kalia_apply"
        },
        {
            "id": "hi_kalia_05",
            "language": "hi",
            "question": "क्या भूमिहीन कृषि मजदूर कालिया योजना का लाभ ले सकते हैं?",
            "expected_intent": "eligibility",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["भूमिहीन", "आजीविका सहायता", "12,500"],
            "should_answer": True,
            "equiv_group": "kalia_landless"
        },
        {
            "id": "hi_bsky_01",
            "language": "hi",
            "question": "बीजू स्वास्थ्य कल्याण योजना (BSKY) में कितनी स्वास्थ्य कवरेज मिलती है?",
            "expected_intent": "benefits",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Financial Coverage & Entitlements",
            "expected_answer_facts": ["5 लाख", "10 लाख", "महिला सदस्यों"],
            "should_answer": True,
            "equiv_group": "bsky_coverage"
        },
        {
            "id": "hi_bsky_02",
            "language": "hi",
            "question": "BSKY स्वास्थ्य योजना का लाभ किसे मिल सकता है?",
            "expected_intent": "eligibility",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Eligibility & Beneficiary Criteria",
            "expected_answer_facts": ["राशन कार्ड", "NFSA", "SFSA", "ओडिशा निवासी"],
            "should_answer": True,
            "equiv_group": "bsky_eligibility"
        },
        {
            "id": "hi_bsky_03",
            "language": "hi",
            "question": "BSKY कार्ड के लिए कौन से दस्तावेज जरूरी हैं?",
            "expected_intent": "documents",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Required Documentation & Verification",
            "expected_answer_facts": ["आधार कार्ड", "राशन कार्ड", "स्मार्ट कार्ड"],
            "should_answer": True,
            "equiv_group": "bsky_docs"
        },
        {
            "id": "hi_bsky_04",
            "language": "hi",
            "question": "क्या BSKY के तहत निजी अस्पतालों में कैशलेस इलाज उपलब्ध है?",
            "expected_intent": "procedure",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Scope of Healthcare Coverage",
            "expected_answer_facts": ["सूचीबद्ध निजी अस्पताल", "कैशलेस", "ओडिशा"],
            "should_answer": True
        },
        {
            "id": "hi_bsky_05",
            "language": "hi",
            "question": "सरकारी अस्पतालों में BSKY के क्या लाभ हैं?",
            "expected_intent": "benefits",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Scope of Healthcare Coverage",
            "expected_answer_facts": ["निःशुल्क उपचार", "सभी सरकारी अस्पताल", "दवाएं"],
            "should_answer": True
        },
        {
            "id": "hi_mbpy_01",
            "language": "hi",
            "question": "मधु बाबू पेंशन योजना के तहत कितनी मासिक पेंशन मिलती है?",
            "expected_intent": "benefits",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Pension Rates & Financial Assistance",
            "expected_answer_facts": ["500", "700", "प्रति माह", "60 से 79 वर्ष", "80 वर्ष"],
            "should_answer": True,
            "equiv_group": "mbpy_amount"
        },
        {
            "id": "hi_mbpy_02",
            "language": "hi",
            "question": "मधु बाबू पेंशन योजना के लिए न्यूनतम आयु क्या है?",
            "expected_intent": "eligibility",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["60 वर्ष", "निराश्रित", "दिव्यांग"],
            "should_answer": True,
            "equiv_group": "mbpy_age"
        },
        {
            "id": "hi_mbpy_03",
            "language": "hi",
            "question": "MBPY पेंशन के लिए कौन से दस्तावेज चाहिए?",
            "expected_intent": "documents",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Required Documents & Application",
            "expected_answer_facts": ["आयु प्रमाण", "आय प्रमाण पत्र", "आधार कार्ड", "बैंक पासबुक"],
            "should_answer": True,
            "equiv_group": "mbpy_docs"
        },
        {
            "id": "hi_mbpy_04",
            "language": "hi",
            "question": "क्या विधवा और दिव्यांग व्यक्ति मधु बाबू पेंशन के लिए आवेदन कर सकते हैं?",
            "expected_intent": "eligibility",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["विधवा", "दिव्यांग", "पात्रता"],
            "should_answer": True
        },
        {
            "id": "hi_mbpy_05",
            "language": "hi",
            "question": "मधु बाबू पेंशन योजना के लिए पारिवारिक आय की सीमा क्या है?",
            "expected_intent": "eligibility",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["24,000", "वार्षिक आय"],
            "should_answer": True
        },
        {
            "id": "hi_sch_01",
            "language": "hi",
            "question": "ओडिशा राज्य छात्रवृत्ति पोर्टल पर कौन सी छात्रवृत्तियां उपलब्ध हैं?",
            "expected_intent": "benefits",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Scholarship Schemes & Financial Benefits",
            "expected_answer_facts": ["पोस्ट मैट्रिक", "प्री मैट्रिक", "मेधावृत्ति"],
            "should_answer": True,
            "equiv_group": "sch_types"
        },
        {
            "id": "hi_sch_02",
            "language": "hi",
            "question": "ओडिशा पोस्ट-मैट्रिक स्कॉलरशिप के लिए पात्रता शर्तें क्या हैं?",
            "expected_intent": "eligibility",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Eligibility Requirements",
            "expected_answer_facts": ["SC/ST/OBC", "ओडिशा निवासी", "आय सीमा"],
            "should_answer": True,
            "equiv_group": "sch_eligibility"
        },
        {
            "id": "hi_sch_03",
            "language": "hi",
            "question": "ओडिशा छात्रवृत्ति आवेदन के लिए कौन से प्रमाण पत्र आवश्यक हैं?",
            "expected_intent": "documents",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Required Documents & Portal Verification",
            "expected_answer_facts": ["जाति प्रमाण पत्र", "आय प्रमाण पत्र", "आधार कार्ड", "अंकतालिका"],
            "should_answer": True,
            "equiv_group": "sch_docs"
        },
        {
            "id": "hi_sch_04",
            "language": "hi",
            "question": "छात्रवृत्ति की राशि छात्रों के बैंक खाते में कैसे भेजी जाती है?",
            "expected_intent": "procedure",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Disbursement & Direct Benefit Transfer",
            "expected_answer_facts": ["DBT", "प्रत्यक्ष लाभ अंतरण", "आधार लिंक्ड बैंक खाता"],
            "should_answer": True
        },
        {
            "id": "hi_sch_05",
            "language": "hi",
            "question": "ओडिशा स्कॉलरशिप की आधिकारिक वेबसाइट क्या है?",
            "expected_intent": "procedure",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Application Process",
            "expected_answer_facts": ["scholarship.odisha.gov.in", "आधिकारिक पोर्टल"],
            "should_answer": True
        },
        {
            "id": "hi_ood_01",
            "language": "hi",
            "question": "जापान की राजधानी का क्या नाम है?",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        },
        {
            "id": "hi_ood_02",
            "language": "hi",
            "question": "मंगल ग्रह पर कुल कितने लोग रहते हैं?",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        },
        {
            "id": "hi_ood_03",
            "language": "hi",
            "question": "मुझे एक अच्छा हिंदी चुटकुला सुनाओ।",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        },
        {
            "id": "hi_ood_04",
            "language": "hi",
            "question": "क्वांटम भौतिकी के बुनियादी नियम क्या हैं?",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        },
        {
            "id": "hi_ood_05",
            "language": "hi",
            "question": "कल के क्रिकेट मैच में किसने शतक बनाया?",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        },

        # ==========================================
        # 3. HINGLISH QUERIES (25 Questions)
        # ==========================================
        {
            "id": "hing_kalia_01",
            "language": "hi-en",
            "question": "KALIA yojana me farmers ko kitna paisa milta hai?",
            "expected_intent": "benefits",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Financial Assistance & Support",
            "expected_answer_facts": ["10,000", "small farmers", "installments"],
            "should_answer": True,
            "equiv_group": "kalia_amount"
        },
        {
            "id": "hing_kalia_02",
            "language": "hi-en",
            "question": "KALIA scheme ke liye eligibility kya hai aur kaun apply kar sakta hai?",
            "expected_intent": "eligibility",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["Odisha resident", "small farmers", "marginal farmers"],
            "should_answer": True,
            "equiv_group": "kalia_eligibility"
        },
        {
            "id": "hing_kalia_03",
            "language": "hi-en",
            "question": "KALIA yojana me apply karne ke liye kaunse documents chahiye?",
            "expected_intent": "documents",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Required Documents",
            "expected_answer_facts": ["Aadhaar card", "bank passbook", "land records"],
            "should_answer": True,
            "equiv_group": "kalia_docs"
        },
        {
            "id": "hing_kalia_04",
            "language": "hi-en",
            "question": "KALIA yojana me online apply kaise kare?",
            "expected_intent": "procedure",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Application Process & Grievance",
            "expected_answer_facts": ["kalia.odisha.gov.in", "Mo Seva Kendra", "portal"],
            "should_answer": True,
            "equiv_group": "kalia_apply"
        },
        {
            "id": "hing_kalia_05",
            "language": "hi-en",
            "question": "kya landless laborers bhi KALIA ka benefit le sakte h?",
            "expected_intent": "eligibility",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["landless", "livelihood support", "12,500"],
            "should_answer": True,
            "equiv_group": "kalia_landless"
        },
        {
            "id": "hing_bsky_01",
            "language": "hi-en",
            "question": "BSKY health card me kitna coverage milta h?",
            "expected_intent": "benefits",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Financial Coverage & Entitlements",
            "expected_answer_facts": ["5 lakh", "10 lakh", "women family members"],
            "should_answer": True,
            "equiv_group": "bsky_coverage"
        },
        {
            "id": "hing_bsky_02",
            "language": "hi-en",
            "question": "BSKY health scheme ke liye kaun eligible hai?",
            "expected_intent": "eligibility",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Eligibility & Beneficiary Criteria",
            "expected_answer_facts": ["ration card", "NFSA", "SFSA", "Odisha"],
            "should_answer": True,
            "equiv_group": "bsky_eligibility"
        },
        {
            "id": "hing_bsky_03",
            "language": "hi-en",
            "question": "BSKY card ke liye kaun kon se document lagenge?",
            "expected_intent": "documents",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Required Documentation & Verification",
            "expected_answer_facts": ["Aadhaar", "Ration Card", "Smart Card"],
            "should_answer": True,
            "equiv_group": "bsky_docs"
        },
        {
            "id": "hing_bsky_04",
            "language": "hi-en",
            "question": "kya BSKY private hospital me bhi cashless treatment deta hai?",
            "expected_intent": "procedure",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Scope of Healthcare Coverage",
            "expected_answer_facts": ["empanelled private hospitals", "cashless"],
            "should_answer": True
        },
        {
            "id": "hing_bsky_05",
            "language": "hi-en",
            "question": "mujhe BSKY card ka main benefit batao",
            "expected_intent": "benefits",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Financial Coverage & Entitlements",
            "expected_answer_facts": ["free treatment", "government hospitals", "5 lakh"],
            "should_answer": True
        },
        {
            "id": "hing_mbpy_01",
            "language": "hi-en",
            "question": "Madhu Babu Pension Yojana me kitna pension milta hai har mahine?",
            "expected_intent": "benefits",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Pension Rates & Financial Assistance",
            "expected_answer_facts": ["500", "700", "monthly", "60 to 79", "80"],
            "should_answer": True,
            "equiv_group": "mbpy_amount"
        },
        {
            "id": "hing_mbpy_02",
            "language": "hi-en",
            "question": "Madhu Babu pension ke liye age limit kya hai?",
            "expected_intent": "eligibility",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["60 years", "destitute"],
            "should_answer": True,
            "equiv_group": "mbpy_age"
        },
        {
            "id": "hing_mbpy_03",
            "language": "hi-en",
            "question": "MBPY pension ke liye kon kon se documents chahiye?",
            "expected_intent": "documents",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Required Documents & Application",
            "expected_answer_facts": ["Age proof", "income certificate", "Aadhaar"],
            "should_answer": True,
            "equiv_group": "mbpy_docs"
        },
        {
            "id": "hing_mbpy_04",
            "language": "hi-en",
            "question": "kya disabled persons ko MBPY me pension milti hai?",
            "expected_intent": "eligibility",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["disability", "pension", "eligible"],
            "should_answer": True
        },
        {
            "id": "hing_mbpy_05",
            "language": "hi-en",
            "question": "MBPY pension scheme me family income limit kitni honi chahiye?",
            "expected_intent": "eligibility",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["24,000", "income limit"],
            "should_answer": True
        },
        {
            "id": "hing_sch_01",
            "language": "hi-en",
            "question": "Odisha state scholarship portal me kaunse scholarships milte hain?",
            "expected_intent": "benefits",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Scholarship Schemes & Financial Benefits",
            "expected_answer_facts": ["Post Matric", "Pre Matric", "Medhabruti"],
            "should_answer": True,
            "equiv_group": "sch_types"
        },
        {
            "id": "hing_sch_02",
            "language": "hi-en",
            "question": "Odisha Post-Matric scholarship ke liye kya eligibility criteria hai?",
            "expected_intent": "eligibility",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Eligibility Requirements",
            "expected_answer_facts": ["SC/ST/OBC", "Odisha resident", "income limit"],
            "should_answer": True,
            "equiv_group": "sch_eligibility"
        },
        {
            "id": "hing_sch_03",
            "language": "hi-en",
            "question": "Odisha scholarship form bharne ke liye kaunse certificates lagenge?",
            "expected_intent": "documents",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Required Documents & Portal Verification",
            "expected_answer_facts": ["caste certificate", "income certificate", "Aadhaar", "mark sheet"],
            "should_answer": True,
            "equiv_group": "sch_docs"
        },
        {
            "id": "hing_sch_04",
            "language": "hi-en",
            "question": "scholarship ka paisa bank account me kaise credit hota hai?",
            "expected_intent": "procedure",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Disbursement & Direct Benefit Transfer",
            "expected_answer_facts": ["DBT", "Direct Benefit Transfer", "Aadhaar linked"],
            "should_answer": True
        },
        {
            "id": "hing_sch_05",
            "language": "hi-en",
            "question": "Odisha scholarship portal ki official website link kya h?",
            "expected_intent": "procedure",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Application Process",
            "expected_answer_facts": ["scholarship.odisha.gov.in"],
            "should_answer": True
        },
        {
            "id": "hing_ood_01",
            "language": "hi-en",
            "question": "Mars pe kitni population rehti hai bhai?",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        },
        {
            "id": "hing_ood_02",
            "language": "hi-en",
            "question": "mujhe ek funny joke sunao na please",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        },
        {
            "id": "hing_ood_03",
            "language": "hi-en",
            "question": "Python me ek calculator app ka code likh do",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        },
        {
            "id": "hing_ood_04",
            "language": "hi-en",
            "question": "kal ka football match kisne jeeta tha?",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        },
        {
            "id": "hing_ood_05",
            "language": "hi-en",
            "question": "Japan ki capital city kaunsi hai?",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        },

        # ==========================================
        # 4. ODIA QUERIES (25 Questions)
        # ==========================================
        {
            "id": "or_kalia_01",
            "language": "or",
            "question": "କାଳିଆ ଯୋଜନାରେ ଚାଷୀମାନଙ୍କୁ କେତେ ଟଙ୍କାର ଆର୍ଥିକ ସହାୟତା ମିଳେ?",
            "expected_intent": "benefits",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Financial Assistance & Support",
            "expected_answer_facts": ["10,000", "କ୍ଷୁଦ୍ର ଚାଷୀ", "କିସ୍ତି"],
            "should_answer": True,
            "equiv_group": "kalia_amount"
        },
        {
            "id": "or_kalia_02",
            "language": "or",
            "question": "ଓଡ଼ିଶାରେ କାଳିଆ ଯୋଜନା ପାଇଁ କିଏ ଯୋଗ୍ୟ ଅଟନ୍ତି?",
            "expected_intent": "eligibility",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["ଓଡ଼ିଶାର ସ୍ଥାୟୀ ବାସିନ୍ଦା", "କ୍ଷୁଦ୍ର ଓ ନାମମାତ୍ର ଚାଷୀ"],
            "should_answer": True,
            "equiv_group": "kalia_eligibility"
        },
        {
            "id": "or_kalia_03",
            "language": "or",
            "question": "କାଳିଆ ଯୋଜନାରେ ଆବେଦନ କରିବା ପାଇଁ କେଉଁ କେଉଁ କାଗଜପତ୍ର ଆବଶ୍ୟକ?",
            "expected_intent": "documents",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Required Documents",
            "expected_answer_facts": ["ଆଧାର କାର୍ଡ", "ବ୍ୟାଙ୍କ ପାସବୁକ", "ଜମି ପଟ୍ଟା"],
            "should_answer": True,
            "equiv_group": "kalia_docs"
        },
        {
            "id": "or_kalia_04",
            "language": "or",
            "question": "କାଳିଆ ଯୋଜନା ପାଇଁ ଅନଲାଇନ୍ ଆବେଦନ କିପରି କରିବେ?",
            "expected_intent": "procedure",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Application Process & Grievance",
            "expected_answer_facts": ["kalia.odisha.gov.in", "ମୋ ସେବା କେନ୍ଦ୍ର"],
            "should_answer": True,
            "equiv_group": "kalia_apply"
        },
        {
            "id": "or_kalia_05",
            "language": "or",
            "question": "ଭୂମିହୀନ କୃଷି ଶ୍ରମିକମାନେ କାଳିଆ ଯୋଜନାରେ ସହାୟତା ପାଇପାରିବେ କି?",
            "expected_intent": "eligibility",
            "expected_document": "KALIA Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["ଭୂମିହୀନ", "ଜୀବିକା ସହାୟତା", "12,500"],
            "should_answer": True,
            "equiv_group": "kalia_landless"
        },
        {
            "id": "or_bsky_01",
            "language": "or",
            "question": "ବିଜୁ ସ୍ୱାସ୍ଥ୍ୟ କଲ୍ୟାଣ ଯୋଜନା (BSKY) ରେ କେତେ ଟଙ୍କାର ଚିକିତ୍ସା ସୁବିଧା ମିଳେ?",
            "expected_intent": "benefits",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Financial Coverage & Entitlements",
            "expected_answer_facts": ["୫ ଲକ୍ଷ", "୧୦ ଲକ୍ଷ", "ମହିଳା ସଦସ୍ୟ"],
            "should_answer": True,
            "equiv_group": "bsky_coverage"
        },
        {
            "id": "or_bsky_02",
            "language": "or",
            "question": "BSKY ସ୍ୱାସ୍ଥ୍ୟ ଯୋଜନା ପାଇଁ କିଏ ଯୋଗ୍ୟ ଅଟନ୍ତି?",
            "expected_intent": "eligibility",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Eligibility & Beneficiary Criteria",
            "expected_answer_facts": ["ରାସନ କାର୍ଡ", "NFSA", "SFSA", "ଓଡ଼ିଶା ବାସିନ୍ଦା"],
            "should_answer": True,
            "equiv_group": "bsky_eligibility"
        },
        {
            "id": "or_bsky_03",
            "language": "or",
            "question": "BSKY ସ୍ମାର୍ଟ କାର୍ଡ ପାଇଁ କେଉଁ ଦଲିଲ ଆବଶ୍ୟକ?",
            "expected_intent": "documents",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Required Documentation & Verification",
            "expected_answer_facts": ["ଆଧାର କାର୍ଡ", "ରାସନ କାର୍ଡ"],
            "should_answer": True,
            "equiv_group": "bsky_docs"
        },
        {
            "id": "or_bsky_04",
            "language": "or",
            "question": "କଣ ଘରୋଇ ଡାକ୍ତରଖାନାରେ BSKY ଅଧୀନରେ ମାଗଣା ଚିକିତ୍ସା ମିଳିବ?",
            "expected_intent": "procedure",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Scope of Healthcare Coverage",
            "expected_answer_facts": ["ତାଲିକାଭୁକ୍ତ ଘରୋଇ ହସ୍ପିଟାଲ", "କ୍ୟାସଲେସ"],
            "should_answer": True
        },
        {
            "id": "or_bsky_05",
            "language": "or",
            "question": "ସରକାରୀ ଡାକ୍ତରଖାନାରେ BSKY ର କଣ ସୁବିଧା ଅଛି?",
            "expected_intent": "benefits",
            "expected_document": "Biju Swasthya Kalyan Yojana Policy",
            "expected_section": "Scope of Healthcare Coverage",
            "expected_answer_facts": ["ସମ୍ପୂର୍ଣ୍ଣ ମାଗଣା", "ସମସ୍ତ ସରକାରୀ ହସ୍ପିଟାଲ"],
            "should_answer": True
        },
        {
            "id": "or_mbpy_01",
            "language": "or",
            "question": "ମଧୁ ବାବୁ ପେନସନ ଯୋଜନାରେ ମାସିକ କେତେ ଟଙ୍କା ପେନସନ ମିଳେ?",
            "expected_intent": "benefits",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Pension Rates & Financial Assistance",
            "expected_answer_facts": ["୫୦୦", "୭୦୦", "ପ୍ରତି ମାସ", "୬୦ ରୁ ୭୯ ବର୍ଷ", "୮୦ ବର୍ଷ"],
            "should_answer": True,
            "equiv_group": "mbpy_amount"
        },
        {
            "id": "or_mbpy_02",
            "language": "or",
            "question": "ମଧୁ ବାବୁ ପେନସନ ପାଇଁ ବୟସ ସୀମା କେତେ ହେବା ଆବଶ୍ୟକ?",
            "expected_intent": "eligibility",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["୬୦ ବର୍ଷ", "ନିଃସହାୟ"],
            "should_answer": True,
            "equiv_group": "mbpy_age"
        },
        {
            "id": "or_mbpy_03",
            "language": "or",
            "question": "MBPY ପେନସନ ପାଇଁ କେଉଁ କେଉଁ କାଗଜପତ୍ର ଆବଶ୍ୟକ?",
            "expected_intent": "documents",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Required Documents & Application",
            "expected_answer_facts": ["ବୟସ ପ୍ରମାଣପତ୍ର", "ଆୟ ପ୍ରମାଣପତ୍ର", "ଆଧାର କାର୍ଡ"],
            "should_answer": True,
            "equiv_group": "mbpy_docs"
        },
        {
            "id": "or_mbpy_04",
            "language": "or",
            "question": "ବିଧବା ଏବଂ ଭିନ୍ନକ୍ଷମ ବ୍ୟକ୍ତି ମଧୁ ବାବୁ ପେନସନ ପାଇପାରିବେ କି?",
            "expected_intent": "eligibility",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["ବିଧବା", "ଭିନ୍ନକ୍ଷମ", "ଯୋଗ୍ୟ"],
            "should_answer": True
        },
        {
            "id": "or_mbpy_05",
            "language": "or",
            "question": "ମଧୁ ବାବୁ ପେନସନ ପାଇଁ ପାରିବାରିକ ଆୟ ସୀମା କେତେ?",
            "expected_intent": "eligibility",
            "expected_document": "Madhu Babu Pension Yojana Guidelines",
            "expected_section": "Eligibility Criteria",
            "expected_answer_facts": ["୨୪,୦୦୦", "ବାର୍ଷିକ ଆୟ"],
            "should_answer": True
        },
        {
            "id": "or_sch_01",
            "language": "or",
            "question": "ଓଡ଼ିଶା ରାଜ୍ୟ ଛାତ୍ରବୃତ୍ତି ପୋର୍ଟାଲରେ କେଉଁ ସବୁ ସ୍କଲାରସିପ୍ ଉପଲବ୍ଧ ଅଛି?",
            "expected_intent": "benefits",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Scholarship Schemes & Financial Benefits",
            "expected_answer_facts": ["ପୋଷ୍ଟ ମାଟ୍ରିକ", "ପ୍ରି ମାଟ୍ରିକ", "ମେଧାବୃତ୍ତି"],
            "should_answer": True,
            "equiv_group": "sch_types"
        },
        {
            "id": "or_sch_02",
            "language": "or",
            "question": "ଓଡ଼ିଶା ପୋଷ୍ଟ-ମାଟ୍ରିକ ଛାତ୍ରବୃତ୍ତି ପାଇଁ ଯୋଗ୍ୟତା ସର୍ତ୍ତାବଳୀ କଣ?",
            "expected_intent": "eligibility",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Eligibility Requirements",
            "expected_answer_facts": ["SC/ST/OBC", "ଓଡ଼ିଶାର ବାସିନ୍ଦା", "ଆୟ ସୀମା"],
            "should_answer": True,
            "equiv_group": "sch_eligibility"
        },
        {
            "id": "or_sch_03",
            "language": "or",
            "question": "ଓଡ଼ିଶା ଛାତ୍ରବୃତ୍ତି ଆବେଦନ ପାଇଁ କେଉଁ ପ୍ରମାଣପତ୍ର ଆବଶ୍ୟକ?",
            "expected_intent": "documents",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Required Documents & Portal Verification",
            "expected_answer_facts": ["ଜାତିଗତ ପ୍ରମାଣପତ୍ର", "ଆୟ ପ୍ରମାଣପତ୍ର", "ଆଧାର", "ମାର୍କଶିଟ୍"],
            "should_answer": True,
            "equiv_group": "sch_docs"
        },
        {
            "id": "or_sch_04",
            "language": "or",
            "question": "ଛାତ୍ରବୃତ୍ତି ଟଙ୍କା ଛାତ୍ରଛାତ୍ରୀଙ୍କ ବ୍ୟାଙ୍କ ଖାତାକୁ କିପରି ପଠାଯାଏ?",
            "expected_intent": "procedure",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Disbursement & Direct Benefit Transfer",
            "expected_answer_facts": ["DBT", "ପ୍ରତ୍ୟକ୍ଷ ସୁବିଧା ହସ୍ତାନ୍ତର", "ଆଧାର ସଂଯୁକ୍ତ ବ୍ୟାଙ୍କ"],
            "should_answer": True
        },
        {
            "id": "or_sch_05",
            "language": "or",
            "question": "ଓଡ଼ିଶା ସ୍କଲାରସିପ୍ ର ଅଫିସିଆଲ ୱେବସାଇଟ୍ କଣ?",
            "expected_intent": "procedure",
            "expected_document": "Odisha State Scholarship Scheme",
            "expected_section": "Application Process",
            "expected_answer_facts": ["scholarship.odisha.gov.in", "ପୋର୍ଟାଲ"],
            "should_answer": True
        },
        {
            "id": "or_ood_01",
            "language": "or",
            "question": "ମଙ୍ଗଳ ଗ୍ରହରେ କେତେ ଲୋକ ବାସ କରନ୍ତି?",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        },
        {
            "id": "or_ood_02",
            "language": "or",
            "question": "ମୋତେ ଗୋଟିଏ ଓଡ଼ିଆ କୌତୁକ କୁହନ୍ତୁ।",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        },
        {
            "id": "or_ood_03",
            "language": "or",
            "question": "ଜାପାନର ରାଜଧାନୀର ନାମ କଣ?",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        },
        {
            "id": "or_ood_04",
            "language": "or",
            "question": "ପାଇଥନ ପ୍ରୋଗ୍ରାମିଂ କିପରି ଶିଖିବେ?",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        },
        {
            "id": "or_ood_05",
            "language": "or",
            "question": "ଗତକାଲି ଫୁଟବଲ ମ୍ୟାଚ୍ କିଏ ଜିତିଲା?",
            "expected_intent": "unsupported",
            "expected_document": "None",
            "expected_section": "None",
            "expected_answer_facts": [],
            "should_answer": False
        }
    ]

    os.makedirs("evaluation", exist_ok=True)
    with open("evaluation/dataset.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Created evaluation dataset with {len(data)} test questions (English: 25, Hindi: 25, Hinglish: 25, Odia: 25).")

if __name__ == "__main__":
    create_dataset()
