import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export type Probationer = {
  id: string
  case_number: string
  full_name: string
  risk_level: 'Low' | 'Medium' | 'High' | 'Warrant'
  phone_number: string
  is_active: boolean
}

export type Appointment = {
  id: string
  probationer_id: string
  scheduled_time: string
  status: 'Scheduled' | 'Completed' | 'Missed' | 'Excused'
}
