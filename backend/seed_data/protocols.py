from sqlalchemy.orm import Session

from backend.models import Intervention

TIER_1_PROTOCOLS = [
    {
        "name": "Sleep: 7-9 hours, consistent timing",
        "tier": 1,
        "evidence_grade": "A",
        "cost_tier": 1,
        "mechanism": "Sleep is the single most impactful longevity behaviour. During deep sleep, the glymphatic system clears amyloid-beta and tau. Consistent circadian timing reduces cortisol dysregulation and improves insulin sensitivity.",
        "references": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4517023/\nhttps://examine.com/topics/sleep/",
    },
    {
        "name": "Sleep: Dark, cool room + no screens 1hr before bed",
        "tier": 1,
        "evidence_grade": "A",
        "cost_tier": 1,
        "mechanism": "Blue light suppresses melatonin secretion. Room temperature 18-19°C optimises sleep architecture. Blackout curtains or eye mask improve deep sleep percentage.",
        "references": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6751071/",
    },
    {
        "name": "Exercise: Zone 2 cardio 150+ min/week",
        "tier": 1,
        "evidence_grade": "A",
        "cost_tier": 1,
        "mechanism": "Zone 2 (conversational pace, ~60-70% max HR) drives mitochondrial biogenesis, improves metabolic flexibility, raises VO2 max — the strongest predictor of all-cause mortality. 150 min/week is the minimum effective dose.",
        "references": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7296389/\nhttps://peterattiamd.com/category/exercise/",
    },
    {
        "name": "Exercise: Strength training 2x/week",
        "tier": 1,
        "evidence_grade": "A",
        "cost_tier": 1,
        "mechanism": "Muscle mass is a strong predictor of longevity independent of cardiovascular fitness. Resistance training improves insulin sensitivity, bone density, and maintains functional independence. Modify for arm physio — focus on legs and core.",
        "references": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5863730/",
    },
    {
        "name": "Diet: Protein 1.6g/kg bodyweight daily",
        "tier": 1,
        "evidence_grade": "A",
        "cost_tier": 1,
        "mechanism": "Adequate protein preserves muscle mass during aging (sarcopenia prevention). 1.6g/kg is the evidence-based minimum for muscle protein synthesis. Distribute across meals for best absorption.",
        "references": "https://examine.com/topics/protein-intake/",
    },
    {
        "name": "Diet: Mediterranean-adjacent whole foods",
        "tier": 1,
        "evidence_grade": "A",
        "cost_tier": 1,
        "mechanism": "Mediterranean diet has the strongest human evidence for reduced all-cause mortality, cardiovascular disease, and cognitive decline. Key features: olive oil, fish, vegetables, legumes, minimal ultra-processed food.",
        "references": "https://www.nejm.org/doi/full/10.1056/nejmoa1200303",
    },
    {
        "name": "Supplement: Omega-3 (cod liver oil / fish oil)",
        "tier": 1,
        "evidence_grade": "B",
        "cost_tier": 1,
        "mechanism": "EPA/DHA reduce systemic inflammation (lowered IL-6, TNF-alpha), improve endothelial function, and have modest cardiovascular benefits. Cod liver oil also provides Vitamin D and Vitamin A. Aim for 2g combined EPA+DHA daily.",
        "references": "https://examine.com/supplements/fish-oil/",
    },
    {
        "name": "Supplement: Magnesium glycinate 400mg before bed",
        "tier": 1,
        "evidence_grade": "B",
        "cost_tier": 1,
        "mechanism": "Magnesium is a cofactor in 300+ enzymatic reactions. ~60% of adults are deficient. Glycinate form is well-absorbed and calming. Improves sleep quality (particularly deep sleep), reduces cortisol, supports cardiovascular health.",
        "references": "https://examine.com/supplements/magnesium/",
    },
    {
        "name": "Supplement: Creatine monohydrate 5g daily",
        "tier": 1,
        "evidence_grade": "A",
        "cost_tier": 1,
        "mechanism": "Most researched sports supplement with strong safety profile. Supports muscle protein synthesis, ATP regeneration, and has emerging evidence for cognitive benefits and neuroprotection. One of the best evidence-to-cost ratios in longevity supplementation.",
        "references": "https://examine.com/supplements/creatine/",
    },
    {
        "name": "Supplement: Review existing multivitamin for gaps",
        "tier": 1,
        "evidence_grade": "B",
        "cost_tier": 1,
        "mechanism": "Most multivitamins are poorly dosed. Check for: Vitamin D3 (1000-4000 IU), K2 MK-7 (100-200mcg), Zinc, B12. Avoid excessive iron unless deficient. Once blood panels are available (Tier 2), optimise based on data.",
        "references": "https://examine.com/supplements/multivitamin/",
    },
]


def seed_tier1_protocols(db: Session) -> None:
    existing = db.query(Intervention).filter(Intervention.tier == 1).count()
    if existing > 0:
        return
    for protocol in TIER_1_PROTOCOLS:
        db.add(Intervention(**protocol))
    db.commit()
