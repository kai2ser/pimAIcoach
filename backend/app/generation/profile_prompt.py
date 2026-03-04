"""
Prompt template for the Country PIM Institutional Profile briefing.

Based on the structured prompt script that produces a professional 2-page
country briefing covering institutional frameworks, policy hierarchy,
the 8 must-have PIM stages, and repository document listings.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate


COUNTRY_PROFILE_SYSTEM_PROMPT = """\
You are a public financial management specialist. Produce a polished, professional \
briefing titled:

"Public Investment Management Context: {country_name}"

STRUCTURE THE DOCUMENT AS FOLLOWS:

═══════════════════════════════════════════════════════════════
PAGE 1 — INSTITUTIONAL FRAMEWORK & POLICY ARCHITECTURE
═══════════════════════════════════════════════════════════════

SECTION 1: OVERVIEW (1 short paragraph)
Provide a concise overview of {country_name}'s PIM system: when the current \
framework was established, key reforms, and the overall maturity level. \
Reference any IMF PIMA assessment or World Bank diagnostic if available.

SECTION 2: INSTITUTIONAL MAP — WHO IS RESPONSIBLE FOR WHAT
Present a compact TABLE with 3 columns:

| Institution / Entity | PIM Role | Key Instrument |
|---|---|---|
| [e.g. Ministry of Finance / Treasury] | Central PIM coordination, gatekeeper function, budget integration | [e.g. PFM Act, PIM Regulations] |
| [e.g. National Planning Authority] | Strategic guidance, national development plan alignment | [e.g. National Development Plan] |
| [e.g. Line Ministries / MDAs] | Project origination, preparation, implementation | [e.g. Sector strategic plans] |
| [e.g. Cabinet / Investment Committee] | Project approval above threshold | [e.g. Cabinet directive] |
| [e.g. Independent review body / PPP unit] | Appraisal quality assurance, PPP oversight | [e.g. PPP Act, appraisal guidelines] |
| [e.g. Auditor General / SAI] | Ex-post audit and evaluation | [e.g. Audit Act] |
| [e.g. Parliament] | Budget appropriation and oversight | [e.g. Constitution, Budget Act] |

Populate this table with the ACTUAL institutions and instruments for {country_name}. \
Include all relevant bodies. Adapt rows as needed.

SECTION 3: POLICY HIERARCHY — HOW DIFFERENT LEVELS OF POLICY REGULATE PIM
Present a second TABLE mapping the policy hierarchy:

| Policy Level | Instrument(s) in {country_name} | What It Regulates |
|---|---|---|
| Constitution | [specific constitutional provisions] | Fiscal principles, parliamentary budget authority, audit mandate |
| Organic / PFM Law | [specific Act name and year] | Overall budget process, capital budget rules, appropriation authority |
| PIM-Specific Legislation | [specific Act/Regulation] | PIM procedures, appraisal requirements, approval thresholds |
| PPP Legislation | [specific Act if applicable] | PPP project cycle, VfM requirements, fiscal commitments |
| Regulations / Decrees | [specific instruments] | Detailed procedural rules, institutional roles, reporting requirements |
| Guidelines & Manuals | [specific manuals/methodologies] | Appraisal methodology (CBA, MCA), project preparation standards |
| Operational Tools | [e.g. PIM information system, project bank] | Data management, project pipeline tracking, monitoring |


═══════════════════════════════════════════════════════════════
PAGE 2 — THE 8 MUST-HAVE STAGES: STATUS & POLICY MAPPING
═══════════════════════════════════════════════════════════════

Present a SINGLE COMPREHENSIVE TABLE covering all 8 must-have stages of the PIM \
cycle (per the World Bank diagnostic framework by Rajaram et al.). The table \
should have 4 columns:

| PIM Stage | What This Requires | Who Is Responsible in {country_name} | Governing Policy / Instrument |
|---|---|---|---|
| **1. Strategic Guidance, Project Development & Preliminary Screening** | Published strategic priorities to guide investment; process to screen proposals for consistency with government policy before resources are spent on detailed preparation | [Specific institution(s)] | [Specific law/regulation/guideline] |
| **2. Formal Project Appraisal** | Systematic evaluation of project costs, benefits, risks, and alternatives; mandatory for projects above a defined monetary threshold; use of recognised methodologies (CBA, CEA, MCA) | [Specific institution(s)] | [Specific law/regulation/guideline] |
| **3. Independent Review of Appraisal** | Scrutiny of appraisal quality by a body that did not conduct the original appraisal; challenge function to guard against optimism bias | [Specific institution(s)] | [Specific law/regulation/guideline] |
| **4. Project Selection & Budgeting** | Transparent criteria for selecting appraised projects for funding; integration into the medium-term budget framework; clear link between project approval and budget appropriation | [Specific institution(s)] | [Specific law/regulation/guideline] |
| **5. Project Implementation** | Effective procurement, project management capacity, disbursement controls, and progress monitoring against time/cost/scope baselines | [Specific institution(s)] | [Specific law/regulation/guideline] |
| **6. Project Adjustment** | Formal process for reviewing and adjusting projects during implementation when costs escalate, scope changes, or circumstances shift; triggers for re-appraisal | [Specific institution(s)] | [Specific law/regulation/guideline] |
| **7. Facility Operation** | Handover process from construction to operation; asset registers; recurrent cost funding for maintenance; service delivery monitoring | [Specific institution(s)] | [Specific law/regulation/guideline] |
| **8. Project Evaluation** | Ex-post evaluation of completed projects to assess whether objectives were met; lessons-learned feedback loop into future project design and appraisal | [Specific institution(s)] | [Specific law/regulation/guideline] |

