import React, { useEffect, useState } from 'react'
import { Alert, CircularProgress, Stack, Typography } from '@mui/material'
import { getStatus, getResult } from '../services/api'
import type { ProcessingResult } from '../services/types'

interface Props {
  documentId: string
  onComplete?: (result: ProcessingResult) => void
}

export default function ProcessingStatus({ documentId, onComplete }: Props) {
  const [status, setStatus] = useState<string>('queued')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    const timer = setInterval(async () => {
      try {
        const s = await getStatus(documentId)
        if (!mounted) return
        setStatus(s.status)
        if (['completed', 'needs_review', 'failed'].includes(s.status)) {
          clearInterval(timer)
          const result = await getResult(documentId)
          onComplete && onComplete(result)
        }
      } catch (e: any) {
        if (!mounted) return
        setError(e?.response?.data?.detail || 'Error checking status')
      }
    }, 2000)
    return () => { mounted = false; clearInterval(timer) }
  }, [documentId, onComplete])

  if (error) return <Alert severity="error">{error}</Alert>

  return (
    <Stack direction="row" spacing={2} alignItems="center">
      <CircularProgress size={20} />
      <Typography>Processing status: {status}</Typography>
    </Stack>
  )
}
