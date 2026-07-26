export type AgentRunStatus =
    | 'pending'
    | 'running'
    | 'completed'
    | 'failed'

export type AgentRecommendation = 'human_review' | 'escalate'

export type AgentStepType =
    | 'classification'
    | 'severity_assessment'
    | 'knowledge_search'
    | 'customer_lookup'
    | 'order_lookup'
    | 'evidence_assessment'
    | 'response_draft'
    | 'escalation_decision'

export type AgentStepStatus =
    | 'pending'
    | 'running'
    | 'completed'
    | 'failed'

export interface AgentStepSummary {
    id: string
    sequence_number: number
    step_type: AgentStepType
    status: AgentStepStatus
    input_data: Record<string, unknown> | null
    output_data: Record<string, unknown> | null
    evidence: unknown[] | null
    confidence: number | null
    error_message: string | null
    started_at: string | null
    completed_at: string | null
    created_at: string
}

export interface AgentRunSummary {
    id: string
    ticket_id: string
    status: AgentRunStatus
    recommendation: AgentRecommendation | null
    confidence: number | null
    drafted_response: string | null
    error_message: string | null
    started_at: string | null
    completed_at: string | null
    created_at: string
}

export interface AgentRunDetail extends AgentRunSummary {
    steps: AgentStepSummary[]
}