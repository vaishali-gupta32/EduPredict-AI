import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useMutation } from '@tanstack/react-query'
import { Upload, FileText, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import client from '../api/client'

export default function UploadPage() {
    const [result, setResult] = useState(null)

    const mutation = useMutation({
        mutationFn: async (file) => {
            const formData = new FormData()
            formData.append('file', file)
            const { data } = await client.post('/upload/csv', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            })
            return data
        },
        onSuccess: (data) => setResult({ type: 'success', data }),
        onError: (err) => {
            const backendDetail = err.response?.data?.detail
            const msg = typeof backendDetail === 'object' ? backendDetail.message : backendDetail
            setResult({ type: 'error', message: msg || err.message })
        },
    })

    const onDrop = useCallback((acceptedFiles) => {
        if (acceptedFiles.length === 0) return
        setResult(null)
        mutation.mutate(acceptedFiles[0])
    }, [mutation])

    const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
        onDrop,
        accept: { 'text/csv': ['.csv'] },
        maxFiles: 1,
        disabled: mutation.isPending,
    })

    return (
        <div className="space-y-6 max-w-2xl mx-auto">
            <div>
                <h1 className="text-2xl font-bold text-slate-100">Upload Student Data</h1>
                <p className="text-slate-400 text-sm mt-1">Upload a CSV file with student records to generate batch predictions</p>
            </div>

            {/* Schema reference */}
            <div className="card bg-indigo-950/40 border-indigo-800/40">
                <h3 className="text-sm font-semibold text-indigo-300 mb-2">Required CSV Columns</h3>
                <p className="text-xs text-slate-400 font-mono leading-relaxed">
                    student_id, age, gender, department, semester, attendance_pct,
                    assignment_score_avg, internal_marks_avg, semester_gpa,
                    study_hours_per_week, participation_score, prev_semester_gpa,
                    backlogs, financial_aid
                </p>
            </div>

            {/* Dropzone */}
            <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200 ${isDragActive
                    ? 'border-indigo-400 bg-indigo-500/10'
                    : 'border-slate-700 bg-slate-900 hover:border-indigo-600 hover:bg-slate-800/50'
                    } ${mutation.isPending ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
                <input {...getInputProps()} />
                <Upload size={40} className={`mx-auto mb-3 ${isDragActive ? 'text-indigo-400' : 'text-slate-500'}`} />
                {mutation.isPending ? (
                    <div>
                        <p className="text-slate-300 font-medium">Processing...</p>
                        <p className="text-slate-500 text-sm mt-1">Running predictions. Please wait.</p>
                        <div className="mt-3 w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
                    </div>
                ) : isDragActive ? (
                    <p className="text-indigo-400 font-medium">Drop the CSV file here</p>
                ) : (
                    <div>
                        <p className="text-slate-300 font-medium">Drag & drop your CSV file here</p>
                        <p className="text-slate-500 text-sm mt-1">or click to browse files</p>
                        <p className="text-slate-600 text-xs mt-2">Only .csv files accepted</p>
                    </div>
                )}
            </div>

            {/* Accepted file name */}
            {acceptedFiles.length > 0 && !mutation.isPending && (
                <div className="flex items-center gap-2 text-slate-300 text-sm bg-slate-800 rounded-lg px-4 py-2.5">
                    <FileText size={16} className="text-indigo-400" />
                    <span>{acceptedFiles[0].name}</span>
                    <span className="text-slate-500 ml-auto">{(acceptedFiles[0].size / 1024).toFixed(1)} KB</span>
                </div>
            )}

            {/* Result */}
            {result?.type === 'success' && (
                <div className="card border-emerald-800/40 bg-emerald-950/20">
                    <div className="flex items-center gap-2 mb-4">
                        <CheckCircle size={20} className="text-emerald-400" />
                        <h3 className="font-semibold text-emerald-400">Upload Successful</h3>
                    </div>
                    <div className="grid grid-cols-3 gap-4 mb-4">
                        {[
                            ['Total Rows', result.data.total_rows],
                            ['Processed', result.data.processed_rows],
                            ['Errors', result.data.error_rows],
                        ].map(([label, val]) => (
                            <div key={label} className="text-center bg-slate-800/50 rounded-xl p-3">
                                <p className="text-2xl font-bold text-slate-100">{val}</p>
                                <p className="text-xs text-slate-500">{label}</p>
                            </div>
                        ))}
                    </div>
                    <p className="text-xs text-slate-500">Batch ID: <span className="font-mono">{result.data.batch_id}</span></p>

                    {result.data.errors?.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-slate-800">
                            <p className="text-sm font-medium text-amber-400 mb-2 flex items-center gap-1"><AlertTriangle size={14} /> Row Errors</p>
                            <div className="max-h-40 overflow-y-auto space-y-1">
                                {result.data.errors.map((e, i) => (
                                    <p key={i} className="text-xs text-slate-400 font-mono bg-slate-800 px-2 py-1 rounded">
                                        Row {e.row}: {e.error}
                                    </p>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {result?.type === 'error' && (
                <div className="card border-red-800/40 bg-red-950/20">
                    <div className="flex items-center gap-2">
                        <XCircle size={20} className="text-red-400" />
                        <h3 className="font-semibold text-red-400">Upload Failed</h3>
                    </div>
                    <p className="text-slate-300 text-sm mt-2">{result.message}</p>
                </div>
            )}
        </div>
    )
}
