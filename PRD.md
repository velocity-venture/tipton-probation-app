# PRD: Tipton County Probation Voice Agent (Phase II)

## Overview

A 24/7 Python-based voice agent that allows probationers to check appointments, schedule reporting dates, and get payment information via phone. The agent identifies callers by their registered phone number and interacts with the Supabase database.

---

## Office Schedule Rules

### Regular Hours
| Day | Availability | Notes |
|-----|--------------|-------|
| Monday | 8:00 AM - 5:00 PM | Walk-in appointments (last appt 4:30 PM) |
| Tuesday | CLOSED to walk-ins | Court obligations |
| Wednesday | 8:00 AM - 5:00 PM | Walk-in appointments (last appt 4:30 PM) |
| Thursday | CLOSED to walk-ins | Court obligations |
| Friday | Phone Reporting Only | Reserved for phone check-ins |

### After-Hours Appointments
- **When:** 1st and 3rd Thursday of each month
- **Time:** 5:00 PM - 7:30 PM only
- **Rule:** Anyone who does not report during after-hours must report Monday or Wednesday during regular business hours

### Lunch Lockout (Monday & Wednesday only)
- **Lunch Break:** 12:00 PM - 1:00 PM (office closed)
- **Cutoff:** Must report by 11:30 AM to be seen before lunch
- **Agent Behavior:** WARN the caller (do not refuse scheduling)
- **Script:** "Please note the office closes for lunch from 12 PM to 1 PM. To be seen before lunch, you must arrive by 11:30 AM."

---

## Caller Identification

1. Agent answers and greets caller
2. Lookup caller by `phone_number` in `probationers` table
3. If found: Greet by name, proceed with options
4. If NOT found: Friendly error message, provide office number

```
Phone Number → probationers.phone_number → probationer record
```

---

## Core Agent Capabilities

### 1. Check Next Appointment
- Query `appointments` table where `probationer_id` matches and `status = 'Scheduled'`
- Return the next `scheduled_time` to the caller
- If no upcoming appointment: Inform caller and offer to schedule

### 2. Schedule New Appointment
- Only allow scheduling for **Monday or Wednesday** (regular hours)
- Validate against lunch lockout rules
- Validate last appointment slot is 4:30 PM
- Create new record in `appointments` with `status = 'Scheduled'`

### 3. Handle Missed Appointments
- If caller has `status = 'Missed'` on a past appointment:
  - Still allow scheduling (no officer approval required)
  - Must be seen **Monday or Wednesday before end of month**
  - Agent script: "I see you have a missed appointment. You can reschedule for any Monday or Wednesday before the end of this month."

### 4. Payment Inquiries
- **Policy:** Cash only, paid at time of appointment
- **Not required:** Clients are NOT required to have payment to be seen
- **Agent script:** "Payments are cash only and collected at the time of your appointment. However, you are not required to have payment in order to be seen."

### 5. Friday Phone Reporting
- If caller is checking in on Friday:
  - Mark appointment as `Completed` (if one exists for that day)
  - Or log the phone check-in appropriately
- Agent script: "Fridays are reserved for phone reporting. I'm marking your check-in as complete."

---

## After-Hours Logic

Since the agent operates 24/7, it must be time-aware:

| Scenario | Agent Behavior |
|----------|----------------|
| Caller at 2 AM on Tuesday | Accept call, but inform: "Walk-in appointments are only available Monday and Wednesday. Would you like to schedule?" |
| Caller on 1st Thursday at 6 PM | Allow scheduling for that evening's after-hours window |
| Caller on 2nd Thursday at 6 PM | Inform: "After-hours appointments are only available on the 1st and 3rd Thursday. The next available is [date]." |

---

## Error Handling & Escalation

### Tone
- **Style:** Friendly but firm
- **Fallback:** Always provide office phone number

### Escalation Triggers
1. Caller explicitly says: "I want to speak to a human"
2. Agent detects frustration (repeated errors, raised voice patterns, explicit frustration)
3. Caller's issue cannot be resolved by the agent

### Escalation Script
```
"I understand this is frustrating. Let me connect you with a probation officer.
You can reach our office at [OFFICE_PHONE_PLACEHOLDER].
Office hours are Monday and Wednesday, 8 AM to 5 PM.
If you'd prefer, you can also call back during those hours for direct assistance."
```

### Error Script (Record Not Found)
```
"I'm sorry, I wasn't able to find your record with this phone number.
Please call our office directly at [OFFICE_PHONE_PLACEHOLDER] for assistance.
Our hours are Monday and Wednesday, 8 AM to 5 PM."
```

---

## Database Interactions

### Tables Used
| Table | Operations |
|-------|------------|
| `probationers` | READ (lookup by phone_number) |
| `appointments` | READ, CREATE, UPDATE (status changes) |

### Key Queries

**Lookup Caller:**
```sql
SELECT * FROM probationers WHERE phone_number = :caller_phone AND is_active = true
```

**Get Next Appointment:**
```sql
SELECT * FROM appointments
WHERE probationer_id = :id AND status = 'Scheduled'
ORDER BY scheduled_time ASC LIMIT 1
```

**Check Missed Appointments:**
```sql
SELECT * FROM appointments
WHERE probationer_id = :id AND status = 'Missed'
```

**Schedule Appointment:**
```sql
INSERT INTO appointments (id, probationer_id, scheduled_time, status)
VALUES (gen_random_uuid(), :id, :datetime, 'Scheduled')
```

**Complete Appointment (Phone Reporting):**
```sql
UPDATE appointments SET status = 'Completed'
WHERE id = :appt_id
```

---

## Validation Rules Summary

| Rule | Condition | Agent Response |
|------|-----------|----------------|
| Lunch Lockout | Appt time 11:31 AM - 12:59 PM on Mon/Wed | Warn: "Office closed 12-1 PM, arrive by 11:30 AM" |
| Last Appointment | Appt time after 4:30 PM | "The last appointment slot is 4:30 PM" |
| Tuesday/Thursday | Any walk-in request | "Walk-ins not available Tue/Thu due to court. Try Mon/Wed" |
| After-Hours | Not 1st or 3rd Thursday | "After-hours only on 1st & 3rd Thursday, 5-7:30 PM" |
| Friday | Walk-in request | "Fridays are for phone reporting only" |

---

## Configuration Placeholders

```yaml
OFFICE_PHONE: "[OFFICE_PHONE_PLACEHOLDER]"
OFFICE_HOURS_START: "08:00"
OFFICE_HOURS_END: "17:00"
LAST_APPOINTMENT_SLOT: "16:30"
LUNCH_START: "12:00"
LUNCH_END: "13:00"
LUNCH_CUTOFF: "11:30"
AFTER_HOURS_START: "17:00"
AFTER_HOURS_END: "19:30"
TIMEZONE: "America/Chicago"  # Confirm timezone
```

---

## Success Metrics

1. **Call Completion Rate:** % of calls resolved without escalation
2. **Scheduling Accuracy:** Appointments created within valid time slots
3. **Caller Satisfaction:** Escalation rate due to frustration (target: < 10%)

---

## Open Questions

- [ ] Confirm timezone (assumed Central Time)
- [ ] Provide office phone number for escalation
- [ ] Define callback hours message for escalation script
- [ ] Should the agent send SMS confirmation after scheduling?
- [ ] Integration with voice platform (Twilio, Vapi, etc.)?

---

*Generated by Claude Code - Planning Phase*
