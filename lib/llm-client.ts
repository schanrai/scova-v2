/**
 * Single entry point for company research. POSTs to Python backend /api/research.
 * Replaces the previous 5 LLM client functions and formatting agent (Task 3).
 */

// ---- Request params (map to Python ResearchRequest) ----
export interface ResearchRequestParams {
  companyName: string
  regionFocus: string
  specificRegion?: string
  divisionFocus?: string
  specificDivision?: string
}

// ---- Response types (mirror Python Pydantic ResearchResponse) ----
export interface StructuredData {
  industry: string
  founded: string
  website: string
  headquarters: string
  annualRevenue: string
  employees: string
}

export interface SectionWithSources {
  content: string
  sources: string[]
}

export interface SectionContent {
  content: string
}

export interface SocialMediaSection {
  handles: string
  content: string
}

export interface DetailedAnalysis {
  companyOverview: SectionWithSources
  companyBackground: SectionWithSources
  financialOverview: SectionWithSources
  audienceSegmentation: SectionWithSources
  marketingActivity: SectionContent
  sponsorshipsExperiential: SectionContent
  socialMediaPresence: SocialMediaSection
  strategicFocus: SectionContent
}

export interface ResearchResponse {
  structured_data: StructuredData
  detailed_analysis: DetailedAnalysis
  metadata: Record<string, unknown>
}

/**
 * Run full research flow via Python backend (6 LLM calls, Pydantic validation).
 * Requires a valid Supabase JWT for /api/research.
 */
export async function startResearch(
  params: ResearchRequestParams,
  accessToken: string
): Promise<ResearchResponse> {
  const body = {
    company_name: params.companyName,
    region_focus: params.regionFocus,
    specific_region: params.specificRegion ?? "",
    division_focus: params.divisionFocus ?? "",
    specific_division: params.specificDivision ?? "",
  }

  const response = await fetch("/api/research", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(body),
  })

  const data = await response.json()

  if (!response.ok) {
    const message =
      typeof data.detail === "string"
        ? data.detail
        : data.error ?? data.message ?? `HTTP ${response.status}`
    throw new Error(message)
  }

  return data as ResearchResponse
}
