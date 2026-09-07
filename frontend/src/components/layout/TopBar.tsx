import { useTheme } from '../../hooks/useTheme'
import type { Theme } from '../../contexts/theme-context'
const themes: Theme[] = [
  'light',
  'dark',
  'system',
]

function TopBar() {
  const {
    theme,
    setTheme,
  } = useTheme()

  return (
    <header
      className="
        flex
        h-14
        items-center
        justify-between
        border-b
        border-[var(--border)]
        bg-[var(--background)]
        px-5
      "
    >
      <div>
        <h1 className="text-sm font-semibold">
          QueryPilot
        </h1>
      </div>

      <div className="flex items-center gap-3">
        <select
          value={theme}
          onChange={(event) =>
            setTheme(event.target.value as Theme)
          }
          className="
            rounded-md
            border
            border-[var(--border)]
            bg-[var(--surface)]
            px-2
            py-1.5
            text-sm
            text-[var(--text-primary)]
            outline-none
            focus:border-[var(--accent)]
          "
          aria-label="Appearance"
        >
          {themes.map((option) => (
            <option
              key={option}
              value={option}
            >
              {option[0].toUpperCase() +
                option.slice(1)}
            </option>
          ))}
        </select>

        <button
          type="button"
          className="
            rounded-md
            border
            border-[var(--border)]
            bg-[var(--surface)]
            px-3
            py-1.5
            text-sm
            hover:bg-[var(--surface-hover)]
          "
        >
          Settings
        </button>
      </div>
    </header>
  )
}

export default TopBar