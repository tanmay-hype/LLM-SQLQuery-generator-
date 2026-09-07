import { useState } from 'react'

import AppShell from './components/layout/AppShell'
import ConnectDatabaseDialog from './components/database/ConnectDatabaseDialog'
import QueryWorkspace from './components/query/QueryWorkspace'

function App() {
  const [
    isConnectDialogOpen,
    setIsConnectDialogOpen,
  ] = useState(false)

  return (
    <>
      <AppShell
        onConnectDatabase={() =>
          setIsConnectDialogOpen(true)
        }
      >
        <QueryWorkspace />
      </AppShell>

      <ConnectDatabaseDialog
        open={isConnectDialogOpen}
        onClose={() =>
          setIsConnectDialogOpen(false)
        }
      />
    </>
  )
}

export default App