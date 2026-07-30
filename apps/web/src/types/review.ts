export type HumanReviewAction =
    | 'approve'
    | 'request_revision'
    | 'escalate'

export interface HumanReviewCreate {
    action: HumanReviewAction
    reviewer_note: string | null
    revised_response: string | null
}

export interface HumanReviewSummary {
    id: string
    agent_run_id: string
    action: HumanReviewAction
    reviewer_note: string | null
    revised_response: string | null
    created_at: string
}