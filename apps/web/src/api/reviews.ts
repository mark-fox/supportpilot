import type {
    HumanReviewCreate,
    HumanReviewSummary,
} from '../types/review'

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

export async function createHumanReview(
    agentRunId: string,
    review: HumanReviewCreate,
): Promise<HumanReviewSummary> {
    const response = await fetch(
        `${apiBaseUrl}/agent-runs/${agentRunId}/reviews`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(review),
        },
    )

    return parseResponse<HumanReviewSummary>(response)
}