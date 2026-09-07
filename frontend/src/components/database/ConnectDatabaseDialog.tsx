import { useState } from 'react'

type ConnectionMode =
  | 'url'
  | 'manual'

type ConnectDatabaseDialogProps = {
  open: boolean
  onClose: () => void
}

function ConnectDatabaseDialog({
  open,
  onClose,
}: ConnectDatabaseDialogProps) {
  const [
    mode,
    setMode,
  ] = useState<ConnectionMode>('url')

  if (!open) {
    return null
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
        {/* Header */}
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

        {/* Body */}
        <div className="px-6 py-5">
          {/* Connection tabs */}
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
              onClick={() => setMode('url')}
              className={`
                flex-1
                rounded-md
                px-3
                py-2
                text-sm
                font-medium
                transition-colors
                ${
                  mode === 'url'
                    ? `
                      bg-[var(--surface-raised)]
                      text-[var(--text-primary)]
                      shadow-sm
                    `
                    : `
                      text-[var(--text-secondary)]
                      hover:text-[var(--text-primary)]
                    `
                }
              `}
            >
              Connection URL
            </button>

            <button
              type="button"
              onClick={() => setMode('manual')}
              className={`
                flex-1
                rounded-md
                px-3
                py-2
                text-sm
                font-medium
                transition-colors
                ${
                  mode === 'manual'
                    ? `
                      bg-[var(--surface-raised)]
                      text-[var(--text-primary)]
                      shadow-sm
                    `
                    : `
                      text-[var(--text-secondary)]
                      hover:text-[var(--text-primary)]
                    `
                }
              `}
            >
              Manual setup
            </button>
          </div>

          {/* URL connection */}
          {mode === 'url' && (
            <div className="mt-5">
              <label
                htmlFor="database-url"
                className="
                  text-sm
                  font-medium
                  text-[var(--text-primary)]
                "
              >
                PostgreSQL connection URL
              </label>

              <input
                id="database-url"
                type="password"
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
                  text-[var(--text-primary)]
                  outline-none
                  placeholder:text-[var(--text-muted)]
                  focus:border-[var(--accent)]
                  focus:ring-2
                  focus:ring-[color-mix(in_srgb,var(--accent)_20%,transparent)]
                "
              />

              <p
                className="
                  mt-2
                  text-xs
                  text-[var(--text-muted)]
                "
              >
                Your credentials will only be sent to the
                QueryPilot backend.
              </p>
            </div>
          )}

          {/* Manual connection */}
          {mode === 'manual' && (
            <div className="mt-5 space-y-4">
              <div>
                <label
                  htmlFor="database-host"
                  className="
                    text-sm
                    font-medium
                    text-[var(--text-primary)]
                  "
                >
                  Host
                </label>

                <input
                  id="database-host"
                  type="text"
                  placeholder="localhost"
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
                    text-[var(--text-primary)]
                    outline-none
                    placeholder:text-[var(--text-muted)]
                    focus:border-[var(--accent)]
                  "
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label
                    htmlFor="database-port"
                    className="
                      text-sm
                      font-medium
                      text-[var(--text-primary)]
                    "
                  >
                    Port
                  </label>

                  <input
                    id="database-port"
                    type="text"
                    defaultValue="5432"
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
                      text-[var(--text-primary)]
                      outline-none
                      focus:border-[var(--accent)]
                    "
                  />
                </div>

                <div className="col-span-2">
                  <label
                    htmlFor="database-name"
                    className="
                      text-sm
                      font-medium
                      text-[var(--text-primary)]
                    "
                  >
                    Database
                  </label>

                  <input
                    id="database-name"
                    type="text"
                    placeholder="llm_sql"
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
                      text-[var(--text-primary)]
                      outline-none
                      placeholder:text-[var(--text-muted)]
                      focus:border-[var(--accent)]
                    "
                  />
                </div>
              </div>

              <div>
                <label
                  htmlFor="database-username"
                  className="
                    text-sm
                    font-medium
                    text-[var(--text-primary)]
                  "
                >
                  Username
                </label>

                <input
                  id="database-username"
                  type="text"
                  placeholder="postgres"
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
                    text-[var(--text-primary)]
                    outline-none
                    placeholder:text-[var(--text-muted)]
                    focus:border-[var(--accent)]
                  "
                />
              </div>

              <div>
                <label
                  htmlFor="database-password"
                  className="
                    text-sm
                    font-medium
                    text-[var(--text-primary)]
                  "
                >
                  Password
                </label>

                <input
                  id="database-password"
                  type="password"
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
                    text-[var(--text-primary)]
                    outline-none
                    placeholder:text-[var(--text-muted)]
                    focus:border-[var(--accent)]
                  "
                />
              </div>

              <div>
                <label
                  htmlFor="ssl-mode"
                  className="
                    text-sm
                    font-medium
                    text-[var(--text-primary)]
                  "
                >
                  SSL mode
                </label>

                <select
                  id="ssl-mode"
                  defaultValue="prefer"
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
                    text-[var(--text-primary)]
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

          {/* Read-only guidance */}
          <div
            className="
              mt-5
              rounded-lg
              border
              border-[var(--border)]
              bg-[var(--surface)]
              px-4
              py-3
            "
          >
            <p
              className="
                text-sm
                font-medium
                text-[var(--text-primary)]
              "
            >
              Read-only access recommended
            </p>

            <p
              className="
                mt-1
                text-xs
                leading-5
                text-[var(--text-secondary)]
              "
            >
              For production databases, connect using a PostgreSQL
              user that only has SELECT permissions.
            </p>
          </div>
        </div>

        {/* Footer */}
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
            className="
              rounded-md
              border
              border-[var(--border)]
              bg-[var(--surface)]
              px-4
              py-2
              text-sm
              font-medium
              text-[var(--text-primary)]
              hover:bg-[var(--surface-hover)]
            "
          >
            Cancel
          </button>

          <button
            type="button"
            className="
              rounded-md
              bg-[var(--accent)]
              px-4
              py-2
              text-sm
              font-medium
              text-[var(--accent-foreground)]
              hover:bg-[var(--accent-hover)]
            "
          >
            Test Connection
          </button>
        </div>
      </div>
    </div>
  )
}

export default ConnectDatabaseDialog