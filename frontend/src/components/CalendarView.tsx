import React from 'react'
import { Calendar, dateFnsLocalizer, View, Event as RBCEvent } from 'react-big-calendar'
import 'react-big-calendar/lib/css/react-big-calendar.css'
import { format, parse, startOfWeek, getDay } from 'date-fns'
import { enUS } from 'date-fns/locale'
import type { CalendarEventOut } from '../services/types'

const locales = { 'en-US': enUS }
const localizer = dateFnsLocalizer({ format, parse, startOfWeek: () => startOfWeek(new Date(), { weekStartsOn: 1 }), getDay, locales })

interface Props {
  events: CalendarEventOut[]
}

export default function CalendarView({ events }: Props) {
  const mapped: RBCEvent[] = events.map(e => ({
    title: e.title,
    start: new Date(e.start),
    end: new Date(e.end),
    allDay: e.all_day,
    resource: e
  }))

  return (
    <div style={{ height: 600 }}>
      <Calendar
        localizer={localizer}
        events={mapped}
        startAccessor="start"
        endAccessor="end"
        defaultView={"month" as View}
      />
    </div>
  )
}
