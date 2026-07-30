import { useEffect, useState } from 'react'

import {
  createAgentRun,
  executeAgentRun,
  getAgentRun,
  getTicketAgentRuns,
} from './api/agentRuns'
import { createHumanReview } from './api/reviews'
import { getTicket, getTickets } from './api/tickets'
import type {
  AgentRunDetail,
  AgentStepSummary,
} from './types/agentRun'
import type {
  HumanReviewAction,
  HumanReviewSummary,
} from './types/review'
import type { TicketDetail, TicketSummary } from './types/ticket'

function formatDate(dateValue: string): string {
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(dateValue))
}

function formatCurrency(cents: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(cents / 100)
}

function formatLabel(value: string): string {
  return value
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function formatConfidence(confidence: number | null): string {
  if (confidence === null) {
    return 'Not available'
  }

  return `${Math.round(confidence * 100)}%`
}

function getStepSummary(step: AgentStepSummary): string {
  switch (step.step_type) {
    case 'classification':
      return String(step.output_data?.issue_type ?? 'Classification complete')
    case 'severity_assessment':
      return String(step.output_data?.severity ?? 'Severity assessed')
    case 'knowledge_search':
      return `${String(step.output_data?.result_count ?? 0)} article(s) found`
    case 'order_lookup':
      return `${String(step.output_data?.result_count ?? 0)} order(s) found`
    case 'evidence_assessment':
      return step.output_data?.is_sufficient
        ? 'Evidence sufficient'
        : 'Evidence insufficient'
    case 'response_draft':
      return step.output_data?.was_drafted
        ? 'Draft created'
        : 'Draft skipped'
    case 'escalation_decision':
      return formatLabel(
        String(step.output_data?.recommendation ?? 'Decision complete'),
      )
    default:
      return formatLabel(step.status)
  }
}

function App() {
  const [tickets, setTickets] = useState<TicketSummary[]>([])
  const [selectedTicket, setSelectedTicket] =
    useState<TicketDetail | null>(null)
  const [agentRun, setAgentRun] = useState<AgentRunDetail | null>(null)
  const [humanReview, setHumanReview] =
    useState<HumanReviewSummary | null>(null)

  const [reviewerNote, setReviewerNote] = useState('')

  const [isQueueLoading, setIsQueueLoading] = useState(true)
  const [isTicketLoading, setIsTicketLoading] = useState(false)
  const [isAgentRunning, setIsAgentRunning] = useState(false)
  const [isReviewSubmitting, setIsReviewSubmitting] = useState(false)

  const [queueError, setQueueError] = useState<string | null>(null)
  const [ticketError, setTicketError] = useState<string | null>(null)
  const [agentError, setAgentError] = useState<string | null>(null)
  const [reviewError, setReviewError] = useState<string | null>(null)

  useEffect(() => {
    async function loadTickets() {
      try {
        const loadedTickets = await getTickets()
        setTickets(loadedTickets)

        if (loadedTickets.length > 0) {
          const firstTicket = await getTicket(loadedTickets[0].id)
          setSelectedTicket(firstTicket)
          await loadLatestAgentRun(firstTicket.id)
        }
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : 'An unexpected error occurred'

        setQueueError(message)
      } finally {
        setIsQueueLoading(false)
      }
    }

    void loadTickets()
  }, [])

  async function refreshSelectedTicket(ticketId: string) {
    const refreshedTicket = await getTicket(ticketId)
    setSelectedTicket(refreshedTicket)

    setTickets((currentTickets) =>
      currentTickets.map((ticket) =>
        ticket.id === refreshedTicket.id
          ? {
            ...ticket,
            status: refreshedTicket.status,
            updated_at: refreshedTicket.updated_at,
          }
          : ticket,
      ),
    )
  }

  async function loadLatestAgentRun(ticketId: string) {
    const runs = await getTicketAgentRuns(ticketId)

    if (runs.length === 0) {
      setAgentRun(null)
      return
    }

    const latestRun = await getAgentRun(runs[0].id)
    setAgentRun(latestRun)
  }

  async function handleTicketSelect(ticketId: string) {
    if (selectedTicket?.id === ticketId) {
      return
    }

    setIsTicketLoading(true)
    setTicketError(null)
    setAgentRun(null)
    setAgentError(null)
    setHumanReview(null)
    setReviewerNote('')
    setReviewError(null)

    try {
      const ticket = await getTicket(ticketId)

      setSelectedTicket(ticket)
      await loadLatestAgentRun(ticketId)
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'An unexpected error occurred'

      setTicketError(message)
    } finally {
      setIsTicketLoading(false)
    }
  }

  async function handleRunAgent() {
    if (!selectedTicket) {
      return
    }

    setIsAgentRunning(true)
    setAgentError(null)
    setAgentRun(null)
    setHumanReview(null)
    setReviewerNote('')
    setReviewError(null)

    try {
      const createdRun = await createAgentRun(selectedTicket.id)
      const completedRun = await executeAgentRun(createdRun.id)

      setAgentRun(completedRun)
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'An unexpected error occurred'

      setAgentError(message)
    } finally {
      setIsAgentRunning(false)
    }
  }

  async function handleReviewAction(action: HumanReviewAction) {
    if (!agentRun || !selectedTicket || humanReview) {
      return
    }

    const normalizedNote = reviewerNote.trim()

    if (action === 'request_revision' && !normalizedNote) {
      setReviewError('Add a reviewer note before requesting revision.')
      return
    }

    setIsReviewSubmitting(true)
    setReviewError(null)

    try {
      const review = await createHumanReview(agentRun.id, {
        action,
        reviewer_note: normalizedNote || null,
        revised_response: null,
      })

      setHumanReview(review)
      await refreshSelectedTicket(selectedTicket.id)
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'An unexpected error occurred'

      setReviewError(message)
    } finally {
      setIsReviewSubmitting(false)
    }
  }

  return (
    <main className="workspace">
      <header className="workspace-header">
        <div>
          <p className="eyebrow">Support operations</p>
          <h1>SupportPilot</h1>
        </div>

        <div className="connection-status">
          <span aria-hidden="true" />
          Local workspace
        </div>
      </header>

      <section className="workspace-grid">
        <aside className="ticket-queue">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Incoming work</p>
              <h2>Ticket queue</h2>
            </div>

            <span className="ticket-count">{tickets.length}</span>
          </div>

          {isQueueLoading && (
            <p className="state-message">Loading tickets…</p>
          )}

          {queueError && (
            <p className="state-message error-message">
              Unable to load tickets: {queueError}
            </p>
          )}

          {!isQueueLoading && !queueError && tickets.length === 0 && (
            <p className="state-message">No support tickets found.</p>
          )}

          <div className="ticket-list">
            {tickets.map((ticket) => (
              <button
                className={`ticket-card ${selectedTicket?.id === ticket.id
                  ? 'ticket-card-selected'
                  : ''
                  }`}
                key={ticket.id}
                onClick={() => void handleTicketSelect(ticket.id)}
                type="button"
              >
                <div className="ticket-card-topline">
                  <span className={`priority priority-${ticket.priority}`}>
                    {ticket.priority}
                  </span>

                  <span>{formatLabel(ticket.status)}</span>
                </div>

                <h3>{ticket.subject}</h3>
                <p>{ticket.customer.full_name}</p>
              </button>
            ))}
          </div>
        </aside>

        <section className="ticket-workspace">
          {isTicketLoading && (
            <p className="state-message">Loading ticket…</p>
          )}

          {ticketError && (
            <p className="state-message error-message">
              Unable to load ticket: {ticketError}
            </p>
          )}

          {!isTicketLoading && !ticketError && selectedTicket && (
            <>
              <header className="ticket-detail-header">
                <div>
                  <p className="eyebrow">Selected ticket</p>
                  <h2>{selectedTicket.subject}</h2>
                </div>

                <div className="ticket-header-actions">
                  <div className="ticket-badges">
                    <span
                      className={`priority priority-${selectedTicket.priority}`}
                    >
                      {selectedTicket.priority}
                    </span>

                    <span className="status-badge">
                      {formatLabel(selectedTicket.status)}
                    </span>
                  </div>

                  <button
                    className="run-agent-button"
                    disabled={isAgentRunning || isReviewSubmitting}
                    onClick={() => void handleRunAgent()}
                    type="button"
                  >
                    {isAgentRunning ? 'Running agent…' : 'Run agent'}
                  </button>
                </div>
              </header>

              <div className="ticket-detail-content">
                <section className="detail-section">
                  <p className="eyebrow">Customer</p>
                  <h3>{selectedTicket.customer.full_name}</h3>
                  <p>{selectedTicket.customer.email}</p>
                </section>

                <section className="detail-section">
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">Customer context</p>
                      <h3>Orders</h3>
                    </div>

                    <span className="ticket-count">
                      {selectedTicket.customer_orders.length}
                    </span>
                  </div>

                  {selectedTicket.customer_orders.length === 0 ? (
                    <p>No orders found for this customer.</p>
                  ) : (
                    <div className="order-list">
                      {selectedTicket.customer_orders.map((order) => (
                        <article className="order-card" key={order.id}>
                          <div>
                            <strong>{order.order_number}</strong>
                            <span>{formatDate(order.created_at)}</span>
                          </div>

                          <div>
                            <span className="order-status">
                              {formatLabel(order.status)}
                            </span>
                            <strong>
                              {formatCurrency(order.total_cents)}
                            </strong>
                          </div>

                          {order.tracking_number && (
                            <p>Tracking: {order.tracking_number}</p>
                          )}
                        </article>
                      ))}
                    </div>
                  )}
                </section>

                <section className="detail-section">
                  <p className="eyebrow">Request</p>
                  <p className="ticket-description">
                    {selectedTicket.description}
                  </p>
                </section>

                {agentRun?.drafted_response && (
                  <section className="draft-section">
                    <div className="section-heading">
                      <div>
                        <p className="eyebrow">Agent artifact</p>
                        <h3>Drafted response</h3>
                      </div>

                      <span className="status-badge">
                        Human approval required
                      </span>
                    </div>

                    <pre className="drafted-response">
                      {agentRun.drafted_response}
                    </pre>
                  </section>
                )}

                {agentRun && (
                  <section className="review-section">
                    <div className="section-heading">
                      <div>
                        <p className="eyebrow">Human control</p>
                        <h3>Review decision</h3>
                      </div>

                      {humanReview && (
                        <span className="review-complete-badge">
                          {formatLabel(humanReview.action)}
                        </span>
                      )}
                    </div>

                    {humanReview ? (
                      <div className="review-result">
                        <strong>
                          Decision recorded: {formatLabel(humanReview.action)}
                        </strong>

                        {humanReview.reviewer_note && (
                          <p>{humanReview.reviewer_note}</p>
                        )}

                        <span>
                          Ticket status: {formatLabel(selectedTicket.status)}
                        </span>
                      </div>
                    ) : (
                      <>
                        <label className="review-note-field">
                          Reviewer note
                          <textarea
                            disabled={isReviewSubmitting}
                            onChange={(event) =>
                              setReviewerNote(event.target.value)
                            }
                            placeholder="Required for revision requests; optional for approval or escalation."
                            rows={4}
                            value={reviewerNote}
                          />
                        </label>

                        {reviewError && (
                          <p className="review-error">{reviewError}</p>
                        )}

                        <div className="review-actions">
                          <button
                            className="review-button approve-button"
                            disabled={isReviewSubmitting}
                            onClick={() =>
                              void handleReviewAction('approve')
                            }
                            type="button"
                          >
                            Approve draft
                          </button>

                          <button
                            className="review-button revision-button"
                            disabled={isReviewSubmitting}
                            onClick={() =>
                              void handleReviewAction('request_revision')
                            }
                            type="button"
                          >
                            Request revision
                          </button>

                          <button
                            className="review-button escalate-button"
                            disabled={isReviewSubmitting}
                            onClick={() =>
                              void handleReviewAction('escalate')
                            }
                            type="button"
                          >
                            Escalate
                          </button>
                        </div>
                      </>
                    )}
                  </section>
                )}

                <section className="ticket-metadata">
                  <div>
                    <span>Created</span>
                    <strong>{formatDate(selectedTicket.created_at)}</strong>
                  </div>

                  <div>
                    <span>Last updated</span>
                    <strong>{formatDate(selectedTicket.updated_at)}</strong>
                  </div>

                  <div>
                    <span>Ticket ID</span>
                    <strong>{selectedTicket.id}</strong>
                  </div>
                </section>
              </div>
            </>
          )}

          {!isTicketLoading && !ticketError && !selectedTicket && (
            <div className="empty-panel-content">
              <p className="eyebrow">Ticket workspace</p>
              <h2>Select a ticket</h2>
              <p>Ticket details and customer context will appear here.</p>
            </div>
          )}
        </section>

        <aside className="trace-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Agent activity</p>
              <h2>Run trace</h2>
            </div>

            {agentRun && (
              <span className="ticket-count">
                {agentRun.steps.length}
              </span>
            )}
          </div>

          {isAgentRunning && (
            <div className="trace-empty">
              <p className="eyebrow">Workflow running</p>
              <h3>Processing ticket</h3>
              <p>
                The agent is gathering evidence and preparing a recommendation.
              </p>
            </div>
          )}

          {agentError && (
            <p className="state-message error-message">
              Unable to run agent: {agentError}
            </p>
          )}

          {!isAgentRunning && !agentError && !agentRun && (
            <div className="trace-empty">
              <p className="eyebrow">No active run</p>
              <h3>Run the agent</h3>
              <p>
                Classification, evidence, tool calls, and recommendations will
                appear here.
              </p>
            </div>
          )}

          {!isAgentRunning && agentRun && (
            <>
              <section className="run-summary">
                <div>
                  <span>Status</span>
                  <strong>{formatLabel(agentRun.status)}</strong>
                </div>

                <div>
                  <span>Recommendation</span>
                  <strong>
                    {agentRun.recommendation
                      ? formatLabel(agentRun.recommendation)
                      : 'None'}
                  </strong>
                </div>

                <div>
                  <span>Confidence</span>
                  <strong>{formatConfidence(agentRun.confidence)}</strong>
                </div>
              </section>

              <div className="trace-list">
                {agentRun.steps.map((step) => (
                  <article className="trace-step" key={step.id}>
                    <div className="trace-step-marker">
                      {step.sequence_number}
                    </div>

                    <div className="trace-step-content">
                      <div className="trace-step-heading">
                        <h3>{formatLabel(step.step_type)}</h3>
                        <span>{formatConfidence(step.confidence)}</span>
                      </div>

                      <p>{getStepSummary(step)}</p>

                      <div className="trace-step-status">
                        {formatLabel(step.status)}
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </>
          )}
        </aside>
      </section>
    </main>
  )
}

export default App