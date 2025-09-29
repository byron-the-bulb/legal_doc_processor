import { configureStore, createSlice, PayloadAction } from '@reduxjs/toolkit'

interface ProcessingState {
  documentId: string | null
  status: string | null
}

const initialState: ProcessingState = {
  documentId: null,
  status: null,
}

const processingSlice = createSlice({
  name: 'processing',
  initialState,
  reducers: {
    setDocumentId(state, action: PayloadAction<string | null>) { state.documentId = action.payload },
    setStatus(state, action: PayloadAction<string | null>) { state.status = action.payload },
  }
})

export const { setDocumentId, setStatus } = processingSlice.actions

export const store = configureStore({
  reducer: { processing: processingSlice.reducer }
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