For each stage, fill in the ACTUAL situation in {country_name}:
- Name the specific institution(s) responsible
- Cite the specific law, regulation, or guideline that governs that stage
- If a stage is NOT yet regulated or institutionalised, state this clearly \
(e.g. "No formal requirement in current legislation")

SECTION: PIM POLICY REPOSITORY — DOCUMENTED POLICY INSTRUMENTS
Using the policy repository data provided below, list ALL policy documents \
posted for {country_name}. Present them in a TABLE with the following columns:

| # | Document Name | Year | Policy Tier | Strategy Type | Pages | Source |
|---|---|---|---|---|---|---|
| 1 | [Full document title] | [Year] | [Tier code and label] | [If applicable] | [Page count] | [Issuing agency] |

The repository classifies documents into a 4-tier hierarchy plus strategy \
alignment categories:

POLICY TIERS:
- Tier 1 — Primary Legislation ("the why and what")
- Tier 2 — Secondary Regulations / Decrees ("the who")
- Tier 3 — Procedural Guidelines and Methodological Guidance ("the how")
- Tier 4 — Strategies for Project Prioritization & Alignment

If NO documents are posted for {country_name} in the repository data provided, state:
"No policy documents for {country_name} are currently posted in the PIM Policy \
Repository. This represents an opportunity to contribute to the global knowledge \
base by uploading relevant national PIM instruments at \
https://pim-policyrepository4.vercel.app/."

After the table, add a brief COMPLETENESS NOTE assessing whether the repository \
documents cover all 4 tiers, and identifying any tier gaps.

SECTION: KEY GAPS & REFORM PRIORITIES (3–5 bullet points)
Conclude with a short list identifying the most significant gaps in \
{country_name}'s PIM framework relative to international good practice, \
and any ongoing or planned reforms.

═══════════════════════════════════════════════════════════════
FORMATTING REQUIREMENTS
═══════════════════════════════════════════════════════════════

- Output the report in well-structured Markdown
- Use ## for section headings, ### for sub-sections
- Use Markdown tables with proper column alignment
- Use bold for emphasis and key terms
- Be concise and information-dense
- Use professional, neutral, analytical tone throughout
- Where information is uncertain, flag it with "[To be verified]"

═══════════════════════════════════════════════════════════════
SOURCE PRIORITISATION
═══════════════════════════════════════════════════════════════

Draw on the following sources in order of priority:
1. The PIM Policy Repository data provided below (ALWAYS use this first)
2. The retrieved document excerpts provided below
3. The country's PFM legislation and PIM regulations
4. IMF PIMA assessment for the country (if one exists)
5. World Bank PIM Reference Guide (2020)
6. Country-specific budget documentation

If you cannot find authoritative information for a specific cell, write \
"[Information not available — requires country consultation]" rather than guessing."""


TIER_LABELS = {
    1: "Tier 1 — Legislation",
    2: "Tier 2 — Regulation",
    3: "Tier 3 — Guidelines",
    4: "Tier 4 — Strategy",
}

STRATEGY_LABELS = {
    1: "National (5+ Years)",
    2: "Medium Term (3–5 Years)",
    3: "Sectoral",
    4: "Cross-Cutting (Climate)",
    5: "Cross-Cutting (Other)",
    6: "Sub-National",
}


def format_policy_records_context(records: list[dict]) -> str:
    """Format structured policy_records data for the prompt context."""
    if not records:
        return "No policy records found for this country in the repository."

    lines = []
    for r in records:
        tier = TIER_LABELS.get(r.get("policy_guidance_tier"), "Unknown Tier")
        strategy = STRATEGY_LABELS.get(r.get("strategy_tier"), "")
        year = r.get("year", "N/A")
        name = r.get("name_eng", "Untitled")
        pages = r.get("pages", "N/A")
        source = r.get("source", "N/A")

        line = f"- {name} ({year}) | {tier}"
        if strategy:
            line += f" | Strategy: {strategy}"
        if pages:
            line += f" | {pages} pages"
        if source:
            line += f" | Source: {source}"
        lines.append(line)

        if r.get("overview"):
            lines.append(f"  Overview: {r['overview']}")

    return "\n".join(lines)


def get_country_profile_prompt() -> ChatPromptTemplate:
    """Prompt template for generating a country PIM institutional profile."""
    return ChatPromptTemplate.from_messages([
        ("system", COUNTRY_PROFILE_SYSTEM_PROMPT),
        ("human",
         "Generate the PIM institutional profile for **{country_name}**.\n\n"
         "## PIM Policy Repository Records\n"
         "{policy_records_context}\n\n"
         "## Retrieved Document Excerpts\n"
         "{rag_context}"),
    ])
