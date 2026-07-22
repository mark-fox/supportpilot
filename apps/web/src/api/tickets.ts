import type { TicketSummary } from '../types/ticket'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL

if (!apiBaseUrl) {
    throw new Error('VITE_API_BASE_URL is not configured')
}

async function parseResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`)
    }

    return response.json() as Promise<T>
}

export async function getTickets(): Promise<TicketSummary[]> {
    const response = await fetch(`${apiBaseUrl}/tickets`)

    return parseResponse<TicketSummary[]>(response)
}

export async function getTicket(ticketId: string): Promise<TicketSummary> {
    const response = await fetch(`${apiBaseUrl}/tickets/${ticketId}`)

    return parseResponse<TicketSummary>(response)
}