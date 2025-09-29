import React from 'react'
import { Typography, Paper, Box } from '@mui/material'

export default function Dashboard() {
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>Welcome</Typography>
      <Typography>
        This dashboard will summarize processing throughput, accuracy, and escalations.
        Use the Case Manager to view calendars, and Process Documents to upload and extract.
      </Typography>
      <Box sx={{ mt: 2 }}>
        <Typography variant="body2">(Charts placeholder)</Typography>
      </Box>
    </Paper>
  )
}
