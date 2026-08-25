"""
Lightweight local knowledge base used for the RAG-lite recommendation
engine (services/rag.py). Each entry is an ORIGINAL, paraphrased summary
of well-established public-health guidance from the named source area —
not scraped or quoted text — tagged so retrieval can match it to a user's
risk factors.

In production, replace/extend this with a real vector-indexed corpus
(e.g. embed WHO / Alzheimer's Association / NIA / PubMed documents with
sentence-transformers into a vector DB such as FAISS, Pinecone, or Mongo
Atlas Vector Search) and swap the keyword retriever below for a real
embedding-similarity search. The interface (services/rag.py:retrieve)
is written so that swap doesn't require touching the callers.
"""

KNOWLEDGE_BASE = [
    {
        "id": "kb_exercise_1",
        "source": "WHO",
        "tags": ["exercise", "physical_activity", "sedentary"],
        "text": (
            "Regular aerobic activity — roughly 150 minutes per week of "
            "moderate exercise such as brisk walking, cycling, or swimming "
            "— is associated with better brain blood flow and slower "
            "cognitive decline in longitudinal studies."
        ),
    },
    {
        "id": "kb_diet_1",
        "source": "Alzheimer's Association",
        "tags": ["diet", "nutrition"],
        "text": (
            "Mediterranean- and MIND-style eating patterns, rich in leafy "
            "greens, berries, nuts, olive oil, and fish, and low in "
            "processed foods and added sugar, are linked to reduced "
            "cognitive decline risk in population studies."
        ),
    },
    {
        "id": "kb_sleep_1",
        "source": "NIA",
        "tags": ["sleep"],
        "text": (
            "Consistent, adequate sleep (roughly 7-8 hours nightly) "
            "supports the brain's overnight clearance of metabolic "
            "byproducts. Chronic sleep deprivation and untreated sleep "
            "apnea are both associated with elevated dementia risk."
        ),
    },
    {
        "id": "kb_stress_1",
        "source": "NIA",
        "tags": ["stress"],
        "text": (
            "Chronic stress elevates cortisol, which over long periods can "
            "affect memory-related brain regions. Mindfulness practice, "
            "regular physical activity, and social support are commonly "
            "recommended stress-reduction strategies."
        ),
    },
    {
        "id": "kb_social_1",
        "source": "Alzheimer's Association",
        "tags": ["social_interaction", "isolation"],
        "text": (
            "Social engagement and maintaining close relationships are "
            "associated with better cognitive reserve. Social isolation is "
            "an independent, modifiable risk factor identified in major "
            "dementia risk-factor reviews."
        ),
    },
    {
        "id": "kb_cognitive_engagement_1",
        "source": "NIA",
        "tags": ["reading_habit", "mental_stimulation"],
        "text": (
            "Lifelong learning and mentally stimulating activity — reading, "
            "puzzles, learning a new skill or language — is associated with "
            "greater cognitive reserve, which may delay the clinical "
            "expression of underlying neurodegeneration."
        ),
    },
    {
        "id": "kb_smoking_1",
        "source": "WHO",
        "tags": ["smoking"],
        "text": (
            "Smoking is a well-established modifiable dementia risk factor "
            "through vascular and oxidative-stress mechanisms. Smoking "
            "cessation at any age is associated with measurable risk "
            "reduction over time."
        ),
    },
    {
        "id": "kb_alcohol_1",
        "source": "WHO",
        "tags": ["alcohol"],
        "text": (
            "Heavy or frequent alcohol use is associated with elevated "
            "dementia risk, while light-to-moderate patterns show mixed "
            "evidence. Reducing intake toward recommended limits is a "
            "reasonable precaution for brain health."
        ),
    },
    {
        "id": "kb_cardio_1",
        "source": "PubMed guidelines",
        "tags": ["hypertension", "cardiovascular_flag", "diabetes"],
        "text": (
            "Managing blood pressure, blood sugar, and cardiovascular "
            "health in midlife is one of the most consistently replicated "
            "modifiable protective factors against later-life cognitive "
            "decline, per large cardiovascular-cognitive cohort studies."
        ),
    },
    {
        "id": "kb_hearing_1",
        "source": "PubMed guidelines",
        "tags": ["hearing_loss"],
        "text": (
            "Untreated hearing loss is associated with increased dementia "
            "risk, potentially through reduced auditory stimulation and "
            "social withdrawal. Hearing aids, when indicated, are "
            "associated with better cognitive outcomes in recent trials."
        ),
    },
    {
        "id": "kb_memory_tips_1",
        "source": "Alzheimer's Association",
        "tags": ["memory_complaints", "word_finding_difficulty"],
        "text": (
            "Simple memory-support strategies — consistent routines, "
            "written reminders, breaking tasks into steps, and repetition "
            "during learning — can help manage day-to-day memory concerns "
            "regardless of underlying cause."
        ),
    },
    {
        "id": "kb_consult_1",
        "source": "NIA",
        "tags": ["general", "consultation"],
        "text": (
            "Persistent or worsening memory or thinking changes, "
            "especially when noticed by family or affecting daily "
            "functioning, warrant evaluation by a physician or neurologist "
            "who can order appropriate clinical testing."
        ),
    },
]