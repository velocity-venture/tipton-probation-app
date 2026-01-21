'use client'

import { useState } from 'react'
import { Shield } from 'lucide-react'
import { ProbationerGrid } from '@/components/ProbationerGrid'
import { CaseDrawer } from '@/components/CaseDrawer'
import type { Probationer } from '@/lib/supabase'

export default function Home() {
  const [selectedProbationer, setSelectedProbationer] = useState<Probationer | null>(null)
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)

  const handleRowClick = (probationer: Probationer) => {
    setSelectedProbationer(probationer)
    setIsDrawerOpen(true)
  }

  const handleCloseDrawer = () => {
    setIsDrawerOpen(false)
  }

  return (
    <main className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-surface/50 backdrop-blur-sm sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-3">
              <Shield className="w-6 h-6 text-primary" />
              <h1 className="text-lg font-semibold text-text-primary">
                Probation Command Center
              </h1>
            </div>
            <div className="text-sm text-text-secondary">
              Tipton County
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="mb-4">
          <h2 className="text-sm font-medium text-text-muted uppercase tracking-wider">
            Active Caseload
          </h2>
        </div>

        <div className="bg-surface rounded-lg border border-border overflow-hidden">
          <ProbationerGrid onRowClick={handleRowClick} />
        </div>
      </div>

      {/* Drawer */}
      <CaseDrawer
        probationer={selectedProbationer}
        isOpen={isDrawerOpen}
        onClose={handleCloseDrawer}
      />
    </main>
  )
}
