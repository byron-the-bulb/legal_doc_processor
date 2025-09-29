import React from 'react'
import { Alert, List, ListItem, ListItemText, Typography } from '@mui/material'
import type { ProcessingResult } from '../services/types'

interface Props { result: ProcessingResult }

export default function HumanReview({ result }: Props) {
  if (!result.human_review_required) return null
  return (
    <>
      <Alert severity="warning" sx={{ mb: 2 }}>Human review required</Alert>
      <Typography variant="h6">Review Prompts</Typography>
      <List>
        {result.error_messages.map((m, i) => (
          <ListItem key={i}><ListItemText primary={m} /></ListItem>
        ))}
      </List>
    </>
  )
}
