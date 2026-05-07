#!/usr/bin/env python3
"""QC progress reporter. Called by cron to send Telegram update."""
import sqlite3, json, urllib.request

DB = '/home/muatasr/.nanobot/workspace/teas-study-app/data/kb/teas_unified.db'
CHAT_ID = '-1003972068284'
THREAD_ID = 220
BOT_TOKEN = '8563031983:AAG0moU-_rQFHb3aldY0m7Owt8FJv_lgXdg'

def get_progress():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    c.execute("SELECT value FROM qc_progress WHERE key='status'")
    status = c.fetchone()[0]
    
    c.execute("SELECT value FROM qc_progress WHERE key='phase1_done'")
    p1_done = int(c.fetchone()[0])
    
    c.execute("SELECT value FROM qc_progress WHERE key='phase1_total'")
    p1_total = int(c.fetchone()[0])
    
    c.execute("SELECT value FROM qc_progress WHERE key='phase2_done'")
    p2_done = int(c.fetchone()[0])
    
    c.execute("SELECT value FROM qc_progress WHERE key='phase2_total'")
    p2_total = int(c.fetchone()[0])
    
    c.execute("SELECT value FROM qc_progress WHERE key='current_batch'")
    batch = c.fetchone()[0]
    
    # Phase 1 failures
    c.execute("SELECT subject, COUNT(*) FROM qc_results WHERE phase1_passed=0 GROUP BY subject")
    p1_fails = c.fetchall()
    
    # Phase 2 low scores
    c.execute("SELECT COUNT(*) FROM qc_results WHERE phase2_done=1 AND phase2_score < 4")
    low_scores = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM qc_results WHERE phase2_done=1 AND phase2_score = 5")
    perfect = c.fetchone()[0]
    
    conn.close()
    return {
        'status': status,
        'p1_done': p1_done, 'p1_total': p1_total,
        'p2_done': p2_done, 'p2_total': p2_total,
        'batch': batch,
        'p1_fails': p1_fails,
        'low_scores': low_scores,
        'perfect': perfect
    }

def send_telegram(text):
    import os
    token = os.environ.get('TELEGRAM_BOT_TOKEN', BOT_TOKEN)
    if not token:
        print('No bot token, skipping Telegram send')
        print(text)
        return
    
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = json.dumps({
        'chat_id': CHAT_ID,
        'message_thread_id': THREAD_ID,
        'text': text,
        'parse_mode': 'Markdown'
    }).encode()
    req = urllib.request.Request(url, data=payload, 
                                  headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f'Telegram error: {e}')

def main():
    p = get_progress()
    
    if p['status'] == 'complete':
        msg = (f"✅ *TEAS QC COMPLETE*\n\n"
               f"Phase 1: {p['p1_done']}/{p['p1_total']} checked\n"
               f"Phase 2: {p['p2_done']} scored\n"
               f"Perfect (5/5): {p['perfect']}\n"
               f"Low score (<4): {p['low_scores']}")
    elif p['status'] == 'idle':
        msg = "⏳ QC system initialized, waiting for master to start..."
    else:
        p1_fail_str = ', '.join(f'{s}:{n}' for s, n in p['p1_fails']) if p['p1_fails'] else 'none'
        pct = (p['p2_done'] / p['p2_total'] * 100) if p['p2_total'] > 0 else 0
        msg = (f"📊 *TEAS QC Progress*\n\n"
               f"Phase 1: {p['p1_done']}/{p['p1_total']} ({p1_fail_str} failures)\n"
               f"Phase 2: {p['p2_done']}/{p['p2_total']} ({pct:.0f}%)\n"
               f"Batch: {p['batch'] or 'none'}\n"
               f"Perfect: {p['perfect']} | Low: {p['low_scores']}")
    
    send_telegram(msg)

if __name__ == '__main__':
    main()
