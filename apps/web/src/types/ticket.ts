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

export interface TicketDetail extends TicketSummary {
    customer_orders: OrderSummary[]
}

export type OrderStatus =
    | 'processing'
    | 'shipped'
    | 'delivered'
    | 'cancelled'
    | 'refunded'

export interface OrderSummary {
    id: string
    order_number: string
    status: OrderStatus
    total_cents: number
    tracking_number: string | null
    created_at: string
}