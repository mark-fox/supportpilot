export type TicketStatus =
    | 'open'
    | 'in_review'
    | 'resolved'
    | 'escalated'

export type TicketPriority = 'low' | 'normal' | 'high' | 'urgent'

export interface CustomerSummary {
    id: string
    email: string
    full_name: string
}

export interface TicketSummary {
    id: string
    subject: string
    description: string
    status: TicketStatus
    priority: TicketPriority
    created_at: string
    updated_at: string
    customer: CustomerSummary
}