'use client'

import { useEffect, useState } from 'react'
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from '@tanstack/react-table'
import { supabase, type Probationer } from '@/lib/supabase'

const columnHelper = createColumnHelper<Probationer>()

const riskColors: Record<Probationer['risk_level'], string> = {
  Low: 'bg-risk-low/20 text-risk-low border-risk-low/30',
  Medium: 'bg-risk-medium/20 text-risk-medium border-risk-medium/30',
  High: 'bg-risk-high/20 text-risk-high border-risk-high/30',
  Warrant: 'bg-risk-warrant/20 text-risk-warrant border-risk-warrant/30',
}

const columns = [
  columnHelper.accessor('case_number', {
    header: 'Case #',
    cell: (info) => (
      <span className="font-mono text-sm text-text-secondary">
        {info.getValue()}
      </span>
    ),
  }),
  columnHelper.accessor('full_name', {
    header: 'Name',
    cell: (info) => (
      <span className="font-medium text-text-primary">{info.getValue()}</span>
    ),
  }),
  columnHelper.accessor('phone_number', {
    header: 'Phone',
    cell: (info) => (
      <span className="text-sm text-text-secondary">{info.getValue()}</span>
    ),
  }),
  columnHelper.accessor('risk_level', {
    header: 'Risk',
    cell: (info) => {
      const level = info.getValue()
      return (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${riskColors[level]}`}
        >
          {level}
        </span>
      )
    },
  }),
]

interface ProbationerGridProps {
  onRowClick: (probationer: Probationer) => void
}

export function ProbationerGrid({ onRowClick }: ProbationerGridProps) {
  const [data, setData] = useState<Probationer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchProbationers() {
      try {
        const { data: probationers, error } = await supabase
          .from('probationers')
          .select('*')
          .eq('is_active', true)
          .order('case_number', { ascending: true })

        if (error) throw error
        setData(probationers || [])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data')
      } finally {
        setLoading(false)
      }
    }

    fetchProbationers()
  }, [])

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-text-secondary">
        Loading...
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-risk-warrant">
        Error: {error}
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id} className="border-b border-border">
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className="h-8 px-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider"
                >
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              onClick={() => onRowClick(row.original)}
              className="h-10 border-b border-border/50 hover:bg-surface cursor-pointer transition-colors"
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-3">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.length === 0 && (
        <div className="flex items-center justify-center h-32 text-text-secondary">
          No probationers found
        </div>
      )}
    </div>
  )
}
