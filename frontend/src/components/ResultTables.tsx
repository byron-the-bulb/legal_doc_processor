import React from 'react'
import { Box, Chip, Divider, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material'
import type { DocumentClassification, ExtractedDate, LegalObligation } from '../services/types'

interface Props {
  classification: DocumentClassification
  dates: ExtractedDate[]
  obligations: LegalObligation[]
}

export default function ResultTables({ classification, dates, obligations }: Props) {
  return (
    <Stack spacing={2}>
      <Box>
        <Typography variant="subtitle1" gutterBottom>Classification</Typography>
        <Stack direction="row" spacing={2} flexWrap="wrap">
          <Chip label={`Type: ${classification.document_type}`} />
          <Chip label={`Confidence: ${(classification.confidence_score * 100).toFixed(0)}%`} />
          {classification.sub_type && <Chip label={`Subtype: ${classification.sub_type}`} />}
          {classification.jurisdiction && <Chip label={`Jurisdiction: ${classification.jurisdiction}`} />}
          {classification.parties_involved?.length ? (
            <Chip label={`Parties: ${classification.parties_involved.join(', ').slice(0, 80)}${classification.parties_involved.join(', ').length > 80 ? '…' : ''}`} />
          ) : null}
        </Stack>
      </Box>

      <Divider />

      <Box>
        <Typography variant="subtitle1" gutterBottom>Extracted Dates</Typography>
        {dates.length === 0 ? (
          <Typography variant="body2" color="text.secondary">None</Typography>
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Confidence</TableCell>
                <TableCell>Source</TableCell>
                <TableCell>Jurisdiction</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {dates.map((d, idx) => (
                <TableRow key={idx}>
                  <TableCell>{new Date(d.date).toLocaleString()}</TableCell>
                  <TableCell>{d.date_type}</TableCell>
                  <TableCell>{(d.confidence_score * 100).toFixed(0)}%</TableCell>
                  <TableCell>{d.source_text}</TableCell>
                  <TableCell>{d.jurisdiction || '-'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Box>

      <Divider />

      <Box>
        <Typography variant="subtitle1" gutterBottom>Obligations</Typography>
        {obligations.length === 0 ? (
          <Typography variant="body2" color="text.secondary">None</Typography>
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Description</TableCell>
                <TableCell>Due Date</TableCell>
                <TableCell>Responsible</TableCell>
                <TableCell>Priority</TableCell>
                <TableCell>Source Doc</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {obligations.map((o, idx) => (
                <TableRow key={idx}>
                  <TableCell>{o.description}</TableCell>
                  <TableCell>{new Date(o.due_date).toLocaleString()}</TableCell>
                  <TableCell>{o.responsible_party}</TableCell>
                  <TableCell>{o.priority_level}</TableCell>
                  <TableCell>{o.source_document}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Box>
    </Stack>
  )
}
