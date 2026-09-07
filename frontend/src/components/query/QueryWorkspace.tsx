import { useState } from 'react'

import type {
  ActiveConnection,
} from '../database/ConnectDatabaseDialog'

type QueryWorkspaceProps = {
  connection: ActiveConnection | null
}

type QueryResponse = {
  sql: string
  results: Record<string, unknown>[]
}

function QueryWorkspace({
  connection,
}: QueryWorkspaceProps) {
  const [
    question,
    setQuestion,
  ] = useState('')

  const [
    loading,
    setLoading,
  ] = useState(false)

  const [
    error,
    setError,
  ] = useState('')

  const [
    response,
    setResponse,
  ] = useState<QueryResponse | null>(
    null,
  )

  async function handleGenerate() {
    if (
      !connection ||
      !question.trim()
    ) {
      return
    }

    setLoading(true)
    setError('')
    setResponse(null)

    try {
      const result = await fetch(
        'http://localhost:8000/generate-sql',
        {
          method: 'POST',
          headers: {
            'Content-Type':
              'application/json',
          },
          body: JSON.stringify({
            question:
              question.trim(),
            connection_id:
              connection.connectionId,
          }),
        },
      )

      const data =
        await result.json()

      if (!result.ok) {
        let message =
          'Query generation failed.'

        if (
          typeof data?.detail ===
          'string'
        ) {
          message = data.detail
        }

        throw new Error(message)
      }

      setResponse(
        data as QueryResponse,
      )
    } catch (error) {
      if (
        error instanceof Error
      ) {
        setError(error.message)
      } else {
        setError(
          'Query generation failed.',
        )
      }
    } finally {
      setLoading(false)
    }
  }

  const columns =
    response?.results.length
      ? Object.keys(
          response.results[0],
        )
      : []

  return (
    <main
      className="
        flex
        min-h-0
        flex-1
        flex-col
        overflow-hidden
        bg-[var(--background)]
      "
    >
      <div
        className="
          flex-1
          overflow-auto
          px-6
          py-8
        "
      >
        <div
          className="
            mx-auto
            w-full
            max-w-5xl
          "
        >
          {!response &&
          !loading &&
          !error ? (
            <div
              className="
                flex
                min-h-[55vh]
                flex-col
                items-center
                justify-center
                text-center
              "
            >
              <div
                className="
                  flex
                  h-12
                  w-12
                  items-center
                  justify-center
                  rounded-xl
                  border
                  border-[var(--border)]
                  bg-[var(--surface)]
                  text-lg
                  font-semibold
                  text-[var(--accent)]
                "
              >
                Q
              </div>

              <h2
                className="
                  mt-4
                  text-2xl
                  font-semibold
                  tracking-tight
                "
              >
                Ask your database
              </h2>

              <p
                className="
                  mt-2
                  max-w-xl
                  text-sm
                  text-[var(--text-secondary)]
                "
              >
                {connection
                  ? `Connected to ${connection.database}. Ask a question in natural language.`
                  : 'Connect PostgreSQL to start querying your data.'}
              </p>
            </div>
          ) : null}

          {loading && (
            <div
              className="
                py-20
                text-center
                text-sm
                text-[var(--text-secondary)]
              "
            >
              Generating SQL and running query...
            </div>
          )}

          {error && (
            <div
              className="
                rounded-lg
                border
                border-[var(--danger)]
                px-4
                py-3
              "
            >
              <p
                className="
                  text-sm
                  font-medium
                  text-[var(--danger)]
                "
              >
                Query failed
              </p>

              <p
                className="
                  mt-1
                  text-sm
                  text-[var(--text-secondary)]
                "
              >
                {error}
              </p>
            </div>
          )}

          {response && (
            <div className="space-y-6">
              <div>
                <p
                  className="
                    text-sm
                    font-medium
                    text-[var(--text-secondary)]
                  "
                >
                  You asked
                </p>

                <p
                  className="
                    mt-2
                    text-base
                    text-[var(--text-primary)]
                  "
                >
                  {question}
                </p>
              </div>

              <div
                className="
                  overflow-hidden
                  rounded-lg
                  border
                  border-[var(--border)]
                "
              >
                <div
                  className="
                    flex
                    items-center
                    justify-between
                    border-b
                    border-[var(--border)]
                    bg-[var(--surface)]
                    px-4
                    py-2.5
                  "
                >
                  <span
                    className="
                      text-xs
                      font-semibold
                      uppercase
                      tracking-wide
                      text-[var(--text-muted)]
                    "
                  >
                    Generated SQL
                  </span>

                  <button
                    type="button"
                    onClick={() =>
                      navigator.clipboard.writeText(
                        response.sql,
                      )
                    }
                    className="
                      rounded-md
                      px-2
                      py-1
                      text-xs
                      text-[var(--text-secondary)]
                      hover:bg-[var(--surface-hover)]
                      hover:text-[var(--text-primary)]
                    "
                  >
                    Copy
                  </button>
                </div>

                <pre
                  className="
                    overflow-x-auto
                    bg-[var(--code-background)]
                    p-4
                    text-sm
                    leading-6
                    text-[var(--text-primary)]
                  "
                >
                  <code>
                    {response.sql}
                  </code>
                </pre>
              </div>

              <div>
                <div
                  className="
                    mb-3
                    flex
                    items-center
                    justify-between
                  "
                >
                  <h3
                    className="
                      text-sm
                      font-semibold
                    "
                  >
                    Results
                  </h3>

                  <span
                    className="
                      text-xs
                      text-[var(--text-muted)]
                    "
                  >
                    {
                      response.results
                        .length
                    }{' '}
                    rows
                  </span>
                </div>

                {response.results
                  .length === 0 ? (
                  <div
                    className="
                      rounded-lg
                      border
                      border-[var(--border)]
                      p-6
                      text-sm
                      text-[var(--text-secondary)]
                    "
                  >
                    Query returned no rows.
                  </div>
                ) : (
                  <div
                    className="
                      overflow-x-auto
                      rounded-lg
                      border
                      border-[var(--border)]
                    "
                  >
                    <table
                      className="
                        min-w-full
                        border-collapse
                        text-sm
                      "
                    >
                      <thead
                        className="
                          bg-[var(--surface)]
                        "
                      >
                        <tr>
                          {columns.map(
                            (column) => (
                              <th
                                key={
                                  column
                                }
                                className="
                                  border-b
                                  border-[var(--border)]
                                  px-4
                                  py-3
                                  text-left
                                  text-xs
                                  font-semibold
                                  uppercase
                                  tracking-wide
                                  text-[var(--text-muted)]
                                "
                              >
                                {column}
                              </th>
                            ),
                          )}
                        </tr>
                      </thead>

                      <tbody>
                        {response.results.map(
                          (
                            row,
                            rowIndex,
                          ) => (
                            <tr
                              key={
                                rowIndex
                              }
                              className="
                                border-b
                                border-[var(--border-muted)]
                                last:border-b-0
                              "
                            >
                              {columns.map(
                                (
                                  column,
                                ) => (
                                  <td
                                    key={
                                      column
                                    }
                                    className="
                                      whitespace-nowrap
                                      px-4
                                      py-3
                                      text-[var(--text-primary)]
                                    "
                                  >
                                    {String(
                                      row[
                                        column
                                      ] ??
                                        '',
                                    )}
                                  </td>
                                ),
                              )}
                            </tr>
                          ),
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <div
        className="
          border-t
          border-[var(--border)]
          bg-[var(--background)]
          px-6
          py-4
        "
      >
        <div
          className="
            mx-auto
            w-full
            max-w-3xl
          "
        >
          <div
            className="
              rounded-xl
              border
              border-[var(--border)]
              bg-[var(--surface-raised)]
              p-3
              shadow-sm
            "
          >
            <textarea
              rows={3}
              value={question}
              onChange={(event) =>
                setQuestion(
                  event.target.value,
                )
              }
              onKeyDown={(
                event,
              ) => {
                if (
                  event.key ===
                    'Enter' &&
                  (event.metaKey ||
                    event.ctrlKey)
                ) {
                  event.preventDefault()

                  void handleGenerate()
                }
              }}
              disabled={!connection}
              placeholder={
                connection
                  ? 'Ask a question about your data...'
                  : 'Connect a database first...'
              }
              className="
                w-full
                resize-none
                border-0
                bg-transparent
                px-2
                py-2
                text-sm
                text-[var(--text-primary)]
                outline-none
                placeholder:text-[var(--text-muted)]
                disabled:cursor-not-allowed
              "
            />

            <div
              className="
                flex
                items-center
                justify-between
                pt-2
              "
            >
              <span
                className="
                  px-2
                  text-xs
                  text-[var(--text-muted)]
                "
              >
                {connection
                  ? connection.database
                  : 'PostgreSQL'}
              </span>

              <button
                type="button"
                onClick={() =>
                  void handleGenerate()
                }
                disabled={
                  !connection ||
                  !question.trim() ||
                  loading
                }
                className="
                  rounded-md
                  bg-[var(--accent)]
                  px-4
                  py-2
                  text-sm
                  font-medium
                  text-[var(--accent-foreground)]
                  hover:bg-[var(--accent-hover)]
                  disabled:cursor-not-allowed
                  disabled:opacity-50
                "
              >
                {loading
                  ? 'Generating...'
                  : 'Generate'}
              </button>
            </div>
          </div>

          <p
            className="
              mt-2
              text-center
              text-xs
              text-[var(--text-muted)]
            "
          >
            Ctrl/⌘ + Enter to run
          </p>
        </div>
      </div>
    </main>
  )
}

export default QueryWorkspace