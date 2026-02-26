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

  const text = await response.text()

  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const data = text ? JSON.parse(text) : {}
      message =
        typeof data.detail === "string"
          ? data.detail
          : data.error ?? data.message ?? message
    } catch {
      if (text && text.length < 200) message = text
    }
    throw new Error(message)
  }

  try {
    return JSON.parse(text) as ResearchResponse
  } catch {
    throw new Error("Invalid response from research API")
  }
}
