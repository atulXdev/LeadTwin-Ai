# Workflow: Score Leads

## Objective
Score each enriched lead 0–100 using the signal matrix from the PRD. Generate explainable AI insights for why each lead is valuable.

## Required Inputs
- `enriched_profile` (dict): Output from Enrich Company workflow
- `contacts` (dict): Extracted contacts (emails, phones, LinkedIn)

## Tools to Execute (in sequence)
1. `tools/scoring_engine.py` → `score_lead(enriched_profile, contacts)` — Calculate score + grade
2. `tools/ai_insights.py` → `generate_insights(enriched_profile, score_data, contacts)` — Generate insight text

## Scoring Matrix
| Signal                | Points |
|-----------------------|--------|
| Has email             | +20    |
| Hiring page exists    | +15    |
| SaaS keyword found    | +15    |
| Has pricing page      | +10    |
| Uses modern stack     | +10    |
| Blog updated recently | +10    |
| Has phone             | +5     |
| Has LinkedIn          | +5     |
| Has services page     | +5     |
| Has about page        | +5     |

## Grading Scale
- **Hot** (60–100): High-value lead, prioritize outreach
- **Warm** (35–59): Moderate signals, worth following up
- **Cold** (0–34): Low signals, monitor for future changes

## Expected Output
```json
{
  "score": 75,
  "grade": "Hot",
  "insights": "AcmeTech is actively hiring developers, indicating growth...",
  "breakdown": { ... }
}
```

## Edge Cases
- **Groq API failure**: Fall back to template-based insights automatically
- **All signals missing**: Score will be 0, grade Cold — still valid output

## Error Handling
- Groq API has automatic fallback to templates
- Never block pipeline on insight generation failure

## Lessons Learned
(Agent updates this section as issues are discovered)
