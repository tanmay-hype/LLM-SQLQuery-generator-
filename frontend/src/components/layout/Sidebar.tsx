type SidebarProps = {
  onConnectDatabase: () => void
}

function Sidebar({
  onConnectDatabase,
}: SidebarProps) {
  return (
    <aside
      className="
        flex
        h-full
        w-64
        flex-col
        border-r
        border-[var(--border)]
        bg-[var(--sidebar-background)]
      "
    >
      <div className="px-4 py-4">
        <button
          type="button"
          className="
            flex
            w-full
            items-center
            justify-center
            rounded-md
            bg-[var(--accent)]
            px-3
            py-2
            text-sm
            font-medium
            text-[var(--accent-foreground)]
            hover:bg-[var(--accent-hover)]
          "
        >
          + New Query
        </button>
      </div>

      <nav className="px-3">
        <p
          className="
            mb-2
            px-2
            text-xs
            font-semibold
            uppercase
            tracking-wide
            text-[var(--text-muted)]
          "
        >
          Workspace
        </p>

        <div className="space-y-1">
          <button
            type="button"
            className="
              w-full
              rounded-md
              bg-[var(--surface-hover)]
              px-3
              py-2
              text-left
              text-sm
              font-medium
              text-[var(--text-primary)]
            "
          >
            Query
          </button>

          <button
            type="button"
            className="
              w-full
              rounded-md
              px-3
              py-2
              text-left
              text-sm
              text-[var(--text-secondary)]
              hover:bg-[var(--surface-hover)]
            "
          >
            Schema
          </button>

          <button
            type="button"
            className="
              w-full
              rounded-md
              px-3
              py-2
              text-left
              text-sm
              text-[var(--text-secondary)]
              hover:bg-[var(--surface-hover)]
            "
          >
            History
          </button>
        </div>
      </nav>

      <div
        className="
          mt-auto
          border-t
          border-[var(--border)]
          p-4
        "
      >
        <p
          className="
            mb-2
            text-xs
            font-semibold
            uppercase
            tracking-wide
            text-[var(--text-muted)]
          "
        >
          Database
        </p>

        <div
          className="
            rounded-md
            border
            border-[var(--border)]
            bg-[var(--surface-raised)]
            p-3
          "
        >
          <p className="text-sm font-medium">
            No database connected
          </p>

          <p
            className="
              mt-1
              text-xs
              text-[var(--text-secondary)]
            "
          >
            Connect PostgreSQL to start querying.
          </p>

          <button
            type="button"
            onClick={onConnectDatabase}
            className="
              mt-3
              w-full
              rounded-md
              border
              border-[var(--border)]
              bg-[var(--surface)]
              px-3
              py-2
              text-sm
              font-medium
              hover:bg-[var(--surface-hover)]
            "
          >
            Connect Database
          </button>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar