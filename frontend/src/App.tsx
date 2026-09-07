import { useTheme } from './hooks/useTheme'
import type { Theme } from './contexts/ThemeContext'

const themes: Theme[] = [
  'light',
  'dark',
  'system',
]

function App() {
  const {
    theme,
    resolvedTheme,
    setTheme,
  } = useTheme()

  return (
    <main
      className="
        min-h-screen
        bg-[var(--background)]
        text-[var(--text-primary)]
      "
    >
      <div className="mx-auto max-w-3xl px-6 py-16">
        <p
          className="
            mb-2
            text-sm
            font-medium
            text-[var(--accent)]
          "
        >
          QueryPilot
        </p>

        <h1 className="text-3xl font-semibold tracking-tight">
          Theme foundation
        </h1>

        <p
          className="
            mt-3
            text-[var(--text-secondary)]
          "
        >
          Current appearance: {theme}
          {' · '}
          Rendering: {resolvedTheme}
        </p>

        <div
          className="
            mt-8
            rounded-xl
            border
            border-[var(--border)]
            bg-[var(--surface)]
            p-5
          "
        >
          <p className="mb-4 text-sm font-medium">
            Appearance
          </p>

          <div className="flex gap-2">
            {themes.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setTheme(option)}
                className={`
                  rounded-md
                  border
                  px-4
                  py-2
                  text-sm
                  font-medium
                  transition-colors
                  ${
                    theme === option
                      ? `
                        border-[var(--accent)]
                        bg-[var(--accent)]
                        text-[var(--accent-foreground)]
                      `
                      : `
                        border-[var(--border)]
                        bg-[var(--surface-raised)]
                        text-[var(--text-primary)]
                        hover:bg-[var(--surface-hover)]
                      `
                  }
                `}
              >
                {option[0].toUpperCase() +
                  option.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-6 flex gap-5 text-sm">
          <span className="text-[var(--success)]">
            ● Connected
          </span>

          <span className="text-[var(--warning)]">
            ● Warning
          </span>

          <span className="text-[var(--danger)]">
            ● Error
          </span>
        </div>
      </div>
    </main>
  )
}

export default App