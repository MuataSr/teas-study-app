# TASK 2 COMPLETION TODO

**DO NOT PROCEED WITHOUT CHECKING OFF EACH ITEM**

---

## TASK A: Resolve 19 remaining messy math questions

- [x] A1. Read each of the 19 questions (Q142-Q175) — determine which are graph/table/image vs text-extractable
- [ ] A2. For graph/table/image questions → mark `status='unusable'` in questions table
- [ ] A3. For text-extractable ones → manually UPDATE clean correct_answer, no LLM needed
- [ ] A4. Verify all 19 handled — query for any remaining score-2 math with messy correct_answer

### A1 Classification:
- **ALREADY CLEAN (5):** Q162 (y=7x+5), Q166 (y=5x), Q172 (T=B+1), Q174 (z=3+y) — ≤25 chars, just flagged by len>25 check incorrectly? No, they're ≤25. Recheck: Q162=6ch, Q166=4ch, Q172=5ch, Q174=5ch. These should have been skipped. The 19 count is wrong — they are NOT messy. Skip them.
- **LONG BUT CORRECT (3):** Q147, Q149, Q175 — text answers that are the full explanation. Trim to core answer.
- **UNUSABLE — graph/table/image (11):** Q142, Q145, Q146, Q151, Q153, Q154, Q155, Q156, Q158, Q161, Q165, Q169

## TASK B: Re-run phase2 QC

- [ ] B1. Find and read the phase2 QC script
- [ ] B2. Verify llama-server is running on port 8082
- [ ] B3. Run phase2 QC with output logged to /tmp/teas_phase2_qc_rerun.log
- [ ] B4. Monitor — confirm it completes without timeout
- [ ] B5. Check log for errors or crashes

## TASK C: Verify final results

- [ ] C1. Query new score distribution — confirm score 0/1/2 math resolved
- [ ] C2. Confirm Q1885 (english) score updated
- [ ] C3. Confirm Q1363, Q1369, Q1374, Q1379 (reading) scores updated
- [ ] C4. Remove recurring cron job (teas-task2-progress)
- [ ] C5. Report final numbers to Mister K
