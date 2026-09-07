import {
  createContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'

export type Theme = 'light' | 'dark' | 'system'

type ThemeContextValue = {
  theme: Theme
  resolvedTheme: 'light' | 'dark'
  setTheme: (theme: Theme) => void
}

export const ThemeContext =
  createContext<ThemeContextValue | null>(null)

type ThemeProviderProps = {
  children: ReactNode
}

const STORAGE_KEY = 'querypilot-theme'

function getSystemTheme(): 'light' | 'dark' {
  return window.matchMedia(
    '(prefers-color-scheme: dark)',
  ).matches
    ? 'dark'
    : 'light'
}

export function ThemeProvider({
  children,
}: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>(() => {
    const storedTheme = localStorage.getItem(
      STORAGE_KEY,
    )

    if (
      storedTheme === 'light' ||
      storedTheme === 'dark' ||
      storedTheme === 'system'
    ) {
      return storedTheme
    }

    return 'system'
  })

  const [systemTheme, setSystemTheme] =
    useState<'light' | 'dark'>(getSystemTheme)

  const resolvedTheme =
    theme === 'system' ? systemTheme : theme

  useEffect(() => {
    const mediaQuery = window.matchMedia(
      '(prefers-color-scheme: dark)',
    )

    const handleChange = () => {
      setSystemTheme(
        mediaQuery.matches ? 'dark' : 'light',
      )
    }

    mediaQuery.addEventListener(
      'change',
      handleChange,
    )

    return () => {
      mediaQuery.removeEventListener(
        'change',
        handleChange,
      )
    }
  }, [])

  useEffect(() => {
    const root = document.documentElement

    root.classList.toggle(
      'dark',
      resolvedTheme === 'dark',
    )

    root.dataset.theme = resolvedTheme
  }, [resolvedTheme])

  const setTheme = (newTheme: Theme) => {
    localStorage.setItem(
      STORAGE_KEY,
      newTheme,
    )

    setThemeState(newTheme)
  }

  return (
    <ThemeContext.Provider
      value={{
        theme,
        resolvedTheme,
        setTheme,
      }}
    >
      {children}
    </ThemeContext.Provider>
  )
}