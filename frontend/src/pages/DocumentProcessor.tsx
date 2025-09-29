import React, { useState } from 'react'
import { Paper, Typography, Divider } from '@mui/material'
import DocumentUpload from '../components/DocumentUpload'
import ProcessingStatus from '../components/ProcessingStatus'
import HumanReview from '../components/HumanReview'
import type { ProcessingResult } from '../services/types'
import ResultTables from '../components/ResultTables'

export default function DocumentProcessor() {
  const [result, setResult] = useState<ProcessingResult | null>(null)
  const [docId, setDocId] = useState<string | null>(null)

  return (
    <>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>Upload Document</Typography>
        <DocumentUpload onUploaded={(res) => { setDocId(res.document_id); setResult(null) }} />
      </Paper>
      {docId && !result && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <ProcessingStatus documentId={docId} onComplete={setResult} />
        </Paper>
      )}
      {result && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6">Processing Result</Typography>
          <Divider sx={{ my: 2 }} />
          <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(result, null, 2)}</pre>
          <Divider sx={{ my: 2 }} />
          <ResultTables classification={result.classification} dates={result.extracted_dates} obligations={result.obligations} />
          <Divider sx={{ my: 2 }} />
          <HumanReview result={result} />
        </Paper>
      )}
    </>
  )
}
