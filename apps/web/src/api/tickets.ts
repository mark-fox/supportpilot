import type { TicketSummary } from '../types/ticket'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL

if (!apiBaseUrl) {
    throw new Error('VITE_API_BASE_URL is not configured')
}

export async function getTickets(): Promise<TicketSummary[]> {
    const response = await fetch(`${apiBaseUrl}/tickets`)

    if (!response.ok) {
        throw new Error(`Ticket request failed with status ${response.status}`)
    }

    return response.json() as Promise<TicketSummary[]>
}