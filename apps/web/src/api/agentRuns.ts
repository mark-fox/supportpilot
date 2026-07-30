import type {
    AgentRunDetail,
    AgentRunSummary,
} from '../types/agentRun'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL

if (!apiBaseUrl) {
    throw new Error('VITE_API_BASE_URL is not configured')
}

async function parseResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        let detail = `Request failed with status ${response.status}`

        try {
            const body = (await response.json()) as {
                detail?: string
            }

            if (body.detail) {
                detail = body.detail
            }
        } catch {
            // Keep the status-based message when the response is not JSON.
        }

        throw new Error(detail)
    }

    return response.json() as Promise<T>
}

export async function createAgentRun(
    ticketId: string,
): Promise<AgentRunSummary> {
    const response = await fetch(
        `${apiBaseUrl}/tickets/${ticketId}/agent-runs`,
        {
            method: 'POST',
        },
    )

    return parseResponse<AgentRunSummary>(response)
}

export async function executeAgentRun(
    agentRunId: string,
): Promise<AgentRunDetail> {
    const response = await fetch(
        `${apiBaseUrl}/agent-runs/${agentRunId}/execute`,
        {
            method: 'POST',
        },
    )

    return parseResponse<AgentRunDetail>(response)
}

export async function getAgentRun(
    agentRunId: string,
): Promise<AgentRunDetail> {
    const response = await fetch(
        `${apiBaseUrl}/agent-runs/${agentRunId}`,
    )

    return parseResponse<AgentRunDetail>(response)
}

export async function getTicketAgentRuns(
    ticketId: string,
): Promise<AgentRunSummary[]> {
    const response = await fetch(
        `${apiBaseUrl}/tickets/${ticketId}/agent-runs`,
    )

    return parseResponse<AgentRunSummary[]>(response)
}