import React, { useState } from 'react'
import { AppBar, Toolbar, Typography, Button, Container, Stack } from '@mui/material'
import Dashboard from './pages/Dashboard'
import History from './pages/History'
import CaseManager from './pages/CaseManager'
import DocumentProcessor from './pages/DocumentProcessor'

 type Page = 'dashboard' | 'case' | 'processor' | 'history'

export default function App() {
  const [page, setPage] = useState<Page>('dashboard')

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>Legal Document Processor</Typography>
          <Stack direction="row" spacing={1}>
            <Button color="inherit" onClick={() => setPage('dashboard')}>Dashboard</Button>
            <Button color="inherit" onClick={() => setPage('case')}>Case Manager</Button>
            <Button color="inherit" onClick={() => setPage('processor')}>Process Documents</Button>
            <Button color="inherit" onClick={() => setPage('history')}>History</Button>
          </Stack>
        </Toolbar>
      </AppBar>
      <Container sx={{ mt: 3 }}>
        {page === 'dashboard' && <Dashboard />}
        {page === 'case' && <CaseManager />}
        {page === 'processor' && <DocumentProcessor />}
        {page === 'history' && <History />}
      </Container>
    </>
  )
}
