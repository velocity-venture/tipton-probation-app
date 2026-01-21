'use client'

import { useEffect, useState } from 'react'
import { X, Calendar, Phone, AlertTriangle } from 'lucide-react'
import { supabase, type Probationer, type Appointment } from '@/lib/supabase'

interface CaseDrawerProps {
  probationer: Probationer | null
  isOpen: boolean
  onClose: () => void
}

const riskColors: Record<Probationer['risk_level'], string> = {
  Low: 'bg-risk-low/20 text-risk-low border-risk-low/30',
  Medium: 'bg-risk-medium/20 text-risk-medium border-risk-medium/30',
  High: 'bg-risk-high/20 text-risk-high border-risk-high/30',
  Warrant: 'bg-risk-warrant/20 text-risk-warrant border-risk-warrant/30',
}

const statusColors: Record<Appointment['status'], string> = {
  Scheduled: 'text-primary',
  Completed: 'text-risk-low',
  Missed: 'text-risk-warrant',
  Excused: 'text-text-secondary',
}

export function CaseDrawer({ probationer, isOpen, onClose }: CaseDrawerProps) {
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loadingAppointments, setLoadingAppointments] = useState(false)

  useEffect(() => {
    async function fetchAppointments() {
      if (!probationer) return

      setLoadingAppointments(true)
      try {
        const { data, error } = await supabase
          .from('appointments')
          .select('*')
          .eq('probationer_id', probationer.id)
          .order('scheduled_time', { ascending: false })
          .limit(3)

        if (error) throw error
        setAppointments(data || [])
      } catch (err) {
        console.error('Failed to fetch appointments:', err)
        setAppointments([])
      } finally {
        setLoadingAppointments(false)
      }
    }

    if (isOpen && probationer) {
      fetchAppointments()
    }
  }, [isOpen, probationer])

  if (!isOpen || !probationer) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed right-0 top-0 h-full w-96 bg-surface border-l border-border z-50 shadow-xl overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-surface border-b border-border p-4">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-lg font-semibold text-text-primary">
                {probationer.full_name}
              </h2>
              <p className="text-sm font-mono text-text-secondary mt-0.5">
                {probationer.case_number}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-1 hover:bg-border/50 rounded transition-colors"
            >
              <X className="w-5 h-5 text-text-secondary" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4 space-y-6">
          {/* Status Section */}
          <div className="space-y-3">
            <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider">
              Status
            </h3>
            <div className="flex items-center gap-3">
              <span
                className={`inline-flex items-center px-2.5 py-1 rounded text-sm font-medium border ${riskColors[probationer.risk_level]}`}
              >
                <AlertTriangle className="w-3.5 h-3.5 mr-1.5" />
                {probationer.risk_level} Risk
              </span>
              <span
                className={`inline-flex items-center px-2.5 py-1 rounded text-sm font-medium border ${
                  probationer.is_active
                    ? 'bg-risk-low/20 text-risk-low border-risk-low/30'
                    : 'bg-text-muted/20 text-text-muted border-text-muted/30'
                }`}
              >
                {probationer.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>

          {/* Contact Section */}
          <div className="space-y-3">
            <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider">
              Contact
            </h3>
            <div className="flex items-center gap-2 text-text-secondary">
              <Phone className="w-4 h-4" />
              <span className="text-sm">{probationer.phone_number}</span>
            </div>
          </div>

          {/* Appointments Section */}
          <div className="space-y-3">
            <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider">
              Recent Appointments
            </h3>
            {loadingAppointments ? (
              <p className="text-sm text-text-secondary">Loading...</p>
            ) : appointments.length > 0 ? (
              <div className="space-y-2">
                {appointments.map((apt) => (
                  <div
                    key={apt.id}
                    className="flex items-center justify-between p-3 bg-background rounded border border-border/50"
                  >
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-text-muted" />
                      <span className="text-sm text-text-primary">
                        {new Date(apt.scheduled_time).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                          hour: 'numeric',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>
                    <span className={`text-xs font-medium ${statusColors[apt.status]}`}>
                      {apt.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-secondary">No appointments found</p>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
