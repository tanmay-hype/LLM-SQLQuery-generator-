function QueryWorkspace() {
  return (
    <main
      className="
        flex
        flex-1
        items-center
        justify-center
        overflow-auto
        bg-[var(--background)]
        px-6
        py-12
      "
    >
      <div className="w-full max-w-3xl">
        <div className="text-center">
          <div
            className="
              mx-auto
              mb-4
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

          <h2 className="text-2xl font-semibold tracking-tight">
            Ask your database
          </h2>

          <p
            className="
              mx-auto
              mt-2
              max-w-xl
              text-sm
              text-[var(--text-secondary)]
            "
          >
            Connect PostgreSQL, then ask questions in natural
            language. QueryPilot will generate and validate the SQL
            for you.
          </p>
        </div>

        <div
          className="
            mt-8
            rounded-xl
            border
            border-[var(--border)]
            bg-[var(--surface-raised)]
            p-3
            shadow-sm
          "
        >
          <textarea
            rows={4}
            placeholder="Ask a question about your data..."
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
            "
          />

          <div className="flex items-center justify-between pt-2">
            <span
              className="
                px-2
                text-xs
                text-[var(--text-muted)]
              "
            >
              PostgreSQL
            </span>

            <button
              type="button"
              disabled
              className="
                rounded-md
                bg-[var(--accent)]
                px-4
                py-2
                text-sm
                font-medium
                text-[var(--accent-foreground)]
                opacity-50
              "
            >
              Generate
            </button>
          </div>
        </div>

        <div
          className="
            mt-4
            flex
            flex-wrap
            justify-center
            gap-2
          "
        >
          {[
            'Top customers',
            'Monthly revenue',
            'Recent orders',
            'Products by category',
          ].map((example) => (
            <button
              key={example}
              type="button"
              className="
                rounded-full
                border
                border-[var(--border)]
                bg-[var(--surface)]
                px-3
                py-1.5
                text-xs
                text-[var(--text-secondary)]
                hover:bg-[var(--surface-hover)]
                hover:text-[var(--text-primary)]
              "
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </main>
  )
}

export default QueryWorkspace