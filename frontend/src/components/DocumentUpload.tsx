import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Box, Typography, LinearProgress, TextField, Stack } from '@mui/material'
import { uploadDocument } from '../services/api'
import type { ProcessingResult } from '../services/types'

interface Props {
  onUploaded: (result: ProcessingResult) => void
}

export default function DocumentUpload({ onUploaded }: Props) {
  const [progress, setProgress] = useState<number>(0)
  const [caseId, setCaseId] = useState<string>("")

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (!acceptedFiles.length) return
    setProgress(10)
    try {
      const res = await uploadDocument(acceptedFiles[0], caseId || undefined)
      setProgress(100)
      onUploaded(res)
    } catch (e) {
      console.error(e)
      setProgress(0)
    }
  }, [caseId, onUploaded])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop })

  return (
    <Stack spacing={2}>
      <TextField label="Case ID (optional)" value={caseId} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCaseId(e.target.value)} />
      <Box {...getRootProps()} sx={{ border: '2px dashed #888', p: 4, textAlign: 'center', cursor: 'pointer' }}>
        <input {...getInputProps()} />
        {
          isDragActive ? <Typography>Drop the files here ...</Typography> : <Typography>Drag & drop a document here, or click to select</Typography>
        }
      </Box>
      {progress > 0 && progress < 100 && (<>
        <Typography>Uploading...</Typography>
        <LinearProgress variant="determinate" value={progress} />
      </>)}
    </Stack>
  )
}
