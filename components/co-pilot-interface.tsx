"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Send, Lightbulb, Star, Loader2, Network } from "lucide-react"
import { startResearch } from "@/lib/llm-client"
import { createClient } from "@/lib/supabase/client"
import { validateCompanyName, validateRegionName, validateDivisionName, validateNumericChoice } from "@/lib/input-validator"

interface CoPilotInterfaceProps {
  stage: "initial" | "region" | "region-specific" | "division" | "division-specific" | "confirmation" | "results" | "feedback" | "feedback-clarification" | "processing" | "processing-feedback"
  onResponse: (stage: string, value: string, llmResult?: string) => void
  feedbackMode?: boolean
  onFeedbackComplete?: () => void
}

export default function CoPilotInterface({
  stage,
  onResponse,
  feedbackMode = false,
  onFeedbackComplete,
}: CoPilotInterfaceProps) {
  const [userInput, setUserInput] = useState("")
  const [validationError, setValidationError] = useState("")
  const [conversationHistory, setConversationHistory] = useState([
    {
      role: "assistant",
      content: feedbackMode
        ? "I see you'd like to make some changes to the research results. What specific adjustments would you like me to make to better match what you're looking for?"
        : "Hey there, which company would you like to research today?",
      timestamp: new Date(),
    },
  ])
  const [companyName, setCompanyName] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingSteps, setProcessingSteps] = useState<string[]>([])
  const [currentStage, setCurrentStage] = useState<CoPilotInterfaceProps['stage']>(feedbackMode ? "feedback" : stage)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [showConversationHistory, setShowConversationHistory] = useState(false)
  const [llmResult, setLlmResult] = useState<string | null>(null);
  const [structuredData, setStructuredData] = useState<any>(null);
  const conversationEndRef = useRef<HTMLDivElement>(null)

  // Add these state variables at the top with your other state declarations
  const [researchFocus, setResearchFocus] = useState<"comprehensive" | "specific" | "products">("comprehensive")
  const [specificDivision, setSpecificDivision] = useState("")
  const [regionFocus, setRegionFocus] = useState<"global" | "specific">("global")
  const [specificRegion, setSpecificRegion] = useState("")
  
  // Research scope state for tracking user choices and sidebar communication
  const [researchScope, setResearchScope] = useState<{
    companyName: string
    regionFocus: string
    specificRegion: string
    researchFocus: string
    specificDivision: string
    step: number
    totalSteps: number
  } | null>(null)

  // Broadcast research scope updates to sidebar
  const broadcastScopeUpdate = (updates: Partial<NonNullable<typeof researchScope>>) => {
    if (!updates) return
    
    setResearchScope((prev) => {
      const newScope = {
        companyName: "",
        regionFocus: "",
        specificRegion: "",
        researchFocus: "",
        specificDivision: "",
        step: 1,
        totalSteps: 4,
      ...prev,
      ...updates,
    }
    
    window.dispatchEvent(new CustomEvent('research-scope-update', { 
      detail: { scope: newScope } 
    }))
      
      return newScope
    })
  }
  
  // Reset conversation when stage changes to initial
  useEffect(() => {
    if (stage === "initial" && !feedbackMode) {
      setConversationHistory([
        {
          role: "assistant",
          content: "Hey there, which company would you like to research today?",
          timestamp: new Date(),
        },
      ])
      setUserInput("")
      setCompanyName("")
      setResearchFocus("comprehensive")
      setSpecificDivision("")
      setRegionFocus("global")
      setSpecificRegion("")
      broadcastScopeUpdate({ companyName: "", step: 1 })
      setIsProcessing(false)
      setProcessingSteps([])
      setCurrentStage("initial")
      setIsCollapsed(false)
      setShowConversationHistory(false)
    }
  }, [stage, feedbackMode])

  // Simulate LLM working in the background
  useEffect(() => {
    if (isProcessing) {
      const steps =
        currentStage === "processing-feedback"
          ? [
              "Processing your feedback... ",
              "Updating research parameters...",
              "Re-analyzing company data with new criteria...",
              "Refining search results...",
              "Generating updated report...",
            ]
          : [
              "Searching for company information...",
              `Finding recent news about ${companyName}...`,
              "Analyzing market position...",
              "Gathering financial data...",
              "Identifying key partnerships...",
              "Compiling sponsorship history...",
              "Analyzing target audience...",
              "Generating comprehensive report...",
            ]

      let currentStep = 0
      const interval = setInterval(() => {
        if (currentStep < steps.length) {
          setProcessingSteps(steps.slice(0, currentStep + 1));
          currentStep++;
        } else {
          clearInterval(interval);
          // <<== PLACE THE LLM CALL HERE
          let combinedResult: any = null;
          const runLLM = async () => {
            try {
              const supabase = createClient();
              const { data: { session } } = await supabase.auth.getSession();
              if (!session?.access_token) {
                throw new Error("Please sign in to run research.");
              }

              const result = await startResearch(
                {
                  companyName,
                  regionFocus,
                  specificRegion,
                  divisionFocus: researchFocus,
                  specificDivision,
                },
                session.access_token
              );

              // Map API response (snake_case) to shape expected by rest of app (camelCase)
              combinedResult = {
                structuredData: result.structured_data,
                detailedAnalysis: result.detailed_analysis,
                metadata: {
                  ...result.metadata,
                  companyName,
                  regionFocus,
                  specificRegion,
                  researchFocus,
                  specificDivision,
                  timestamp: new Date().toISOString(),
                },
              };

              setLlmResult(JSON.stringify(combinedResult, null, 2));
              setStructuredData(combinedResult);
            } catch (e) {
              console.error('Research failed:', e);
              const errorMessage = (e as Error).message;
              setLlmResult("Error: " + errorMessage);
              
              // Pass error details to parent for better error messages
              const errorDetails = JSON.stringify({
                error: true,
                message: errorMessage
              });
              
              if (currentStage === "processing-feedback") {
                onFeedbackComplete?.();
              } else {
                onResponse("results", companyName, errorDetails);
              }
              setIsProcessing(false);
              return;
            } finally {
              setIsProcessing(false);
              if (currentStage === "processing-feedback") {
                onFeedbackComplete?.();
              } else {
                // FIX: Check if combinedResult exists before using it
                if (combinedResult) {
                onResponse("results", companyName, JSON.stringify(combinedResult));
                }
              }
            }
          };
  
          setTimeout(runLLM, 1500); // Small delay after steps complete
        }
      }, 1000)

      return () => clearInterval(interval)
    }
  }, [isProcessing, companyName, onResponse, currentStage, onFeedbackComplete, researchFocus, specificDivision, regionFocus, specificRegion])

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    const scrollToBottom = () => {
      if (conversationEndRef.current) {
        conversationEndRef.current.scrollIntoView({
          behavior: "smooth",
          block: "end",
        })
      }
    }

    // Small delay to ensure DOM has updated
    const timeoutId = setTimeout(scrollToBottom, 100)

    return () => clearTimeout(timeoutId)
  }, [conversationHistory])

  // Get button options based on current stage
  const getOptionsForStage = (stage: string): Array<{ value: string; label: string; description: string }> => {
    if (stage === "region") {
      return [
        { value: '1', label: 'Global overview', description: 'Worldwide operations' },
        { value: '2', label: 'Specific region', description: 'Focus on one market' }
      ]
    }
    
    if (stage === "division") {
      return [
        { value: '1', label: 'Comprehensive overview', description: 'All business areas' },
        { value: '2', label: 'Specific division', description: 'Focus on one unit' }
      ]
    }
    
    return []
  }

  // Handle quick selection from button cards
  const handleQuickSelect = (value: string) => {
    if (!value) return
    
    setUserInput(value)
    // Trigger form submission after a brief moment
    setTimeout(() => {
      const form = document.querySelector('form')
      form?.requestSubmit()
    }, 50)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!userInput.trim()) return

    // Validate input based on current stage
    const trimmedInput = userInput.trim();
    let validationResult;
    let validatedInput = trimmedInput;

    if (currentStage === "initial") {
      validationResult = validateCompanyName(trimmedInput);
      validatedInput = validationResult.sanitized;
    } else if (currentStage === "region-specific") {
      validationResult = validateRegionName(trimmedInput);
      validatedInput = validationResult.sanitized;
    } else if (currentStage === "division-specific") {
      validationResult = validateDivisionName(trimmedInput);
      validatedInput = validationResult.sanitized;
    } else if (currentStage === "region" || currentStage === "division") {
      validationResult = validateNumericChoice(trimmedInput, ["1", "2"]);
      validatedInput = validationResult.sanitized;
    } else {
      // For other stages, just use trimmed input
      validationResult = { isValid: true, sanitized: trimmedInput, issues: [], blocked: false };
      validatedInput = trimmedInput;
    }

    // If input was completely blocked (only malicious content), show error message and reject
    if (validationResult.blocked || (!validationResult.isValid && validatedInput === "")) {
      setValidationError("Invalid input detected");
      setTimeout(() => setValidationError(""), 3000);
      return; // Silent rejection - input field just doesn't respond
    }

    // Add user message to conversation (use original input for display, validated for processing)
    const newUserMessage = {
      role: "user",
      content: validatedInput, // Use validated/sanitized input for display
      timestamp: new Date(),
    }

    let assistantResponse = ""
    let nextStage = ""

    if (currentStage === "initial") {
      setCompanyName(validatedInput) // Use validated input for state
      broadcastScopeUpdate({ companyName: validatedInput, step: 2 })
      assistantResponse = `Great! How would you like me to focus the research on ${validatedInput}?

Please choose one of the options below:`
      nextStage = "region"
      setCurrentStage("region")
    } else if (currentStage === "region") {
      const userResponse = validatedInput; // Use validated input
      
      if (userResponse === "1") {
        setRegionFocus("global");
        setSpecificRegion("global");
        broadcastScopeUpdate({ regionFocus: "Global", specificRegion: "Global", step: 3 })
        assistantResponse = `Perfect! Now how would you like me to focus the research on ${companyName}?

Please choose one of the options below:`
        nextStage = "division"
        setCurrentStage("division")
      } else if (userResponse === "2") {
        setRegionFocus("specific");
        broadcastScopeUpdate({ regionFocus: "Specific Region", step: 2.5 })
        assistantResponse = `Great! Which specific region or market would you like me to focus on? For example: North America, Europe, Asia Pacific, Latin America, or a specific country.`
        nextStage = "region-specific"
        setCurrentStage("region-specific")
      } else {
        // Invalid input - ask them to choose from buttons
        assistantResponse = `Please choose one of the options below to continue.`
        nextStage = "region"
        setCurrentStage("region")
      }
    } else if (currentStage === "region-specific") {
      setSpecificRegion(validatedInput);
      broadcastScopeUpdate({ specificRegion: validatedInput, step: 3 })
      assistantResponse = `Perfect! Now how would you like me to focus the research on ${companyName} in ${validatedInput}?

Please choose one of the options below.`
      nextStage = "division"
      setCurrentStage("division")
    } else if (currentStage === "division") {
      const userResponse = validatedInput; // Use validated input
      
      if (userResponse === "1") {
        setResearchFocus("comprehensive");
        broadcastScopeUpdate({ researchFocus: "Comprehensive", step: 4 })
        // Don't set specificDivision for comprehensive overview
        assistantResponse = `Perfect! I'll provide a research report for ${companyName}${regionFocus === "specific" ? ` in ${specificRegion}` : " globally"}. Sound good?`
        nextStage = "confirmation"
        setCurrentStage("confirmation")
      } else if (userResponse === "2") {
        setResearchFocus("specific");
        broadcastScopeUpdate({ researchFocus: "Specific Division", step: 3.5 })
        assistantResponse = `Great! Which specific division or business unit would you like me to focus on?`
        nextStage = "division-specific"
        setCurrentStage("division-specific")
      } else {
        // Invalid input - ask them to choose from buttons
        assistantResponse = `Please choose one of the options below to continue.`
        nextStage = "division"
        setCurrentStage("division")
      }
    } else if (currentStage === "division-specific") {
      setSpecificDivision(validatedInput);
      broadcastScopeUpdate({ specificDivision: validatedInput, step: 4 })
      assistantResponse = `Perfect! I'll provide a research report for ${companyName}${regionFocus === "specific" ? ` in ${specificRegion}` : " globally"}, focusing on their ${validatedInput} division. Sound good?`
      nextStage = "confirmation"
      setCurrentStage("confirmation")
    } else if (currentStage === "confirmation") {
      // Handle user's affirmative response
      assistantResponse = "Great! Let me gather all the relevant information for you. This might take a moment..."
      setIsProcessing(true)
      nextStage = "processing"
      setCurrentStage("processing")
    } else if (currentStage === "feedback") {
      // Analyze feedback and potentially ask clarifying questions
      const feedback = validatedInput.toLowerCase()

      if (feedback.includes("industry") || feedback.includes("sector")) {
        assistantResponse =
          "Got it! Which industry would you prefer me to focus on? For example: healthcare, technology, renewable energy, financial services, etc."
        nextStage = "feedback-clarification"
        setCurrentStage("feedback-clarification")
      } else if (feedback.includes("size") || feedback.includes("employee") || feedback.includes("revenue")) {
        assistantResponse =
          "Understood! What company size are you looking for? For example: 'startups under 100 employees', 'mid-size companies 500-5000 employees', or 'large enterprises 10,000+ employees'?"
        nextStage = "feedback-clarification"
        setCurrentStage("feedback-clarification")
      } else if (feedback.includes("region") || feedback.includes("location") || feedback.includes("geographic")) {
        assistantResponse =
          "I see! Which geographic region should I focus on? For example: North America, Europe, Asia Pacific, or a specific country?"
        nextStage = "feedback-clarification"
        setCurrentStage("feedback-clarification")
      } else if (feedback.includes("different company") || feedback.includes("another company")) {
        assistantResponse = "No problem! What company would you like me to research instead?"
        nextStage = "feedback-clarification"
        setCurrentStage("feedback-clarification")
      } else {
        // Generic feedback - ask for more specifics with context from user input
        const contextualSuggestions = []

        if (feedback.includes("more") || feedback.includes("add") || feedback.includes("include")) {
          contextualSuggestions.push("add more detailed information about specific aspects")
        }
        if (feedback.includes("less") || feedback.includes("remove") || feedback.includes("exclude")) {
          contextualSuggestions.push("focus on fewer areas with deeper analysis")
        }
        if (feedback.includes("recent") || feedback.includes("latest") || feedback.includes("current")) {
          contextualSuggestions.push("emphasize more recent developments and news")
        }
        if (feedback.includes("financial") || feedback.includes("revenue") || feedback.includes("profit")) {
          contextualSuggestions.push("expand the financial analysis section")
        }
        if (feedback.includes("competitor") || feedback.includes("competition") || feedback.includes("market")) {
          contextualSuggestions.push("include more competitive landscape analysis")
        }
        if (feedback.includes("partnership") || feedback.includes("collaboration") || feedback.includes("alliance")) {
          contextualSuggestions.push("detail their strategic partnerships and collaborations")
        }

        const baseMessage = `Thanks for the feedback! Based on your input "${validatedInput}", I can help you refine the research.`

        if (contextualSuggestions.length > 0) {
          assistantResponse = `${baseMessage} Would you like me to ${contextualSuggestions.join(", or ")}? Please let me know which specific aspects you'd like me to adjust.`
        } else {
          assistantResponse = `${baseMessage} Could you be more specific about what you'd like me to adjust? For example, would you like me to focus more on their recent developments, expand on their financial performance, include more partnership details, or analyze their competitive position?`
        }

        nextStage = "feedback-clarification"
        setCurrentStage("feedback-clarification")
      }
    } else if (currentStage === "feedback-clarification") {
      assistantResponse = "Perfect! Let me update the research with your requirements. This will take a moment..."
      setIsProcessing(true)
      nextStage = "processing-feedback"
      setCurrentStage("processing-feedback")
    }

    const newAssistantMessage = {
      role: "assistant",
      content: assistantResponse,
      timestamp: new Date(),
    }

    setConversationHistory((prev) => [...prev, newUserMessage, newAssistantMessage])

    if (currentStage !== "confirmation" && currentStage !== "processing") {
      onResponse(nextStage, validatedInput)
    }

    setUserInput("")
  }

  return (
    <>
      {/* Header - moved outside and repositioned */}
      <div className="mb-6 ml-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Network className="h-5 w-5 text-gray-600" />
            <h1 className="text-base font-bold uppercase tracking-wide">AI Research Co-Pilot</h1>
          </div>
          {feedbackMode && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="text-gray-600 hover:text-gray-800"
            >
              {isCollapsed ? "Expand" : "Minimize"}
            </Button>
          )}
        </div>
        {!feedbackMode && (
          <p className="text-body text-gray-600">
            Search the web and research your company using our AI-powered co-pilot
          </p>
        )}
      </div>

      <div
        className={`flex flex-col ${feedbackMode && isCollapsed ? "h-auto" : "h-full"} p-6 ${feedbackMode ? "border-2 border-orange-200 rounded-lg bg-orange-50/10" : ""}`}
      >
        {/* Feedback Mode Indicator */}
        {feedbackMode && !isCollapsed && (
          <div className="mb-6 p-4 bg-orange-50 border-l-4 border-orange-400 rounded-r-lg">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-2 h-2 bg-orange-400 rounded-full animate-pulse"></div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-orange-800 uppercase tracking-wide">Feedback Mode Active</p>
                <p className="text-xs text-orange-600">Provide feedback to refine the research results</p>
              </div>
            </div>
          </div>
        )}

        {/* Rest of the content remains the same */}
        {isProcessing ? (
          <div className="flex-1 flex flex-col items-center justify-center">
            <div className="text-center space-y-24 max-w-2xl">
              <div className="flex items-center justify-center">
                <Loader2 className="h-12 w-12 animate-spin text-black" />
              </div>
              <h2 className="text-xl font-bold uppercase tracking-wide">Generating Brand Research</h2>
              <div className="space-y-4 text-left">
                {processingSteps
                  .filter((step) => step && step.trim())
                  .map((step, index) => (
                    <div key={index} className="flex items-center gap-4">
                      <div className="w-4 h-4 rounded-full bg-black"></div>
                      <p className="text-body text-gray-800">{step}</p>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Conversation Thread - only show when not collapsed or not in feedback mode */}
            <div className="flex-1 space-y-4 mb-6 overflow-y-auto max-h-[400px] scroll-smooth">
              {/* Show conversation history toggle button in feedback mode */}
              {feedbackMode && conversationHistory.length > 1 && (
                <div className="flex justify-center pb-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowConversationHistory(!showConversationHistory)}
                    className="text-xs text-gray-500 hover:text-gray-700"
                  >
                    {showConversationHistory
                      ? "Show less"
                      : `View conversation history (${conversationHistory.length - 1} earlier messages)`}
                  </Button>
                </div>
              )}

              {/* Display messages based on feedback mode and history toggle */}
              {(feedbackMode && !showConversationHistory ? conversationHistory.slice(-1) : conversationHistory).map(
                (message, index, displayedMessages) => (
                  <div
                    key={feedbackMode && !showConversationHistory ? `recent-${index}` : index}
                    className={`flex items-start gap-4 ${message.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    {message.role === "assistant" && (
                      <div className="flex-shrink-0 w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center bg-white">
                        <Lightbulb className="h-4 w-4 text-gray-600" />
                      </div>
                    )}

                    <div className={`max-w-[80%] ${message.role === "user" ? "text-right" : "text-left"}`}>
                      <p className="text-body text-gray-800 leading-relaxed">{message.content}</p>
                      
                      {/* Add clickable button options for numbered choices */}
                      {message.role === "assistant" && 
                       index === displayedMessages.length - 1 && 
                       getOptionsForStage(currentStage).length > 0 && (
                        <div className="mt-4 flex gap-3">
                          {getOptionsForStage(currentStage).map((option) => (
                            <button
                              key={option.value}
                              onClick={() => handleQuickSelect(option.value)}
                              onKeyDown={(e) => e.key === 'Enter' && handleQuickSelect(option.value)}
                              aria-label={`Select ${option.label}`}
                              tabIndex={0}
                              role="button"
                              className="flex-1 text-left bg-white border-2 border-gray-200 hover:border-black hover:bg-gray-50 hover:shadow-sm cursor-pointer rounded-lg p-4 transition-all duration-200 group"
                            >
                              <div className="font-semibold text-sm group-hover:text-black">{option.label}</div>
                              <div className="text-xs text-gray-600 mt-1">{option.description}</div>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>

                    {message.role === "user" && (
                      <div className="flex-shrink-0 w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center bg-white">
                        <Star className="h-4 w-4 text-gray-600" />
                      </div>
                    )}
                  </div>
                ),
              )}

              {/* Invisible element to scroll to */}
              <div ref={conversationEndRef} className="h-1" />
            </div>

            {/* Show current message when collapsed in feedback mode */}
            {feedbackMode && isCollapsed && (
              <div className="mb-6">
                <div className="flex items-start gap-4 justify-start">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center bg-white">
                    <Lightbulb className="h-4 w-4 text-gray-600" />
                  </div>
                  <div className="max-w-[80%] text-left">
                    <p className="text-body text-gray-800 leading-relaxed">
                      {conversationHistory[conversationHistory.length - 1]?.content}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Input Area - always visible */}
            <div className="pt-6">
              <form onSubmit={handleSubmit} className="flex gap-4">
                {(() => {
                  const hasButtonOptions = currentStage === "region" || currentStage === "division"
                  return (
                    <textarea
                      disabled={hasButtonOptions}
                      placeholder={
                        hasButtonOptions
                          ? "Please select an option above"
                          : currentStage === "feedback" || currentStage === "feedback-clarification"
                          ? "Try: 'Focus more on their recent partnerships' or 'Include more financial data' or 'Add information about their sustainability initiatives' or 'Expand on their target audience demographics'"
                          : "Type your response..."
                      }
                      value={userInput}
                      onChange={(e) => setUserInput(e.target.value)}
                      maxLength={200}
                      className={`flex-1 bg-white border-gray-200 rounded-md px-3 py-2 h-20 resize-none border text-sm focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent ${hasButtonOptions ? 'opacity-50 cursor-not-allowed' : ''}`}
                      onKeyDown={(e) => {
                        if (hasButtonOptions) {
                          e.preventDefault()
                          return
                        }
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault()
                          handleSubmit(e)
                        }
                      }}
                    />
                  )
                })()}
                <Button type="submit" size="icon" className="bg-black text-white hover:bg-gray-800">
                  <Send className="h-4 w-4" />
                  <span className="sr-only">Send</span>
                </Button>
              </form>
              {validationError && (
                <div className="text-red-600 text-sm mt-2 px-3 py-2 bg-red-50 border border-red-200 rounded-md">
                  {validationError}
                </div>
              )}
            </div>

            {/* Progress Stepper - only show after company name entered */}
            {!feedbackMode && currentStage !== 'initial' && companyName && (
              <div className="mt-6 px-4 py-3 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center justify-between text-xs font-medium uppercase tracking-wide">
                  <span className="text-gray-400">
                    1. Company
                  </span>
                  <div className="h-px flex-1 mx-2 bg-gray-300" />
                  <span className={['region', 'region-specific'].includes(currentStage) ? 'text-black' : 'text-gray-400'}>
                    2. Region
                  </span>
                  <div className="h-px flex-1 mx-2 bg-gray-300" />
                  <span className={['division', 'division-specific'].includes(currentStage) ? 'text-black' : 'text-gray-400'}>
                    3. Scope
                  </span>
                  <div className="h-px flex-1 mx-2 bg-gray-300" />
                  <span className={currentStage === 'confirmation' ? 'text-black' : 'text-gray-400'}>
                    4. Confirm
                  </span>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </>
  )
}
