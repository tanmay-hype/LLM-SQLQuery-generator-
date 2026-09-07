import { useState } from 'react'

type ConnectionMode =
  | 'url'
  | 'manual'

type ConnectionStatus =
  | 'idle'
  | 'testing'
  | 'success'
  | 'error'

type ConnectDatabaseDialogProps = {
  open: boolean
  onClose: () => void
}

type TestConnectionResponse = {
  success: boolean
  message: string
  database?: string | null
  server_version?: string | null
}

function ConnectDatabaseDialog({
  open,
  onClose,
}: ConnectDatabaseDialogProps) {
  const [
    mode,
    setMode,
  ] = useState<ConnectionMode>('url')

  const [
    connectionUrl,
    setConnectionUrl,
  ] = useState('')

  const [
    host,
    setHost,
  ] = useState('postgres-db')

  const [
    port,
    setPort,
  ] = useState('5432')

  const [
    database,
    setDatabase,
  ] = useState('llm_sql')

  const [
    username,
    setUsername,
  ] = useState('postgres')

  const [
    password,
    setPassword,
  ] = useState('')

  const [
    sslMode,
    setSslMode,
  ] = useState<
    'disable' | 'prefer' | 'require'
  >('disable')

  const [
    status,
    setStatus,
  ] = useState<ConnectionStatus>('idle')

  const [
    statusMessage,
    setStatusMessage,
  ] = useState('')

  const [
    connectedDatabase,
    setConnectedDatabase,
  ] = useState('')

  const [
    serverVersion,
    setServerVersion,
  ] = useState('')

  if (!open) {
    return null
  }

  async function handleTestConnection() {
    setStatus('testing')
    setStatusMessage('')
    setConnectedDatabase('')
    setServerVersion('')

    const payload =
      mode === 'url'
        ? {
            mode: 'url',
            connection_url:
              connectionUrl,
          }
        : {
            mode: 'manual',
            host,
            port: Number(port),
            database,
            username,
            password,
            ssl_mode: sslMode,
          }

    try {
      const response = await fetch(
        'http://localhost:8000/connections/test',
        {
          method: 'POST',
          headers: {
            'Content-Type':
              'application/json',
          },
          body: JSON.stringify(payload),
        },
      )

      const data = await response.json()

      if (!response.ok) {
        let message =
          'Connection failed.'

        if (
          typeof data?.detail ===
          'string'
        ) {
          message = data.detail
        }

        if (
          Array.isArray(data?.detail) &&
          data.detail.length > 0
        ) {
          message =
            data.detail[0]?.msg ??
            message
        }

        throw new Error(message)
      }

      const result =
        data as TestConnectionResponse

      setStatus('success')
      setStatusMessage(
        result.message,
      )
      setConnectedDatabase(
        result.database ?? '',
      )
      setServerVersion(
        result.server_version ?? '',
      )
    } catch (error) {
      setStatus('error')

      if (
        error instanceof Error
      ) {
        setStatusMessage(
          error.message,
        )
      } else {
        setStatusMessage(
          'Connection failed.',
        )
      }
    }
  }

  return (
    <div
      className="
        fixed
        inset-0
        z-50
        flex
        items-center
        justify-center
        bg-black/50
        px-4
      "
      role="dialog"
      aria-modal="true"
      aria-labelledby="connect-database-title"
    >
      <div
        className="
          w-full
          max-w-xl
          rounded-xl
          border
          border-[var(--border)]
          bg-[var(--surface-raised)]
          shadow-2xl
        "
      >
        <div
          className="
            flex
            items-start
            justify-between
            border-b
            border-[var(--border)]
            px-6
            py-5
          "
        >
          <div>
            <h2
              id="connect-database-title"
              className="
                text-lg
                font-semibold
                text-[var(--text-primary)]
              "
            >
              Connect PostgreSQL
            </h2>

            <p
              className="
                mt-1
                text-sm
                text-[var(--text-secondary)]
              "
            >
              Connect a database to start asking questions.
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="
              flex
              h-8
              w-8
              items-center
              justify-center
              rounded-md
              text-[var(--text-secondary)]
              hover:bg-[var(--surface-hover)]
              hover:text-[var(--text-primary)]
            "
            aria-label="Close dialog"
          >
            ×
          </button>
        </div>

        <div className="px-6 py-5">
          <div
            className="
              flex
              rounded-lg
              border
              border-[var(--border)]
              bg-[var(--surface)]
              p-1
            "
          >
            <button
              type="button"
              onClick={() => {
                setMode('url')
                setStatus('idle')
              }}
              className={`
                flex-1
                rounded-md
                px-3
                py-2
                text-sm
                font-medium
                ${
                  mode === 'url'
                    ? `
                      bg-[var(--surface-raised)]
                      text-[var(--text-primary)]
                      shadow-sm
                    `
                    : `
                      text-[var(--text-secondary)]
                    `
                }
              `}
            >
              Connection URL
            </button>

            <button
              type="button"
              onClick={() => {
                setMode('manual')
                setStatus('idle')
              }}
              className={`
                flex-1
                rounded-md
                px-3
                py-2
                text-sm
                font-medium
                ${
                  mode === 'manual'
                    ? `
                      bg-[var(--surface-raised)]
                      text-[var(--text-primary)]
                      shadow-sm
                    `
                    : `
                      text-[var(--text-secondary)]
                    `
                }
              `}
            >
              Manual setup
            </button>
          </div>

          {mode === 'url' && (
            <div className="mt-5">
              <label
                htmlFor="database-url"
                className="text-sm font-medium"
              >
                PostgreSQL connection URL
              </label>

              <input
                id="database-url"
                type="password"
                value={connectionUrl}
                onChange={(event) =>
                  setConnectionUrl(
                    event.target.value,
                  )
                }
                placeholder="postgresql://user:password@host:5432/database"
                className="
                  mt-2
                  w-full
                  rounded-md
                  border
                  border-[var(--border)]
                  bg-[var(--background)]
                  px-3
                  py-2.5
                  text-sm
                  outline-none
                  focus:border-[var(--accent)]
                "
              />
            </div>
          )}

          {mode === 'manual' && (
            <div className="mt-5 space-y-4">
              <div>
                <label
                  htmlFor="database-host"
                  className="text-sm font-medium"
                >
                  Host
                </label>

                <input
                  id="database-host"
                  value={host}
                  onChange={(event) =>
                    setHost(
                      event.target.value,
                    )
                  }
                  className="
                    mt-2
                    w-full
                    rounded-md
                    border
                    border-[var(--border)]
                    bg-[var(--background)]
                    px-3
                    py-2.5
                    text-sm
                    outline-none
                    focus:border-[var(--accent)]
                  "
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label
                    htmlFor="database-port"
                    className="text-sm font-medium"
                  >
                    Port
                  </label>

                  <input
                    id="database-port"
                    value={port}
                    onChange={(event) =>
                      setPort(
                        event.target.value,
                      )
                    }
                    className="
                      mt-2
                      w-full
                      rounded-md
                      border
                      border-[var(--border)]
                      bg-[var(--background)]
                      px-3
                      py-2.5
                      text-sm
                      outline-none
                      focus:border-[var(--accent)]
                    "
                  />
                </div>

                <div className="col-span-2">
                  <label
                    htmlFor="database-name"
                    className="text-sm font-medium"
                  >
                    Database
                  </label>

                  <input
                    id="database-name"
                    value={database}
                    onChange={(event) =>
                      setDatabase(
                        event.target.value,
                      )
                    }
                    className="
                      mt-2
                      w-full
                      rounded-md
                      border
                      border-[var(--border)]
                      bg-[var(--background)]
                      px-3
                      py-2.5
                      text-sm
                      outline-none
                      focus:border-[var(--accent)]
                    "
                  />
                </div>
              </div>

              <div>
                <label
                  htmlFor="database-username"
                  className="text-sm font-medium"
                >
                  Username
                </label>

                <input
                  id="database-username"
                  value={username}
                  onChange={(event) =>
                    setUsername(
                      event.target.value,
                    )
                  }
                  className="
                    mt-2
                    w-full
                    rounded-md
                    border
                    border-[var(--border)]
                    bg-[var(--background)]
                    px-3
                    py-2.5
                    text-sm
                    outline-none
                    focus:border-[var(--accent)]
                  "
                />
              </div>

              <div>
                <label
                  htmlFor="database-password"
                  className="text-sm font-medium"
                >
                  Password
                </label>

                <input
                  id="database-password"
                  type="password"
                  value={password}
                  onChange={(event) =>
                    setPassword(
                      event.target.value,
                    )
                  }
                  placeholder="Enter database password"
                  className="
                    mt-2
                    w-full
                    rounded-md
                    border
                    border-[var(--border)]
                    bg-[var(--background)]
                    px-3
                    py-2.5
                    text-sm
                    outline-none
                    focus:border-[var(--accent)]
                  "
                />
              </div>

              <div>
                <label
                  htmlFor="ssl-mode"
                  className="text-sm font-medium"
                >
                  SSL mode
                </label>

                <select
                  id="ssl-mode"
                  value={sslMode}
                  onChange={(event) =>
                    setSslMode(
                      event.target.value as
                        | 'disable'
                        | 'prefer'
                        | 'require',
                    )
                  }
                  className="
                    mt-2
                    w-full
                    rounded-md
                    border
                    border-[var(--border)]
                    bg-[var(--background)]
                    px-3
                    py-2.5
                    text-sm
                    outline-none
                    focus:border-[var(--accent)]
                  "
                >
                  <option value="disable">
                    Disable
                  </option>

                  <option value="prefer">
                    Prefer
                  </option>

                  <option value="require">
                    Require
                  </option>
                </select>
              </div>
            </div>
          )}

          {status === 'success' && (
            <div
              className="
                mt-5
                rounded-lg
                border
                border-[var(--success)]
                px-4
                py-3
              "
            >
              <p
                className="
                  text-sm
                  font-medium
                  text-[var(--success)]
                "
              >
                Connection successful
              </p>

              <p
                className="
                  mt-1
                  text-xs
                  text-[var(--text-secondary)]
                "
              >
                {connectedDatabase}
                {serverVersion &&
                  ` · PostgreSQL ${serverVersion}`}
              </p>
            </div>
          )}

          {status === 'error' && (
            <div
              className="
                mt-5
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
                Connection failed
              </p>

              <p
                className="
                  mt-1
                  text-xs
                  text-[var(--text-secondary)]
                "
              >
                {statusMessage}
              </p>
            </div>
          )}
        </div>

        <div
          className="
            flex
            items-center
            justify-end
            gap-2
            border-t
            border-[var(--border)]
            px-6
            py-4
          "
        >
          <button
            type="button"
            onClick={onClose}
            disabled={
              status === 'testing'
            }
            className="
              rounded-md
              border
              border-[var(--border)]
              bg-[var(--surface)]
              px-4
              py-2
              text-sm
              font-medium
              hover:bg-[var(--surface-hover)]
              disabled:cursor-not-allowed
              disabled:opacity-50
            "
          >
            Cancel
          </button>

          <button
            type="button"
            onClick={
              handleTestConnection
            }
            disabled={
              status === 'testing'
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
              disabled:opacity-60
            "
          >
            {status === 'testing'
              ? 'Testing...'
              : 'Test Connection'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ConnectDatabaseDialog