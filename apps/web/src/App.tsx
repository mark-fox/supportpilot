import { useEffect, useState } from 'react'

import { getTicket, getTickets } from './api/tickets'
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

function App() {
  const [tickets, setTickets] = useState<TicketSummary[]>([])
  const [selectedTicket, setSelectedTicket] =
    useState<TicketDetail | null>(null)
  const [isQueueLoading, setIsQueueLoading] = useState(true)
  const [isTicketLoading, setIsTicketLoading] = useState(false)
  const [queueError, setQueueError] = useState<string | null>(null)
  const [ticketError, setTicketError] = useState<string | null>(null)

  useEffect(() => {
    async function loadTickets() {
      try {
        const loadedTickets = await getTickets()
        setTickets(loadedTickets)

        if (loadedTickets.length > 0) {
          const firstTicket = await getTicket(loadedTickets[0].id)
          setSelectedTicket(firstTicket)
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

  async function handleTicketSelect(ticketId: string) {
    if (selectedTicket?.id === ticketId) {
      return
    }

    setIsTicketLoading(true)
    setTicketError(null)

    try {
      const ticket = await getTicket(ticketId)
      setSelectedTicket(ticket)
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

                  <span>{ticket.status.replace('_', ' ')}</span>
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

                <div className="ticket-badges">
                  <span
                    className={`priority priority-${selectedTicket.priority}`}
                  >
                    {selectedTicket.priority}
                  </span>

                  <span className="status-badge">
                    {selectedTicket.status.replace('_', ' ')}
                  </span>
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
                              {order.status}
                            </span>
                            <strong>{formatCurrency(order.total_cents)}</strong>
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
              <p>
                Ticket details and customer context will appear here.
              </p>
            </div>
          )}
        </section>

        <aside className="empty-panel trace-panel">
          <p className="eyebrow">Agent activity</p>
          <h2>Run trace</h2>
          <p>
            Classification, evidence, tool calls, and recommendations will
            appear here.
          </p>
        </aside>
      </section>
    </main>
  )
}

export default App