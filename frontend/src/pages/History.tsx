import React, { useEffect, useState, useMemo } from 'react'
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  Chip,
  Divider,
  IconButton,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import RefreshIcon from '@mui/icons-material/Refresh'
import type { DocumentListItem } from '../services/types'
import { listDocuments } from '../services/api'
import ResultTables from '../components/ResultTables'

export default function History() {
  const [docs, setDocs] = useState<DocumentListItem[]>([])
  const [loading, setLoading] = useState(false)
  const [caseId, setCaseId] = useState('')

  const fetchDocs = async () => {
    setLoading(true)
    try {
      const items = await listDocuments({ case_id: caseId || undefined, limit: 100 })
      setDocs(items)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocs()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const headerChips = useMemo(() => (
    <Stack direction="row" spacing={1} flexWrap="wrap">
      <Chip label={`Total: ${docs.length}`} />
      {caseId && <Chip label={`Case: ${caseId}`} />}
    </Stack>
  ), [docs.length, caseId])

  return (
    <Paper sx={{ p: 2 }}>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="center" justifyContent="space-between">
        <Typography variant="h6">Upload History</Typography>
        {headerChips}
      </Stack>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="center" sx={{ mt: 2 }}>
        <TextField size="small" label="Filter by Case ID" value={caseId} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCaseId(e.target.value)} />
        <Button variant="contained" startIcon={<RefreshIcon />} onClick={fetchDocs} disabled={loading}>
          Refresh
        </Button>
      </Stack>

      <Box sx={{ mt: 2 }}>
        {docs.length === 0 ? (
          <Typography variant="body2" color="text.secondary">No documents found.</Typography>
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Created</TableCell>
                <TableCell>Filename</TableCell>
                <TableCell>Case</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Confidence</TableCell>
                <TableCell>Human Review</TableCell>
                <TableCell>Errors</TableCell>
                <TableCell>Details</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {docs.map((d) => (
                <TableRow key={d.document_id}>
                  <TableCell>{new Date(d.created_at).toLocaleString()}</TableCell>
                  <TableCell>{d.filename}</TableCell>
                  <TableCell>{d.case_id || '-'}</TableCell>
                  <TableCell>{d.processing_status}</TableCell>
                  <TableCell>{d.classification.document_type}</TableCell>
                  <TableCell>{(d.classification.confidence_score * 100).toFixed(0)}%</TableCell>
                  <TableCell>{d.human_review_required ? 'Yes' : 'No'}</TableCell>
                  <TableCell>{d.error_messages?.length ? d.error_messages.join(', ') : '-'}</TableCell>
                  <TableCell>
                    <Accordion sx={{ boxShadow: 'none' }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="body2">View</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Typography variant="subtitle2">JSON</Typography>
                        <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(d, null, 2)}</pre>
                        <Divider sx={{ my: 2 }} />
                        <ResultTables classification={d.classification} dates={d.extracted_dates} obligations={d.obligations} />
                      </AccordionDetails>
                    </Accordion>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Box>
    </Paper>
  )
}
