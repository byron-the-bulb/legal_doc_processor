export interface ExtractedDate {
  date: string
  date_type: string
  confidence_score: number
  source_text: string
  jurisdiction?: string | null
}

export interface LegalObligation {
  description: string
  due_date: string
  responsible_party: string
  priority_level: string
  associated_case: string
  source_document: string
}

export interface DocumentClassification {
  document_type: string
  confidence_score: number
  sub_type?: string | null
  jurisdiction?: string | null
  parties_involved: string[]
}

export interface ProcessingResult {
  document_id: string
  classification: DocumentClassification
  extracted_dates: ExtractedDate[]
  obligations: LegalObligation[]
  processing_status: string
  human_review_required: boolean
  error_messages: string[]
}

export interface CalendarEventOut {
  id: string
  case_id: string
  title: string
  description?: string | null
  start: string
  end: string
  all_day: boolean
  source_document?: string | null
}

export interface CalendarEventCreate {
  title: string
  description?: string | null
  start: string
  end: string
  all_day?: boolean
  source_document?: string | null
}

export interface DocumentListItem {
  document_id: string
  filename: string
  case_id?: string | null
  created_at: string
  processing_status: string
  classification: DocumentClassification
  extracted_dates: ExtractedDate[]
  obligations: LegalObligation[]
  human_review_required: boolean
  error_messages: string[]
}
