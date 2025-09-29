import axios from 'axios'
import type { ProcessingResult, CalendarEventOut, CalendarEventCreate, DocumentListItem } from './types'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
export const api = axios.create({ baseURL })

export async function uploadDocument(file: File, caseId?: string): Promise<ProcessingResult> {
  const form = new FormData()
  form.append('file', file)
  if (caseId) form.append('case_id', caseId)
  const { data } = await api.post<ProcessingResult>('/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function getStatus(documentId: string): Promise<{ document_id: string; status: string }> {
  const { data } = await api.get(`/documents/${documentId}/status`)
  return data
}

export async function getResult(documentId: string): Promise<ProcessingResult> {
  const { data } = await api.get<ProcessingResult>(`/documents/${documentId}/result`)
  return data
}

export async function getCaseCalendar(caseId: string): Promise<CalendarEventOut[]> {
  const { data } = await api.get<CalendarEventOut[]>(`/cases/${caseId}/calendar`)
  return data
}

export async function createCalendarEvent(caseId: string, payload: CalendarEventCreate): Promise<CalendarEventOut> {
  const { data } = await api.post<CalendarEventOut>(`/cases/${caseId}/calendar/events`, payload)
  return data
}

export async function listDocuments(params?: { case_id?: string; limit?: number; offset?: number }): Promise<DocumentListItem[]> {
  const { data } = await api.get<DocumentListItem[]>(`/documents`, { params })
  return data
}
