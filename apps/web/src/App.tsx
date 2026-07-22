import { useEffect, useState } from 'react'

import { getTickets } from './api/tickets'
import type { TicketSummary } from './types/ticket'

function App() {
  const [tickets, setTickets] = useState<TicketSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    async function loadTickets() {
      try {
        const loadedTickets = await getTickets()
        setTickets(loadedTickets)
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : 'An unexpected error occurred'

        setErrorMessage(message)
      } finally {
        setIsLoading(false)
      }
    }

    void loadTickets()
  }, [])

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

          {isLoading && <p className="state-message">Loading tickets…</p>}

          {errorMessage && (
            <p className="state-message error-message">
              Unable to load tickets: {errorMessage}
            </p>
          )}

          {!isLoading && !errorMessage && tickets.length === 0 && (
            <p className="state-message">No support tickets found.</p>
          )}

          <div className="ticket-list">
            {tickets.map((ticket) => (
              <article className="ticket-card" key={ticket.id}>
                <div className="ticket-card-topline">
                  <span className={`priority priority-${ticket.priority}`}>
                    {ticket.priority}
                  </span>

                  <span>{ticket.status.replace('_', ' ')}</span>
                </div>

                <h3>{ticket.subject}</h3>
                <p>{ticket.customer.full_name}</p>
              </article>
            ))}
          </div>
        </aside>

        <section className="empty-panel">
          <p className="eyebrow">Ticket workspace</p>
          <h2>Select a ticket</h2>
          <p>
            Ticket details, customer context, and the agent workflow will
            appear here.
          </p>
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