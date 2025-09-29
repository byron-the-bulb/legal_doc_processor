import React, { useEffect, useState } from 'react'
import { Paper, TextField, Stack, Button } from '@mui/material'
import { getCaseCalendar, createCalendarEvent } from '../services/api'
import type { CalendarEventOut } from '../services/types'
import CalendarView from '../components/CalendarView'

export default function CaseManager() {
  const [caseId, setCaseId] = useState<string>('test-case')
  const [events, setEvents] = useState<CalendarEventOut[]>([])
  const [title, setTitle] = useState('')
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')

  async function refresh() {
    if (!caseId) return
    const e = await getCaseCalendar(caseId)
    setEvents(e)
  }

  useEffect(() => { refresh() }, [caseId])

  async function addEvent() {
    if (!caseId || !title || !start || !end) return
    await createCalendarEvent(caseId, { title, start, end, all_day: false })
    setTitle(''); setStart(''); setEnd('')
    await refresh()
  }

  return (
    <Stack spacing={2}>
      <Paper sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField label="Case ID" value={caseId} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCaseId(e.target.value)} />
          <Button variant="contained" onClick={refresh}>Refresh</Button>
        </Stack>
      </Paper>
      <CalendarView events={events} />
      <Paper sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField label="Title" value={title} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTitle(e.target.value)} />
          <TextField label="Start (ISO)" value={start} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setStart(e.target.value)} />
          <TextField label="End (ISO)" value={end} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEnd(e.target.value)} />
          <Button variant="contained" onClick={addEvent}>Add Event</Button>
        </Stack>
      </Paper>
    </Stack>
  )
}
