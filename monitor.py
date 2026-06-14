"""
PC Login Monitor
Auto-detects your Gmail from Chrome — just generate a quick security code and go.
"""

import sys, os, json, threading, time, winreg, winsound, ctypes, socket, ssl, smtplib, glob, subprocess
import tkinter as tk
from tkinter import messagebox
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
from pathlib import Path
import webbrowser

# ════════════════════════════════════════════════════════
#  PATHS & CONFIG
# ════════════════════════════════════════════════════════
APP_DIR = Path(os.environ['APPDATA']) / 'PCLoginMonitor'
CFG_F   = APP_DIR / 'config.json'
LOG_F   = APP_DIR / 'log.txt'
PC_NAME = os.environ.get('COMPUTERNAME', socket.gethostname())

def cfg_load():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        return {**{'gmail':'','appcode':'','ready':False},
                **json.loads(CFG_F.read_text())}
    except:
        return {'gmail':'','appcode':'','ready':False}

def cfg_save(d):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CFG_F.write_text(json.dumps(d, indent=2))

def log(msg):
    t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with open(LOG_F, 'a', encoding='utf-8') as f:
            f.write(f'[{t}] {msg}\n')
    except: pass
    print(f'[{t}] {msg}')

# ════════════════════════════════════════════════════════
#  DETECT GMAIL FROM CHROME  (auto-fills the email field)
# ════════════════════════════════════════════════════════
def detect_chrome_gmail():
    chrome_dir = Path(os.environ.get('LOCALAPPDATA','')) / 'Google' / 'Chrome' / 'User Data'
    for pref in glob.glob(str(chrome_dir / '*/Preferences')):
        try:
            data = json.loads(open(pref, encoding='utf-8', errors='ignore').read())
            for acc in data.get('account_info', []):
                email = acc.get('email','')
                if '@gmail.com' in email.lower() or '@googlemail.com' in email.lower():
                    return email
        except: pass
    return ''

# ════════════════════════════════════════════════════════
#  ADMIN ELEVATION
# ════════════════════════════════════════════════════════
def is_admin():
    try: return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except: return False

def elevate():
    ctypes.windll.shell32.ShellExecuteW(
        None, 'runas', sys.executable,
        f'"{os.path.abspath(__file__)}"', None, 1)
    sys.exit(0)

# ════════════════════════════════════════════════════════
#  EMAIL  (Gmail SMTP)
# ════════════════════════════════════════════════════════
def _smtp_send(gmail, code, subject, html, photo_bytes=None):
    msg = MIMEMultipart('related')
    msg['Subject'] = subject
    msg['From']    = gmail
    msg['To']      = gmail
    alt = MIMEMultipart('alternative')
    msg.attach(alt)
    alt.attach(MIMEText(html, 'html'))
    if photo_bytes:
        img = MIMEImage(photo_bytes, 'jpeg')
        img.add_header('Content-ID', '<photo>')
        img.add_header('Content-Disposition', 'inline', filename='intruder.jpg')
        msg.attach(img)
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ctx, timeout=15) as s:
        s.login(gmail, code)
        s.sendmail(gmail, gmail, msg.as_string())

def send_email(subject, html, photo_bytes=None):
    cfg = cfg_load()
    if not cfg.get('ready'): return
    try:
        _smtp_send(cfg['gmail'], cfg['appcode'], subject, html, photo_bytes)
        log(f'Email sent: {subject}')
    except Exception as e:
        log(f'Email error: {e}')

def email_login(user):
    now  = datetime.now().strftime('%A, %B %d %Y   %I:%M %p')
    html = f"""<html><body style="margin:0;background:#0d1117;font-family:'Segoe UI',Arial">
<div style="max-width:460px;margin:36px auto;border-radius:10px;overflow:hidden;box-shadow:0 4px 24px #000">
  <div style="background:linear-gradient(135deg,#1565C0,#0D47A1);padding:30px;text-align:center">
    <div style="font-size:56px">🔐</div>
    <h1 style="color:#fff;margin:10px 0 4px;font-size:22px">Login Detected</h1>
    <p style="color:#90CAF9;margin:0">Someone logged into your PC</p>
  </div>
  <div style="background:#161b22;padding:24px;color:#e6edf3;font-size:14px">
    <table style="width:100%;border-collapse:collapse">
      <tr><td style="padding:9px 0;color:#8b949e">🕐 Time</td>
          <td style="padding:9px 0"><b>{now}</b></td></tr>
      <tr style="border-top:1px solid #21262d">
          <td style="padding:9px 0;color:#8b949e">👤 User</td>
          <td style="padding:9px 0"><b>{user or 'Unknown'}</b></td></tr>
      <tr style="border-top:1px solid #21262d">
          <td style="padding:9px 0;color:#8b949e">💻 Computer</td>
          <td style="padding:9px 0"><b>{PC_NAME}</b></td></tr>
    </table>
  </div>
</div></body></html>"""
    threading.Thread(target=send_email,
        args=(f'🔐 Login Alert — {PC_NAME}', html), daemon=True).start()

def email_hacker(user, photo_bytes=None):
    now  = datetime.now().strftime('%A, %B %d %Y   %I:%M:%S %p')
    photo_html = (
        '<div style="text-align:center;margin-top:14px">'
        '<p style="color:#00FF41;font-size:12px;margin:0 0 8px">📸 INTRUDER PHOTO:</p>'
        '<img src="cid:photo" style="max-width:100%;border:3px solid #FF0000;border-radius:6px"/></div>'
        if photo_bytes else
        '<p style="color:#555;text-align:center;margin:12px 0">📷 No camera available</p>'
    )
    html = f"""<html><body style="margin:0;background:#000;font-family:'Courier New',monospace">
<div style="max-width:540px;margin:28px auto;border:2px solid #FF0000;border-radius:8px;
            overflow:hidden;box-shadow:0 0 40px #FF000055">
  <div style="background:#1a0000;padding:26px;text-align:center">
    <div style="color:#FF0000;font-size:16px;letter-spacing:4px;font-weight:bold">
      ⚠️ &nbsp; SECURITY BREACH &nbsp; ⚠️</div>
    <div style="font-size:80px;margin:12px 0">🤖</div>
    <h1 style="color:#FF0000;font-size:28px;margin:0;letter-spacing:3px">HACKER DETECTED!</h1>
    <p style="color:#FF6B6B;font-size:16px;margin:8px 0 0">Someone tried to break into your PC!</p>
  </div>
  <div style="background:#0a0000;padding:22px">
    <div style="background:#1a0000;border:1px solid #FF2222;border-radius:6px;padding:14px;margin-bottom:14px">
      <table style="width:100%;border-collapse:collapse;font-size:14px">
        <tr><td style="padding:8px 0;color:#FF4444">🕐 Time</td>
            <td style="padding:8px 0;color:#FFB3B3"><b>{now}</b></td></tr>
        <tr><td style="padding:8px 0;color:#FF4444">👤 Attacker</td>
            <td style="padding:8px 0;color:#FFB3B3"><b>{user or '???'}</b></td></tr>
        <tr><td style="padding:8px 0;color:#FF4444">💻 Target PC</td>
            <td style="padding:8px 0;color:#FFB3B3"><b>{PC_NAME}</b></td></tr>
        <tr><td style="padding:8px 0;color:#FF4444">Status</td>
            <td style="padding:8px 0"><b style="color:#FF0000">❌ WRONG PASSWORD</b></td></tr>
      </table>
    </div>
    {photo_html}
    <div style="margin-top:14px;padding:16px;background:#1a1a00;
                border:2px solid #FFFF00;border-radius:6px;text-align:center">
      <p style="color:#FFFF00;font-size:18px;font-weight:bold;margin:0;letter-spacing:2px">
        ⚡ FUCK OFF MY PC ⚡</p>
      <p style="color:#FFA500;font-size:14px;margin:8px 0 0">
        Otherwise I will HACK YOUR LIFE and send you to HELL!</p>
      <p style="font-size:26px;margin:6px 0">🔥 👿 🔥 💀 😈 💀 🔥 👿 🔥</p>
    </div>
  </div>
</div></body></html>"""
    threading.Thread(target=send_email,
        args=(f'🚨 HACKER ALERT — {PC_NAME}', html, photo_bytes), daemon=True).start()

# ════════════════════════════════════════════════════════
#  CAMERA
# ════════════════════════════════════════════════════════
def capture_photo():
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            time.sleep(0.5)
            ok, frame = cap.read()
            cap.release()
            if ok:
                _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                log('Photo captured')
                return buf.tobytes()
    except Exception as e:
        log(f'Camera: {e}')
    return None

# ════════════════════════════════════════════════════════
#  SIREN
# ════════════════════════════════════════════════════════
def play_siren(seconds=3):
    def _go():
        end = time.time() + seconds
        while time.time() < end:
            for f in range(600, 1200, 25):
                if time.time() >= end: return
                winsound.Beep(f, 12)
            for f in range(1200, 600, -25):
                if time.time() >= end: return
                winsound.Beep(f, 12)
    threading.Thread(target=_go, daemon=True).start()

# ════════════════════════════════════════════════════════
#  HACKER POPUP
# ════════════════════════════════════════════════════════
def show_hack_popup(root):
    def _build():
        p = tk.Toplevel(root)
        p.attributes('-fullscreen', True)
        p.attributes('-topmost', True)
        p.configure(bg='#000000')
        p.focus_force()
        W = p.winfo_screenwidth()
        H = p.winfo_screenheight()
        fs = max(14, W // 55)
        c = tk.Canvas(p, bg='#000000', highlightthickness=0)
        c.pack(fill='both', expand=True)
        for y in range(0, H, 5):
            c.create_line(0, y, W, y, fill='#050f05')
        for i in range(6, 0, -1):
            c.create_rectangle(i, i, W-i, H-i,
                               outline='#%02x0000' % (20*i), width=1)
        def shadow(x, y, text, size, color, tags=(), justify='center'):
            c.create_text(x+3, y+3, text=text, justify=justify,
                font=('Courier New', size, 'bold'), fill='#330000')
            return c.create_text(x, y, text=text, justify=justify,
                font=('Courier New', size, 'bold'), fill=color, tags=tags)
        shadow(W//2, int(H*.10), '🚨  INTRUSION DETECTED  🚨', fs*2, '#FF0000', tags='blink')
        c.create_text(W//2, int(H*.29), text='🤖',
            font=('Segoe UI Emoji', min(140, fs*6)))
        shadow(W//2, int(H*.51), 'FUCK OFF MY PC!', fs*3, '#FF4500')
        shadow(W//2, int(H*.63),
            'OTHERWISE I WILL HACK YOUR LIFE\nAND SEND YOU TO HELL!',
            fs+2, '#FF6600', justify='center')
        c.create_text(W//2, int(H*.73),
            text='🔥  👿  🔥  💀  😈  💀  🔥  👿  🔥',
            font=('Segoe UI Emoji', fs+4))
        c.create_text(W//2, int(H*.82),
            text='📸  YOUR PHOTO HAS BEEN CAPTURED AND SENT TO THE OWNER  📸',
            font=('Courier New', fs-1), fill='#00FF41')
        timer_id = c.create_text(W//2, int(H*.91),
            text='Closing in 8 seconds...',
            font=('Courier New', fs-3), fill='#555555')
        _bi = [0]
        _bc = ['#FF0000','#FF4400','#FF8800','#FF4400']
        def blink():
            _bi[0] = (_bi[0]+1) % len(_bc)
            for it in c.find_withtag('blink'):
                try: c.itemconfig(it, fill=_bc[_bi[0]])
                except: pass
            if p.winfo_exists(): p.after(350, blink)
        blink()
        rem = [8]
        def tick():
            rem[0] -= 1
            if p.winfo_exists():
                c.itemconfig(timer_id, text=f'Closing in {rem[0]} seconds...')
                if rem[0] > 0: p.after(1000, tick)
                else: p.destroy()
        p.after(1000, tick)
        play_siren(3)
    root.after(0, _build)

# ════════════════════════════════════════════════════════
#  LOGIN MONITOR  (WTS)
# ════════════════════════════════════════════════════════
WM_WTS     = 0x02B1
WTS_LOGON  = 0x5
WTS_LOGOFF = 0x6
WTS_LOCK   = 0x7
WTS_UNLOCK = 0x8

def start_login_monitor(on_login, on_logoff):
    def _run():
        try:
            import win32api, win32gui, win32ts
            _wts = ctypes.WinDLL('Wtsapi32.dll')
            def wnd_proc(hwnd, msg, wp, lp):
                if msg == WM_WTS:
                    user = ''
                    try: user = win32ts.WTSQuerySessionInformation(None, lp, win32ts.WTSUserName) or ''
                    except: pass
                    if wp in (WTS_LOGON, WTS_UNLOCK):  on_login(user, lp)
                    elif wp == WTS_LOGOFF: on_logoff(lp)
                return win32gui.DefWindowProc(hwnd, msg, wp, lp)
            wc = win32gui.WNDCLASS()
            wc.hInstance = win32api.GetModuleHandle(None)
            wc.lpszClassName = 'PCLM_WND'
            wc.lpfnWndProc = wnd_proc
            try: win32gui.RegisterClass(wc)
            except: pass
            hwnd = win32gui.CreateWindow('PCLM_WND','',0, 0,0,0,0, 0,0, wc.hInstance, None)
            _wts.WTSRegisterSessionNotification(hwnd, 1)
            log('Login monitor active')
            win32gui.PumpMessages()
        except Exception as e:
            log(f'Login monitor error: {e}')
    threading.Thread(target=_run, daemon=True, name='WTS').start()

# ════════════════════════════════════════════════════════
#  FAILED-LOGIN MONITOR  (win32evtlog — Security Event 4625)
# ════════════════════════════════════════════════════════
def start_failedlogin_monitor(on_fail):
    def _run():
        try:
            import win32evtlog

            # ── Pre-start check ──────────────────────────────────────────
            # Wrong passwords at the Windows login screen happen BEFORE this
            # monitor starts, so their 4625 events are already in the log.
            # Scan the last 5 minutes of events to catch them.
            try:
                h_pre  = win32evtlog.OpenEventLog(None, 'Security')
                cutoff = datetime.now() - timedelta(minutes=5)
                batch  = win32evtlog.ReadEventLog(
                    h_pre,
                    win32evtlog.EVENTLOG_BACKWARDS_READ |
                    win32evtlog.EVENTLOG_SEQUENTIAL_READ, 0) or []
                win32evtlog.CloseEventLog(h_pre)
                for ev in batch:
                    try:
                        ev_t = ev.TimeGenerated.replace(tzinfo=None)
                    except Exception:
                        break
                    if ev_t < cutoff:
                        break
                    if (ev.EventID & 0xFFFF) == 4625:
                        user = ''
                        try:
                            ins = ev.StringInserts or []
                            user = ins[5] if len(ins) > 5 else ''
                        except Exception:
                            pass
                        log(f'Pre-start wrong password: "{user}"')
                        on_fail(user)
                        break
            except Exception as pre_err:
                log(f'Pre-start check: {pre_err}')

            # ── Live monitoring ──────────────────────────────────────────
            h    = win32evtlog.OpenEventLog(None, 'Security')
            seen = win32evtlog.GetNumberOfEventLogRecords(h)
            log(f'Failed-login monitor active (event log count={seen})')

            while True:
                time.sleep(2)
                try:
                    cur = win32evtlog.GetNumberOfEventLogRecords(h)
                    if cur > seen:
                        evts = win32evtlog.ReadEventLog(
                            h,
                            win32evtlog.EVENTLOG_BACKWARDS_READ |
                            win32evtlog.EVENTLOG_SEQUENTIAL_READ, 0) or []
                        seen = cur
                        for ev in evts:
                            if (ev.EventID & 0xFFFF) == 4625:
                                user = ''
                                try:
                                    ins = ev.StringInserts or []
                                    user = ins[5] if len(ins) > 5 else ''
                                except Exception:
                                    pass
                                log(f'Wrong password detected: "{user}"')
                                on_fail(user)
                                break
                except Exception as poll_err:
                    log(f'Event poll: {poll_err}')
                    try: win32evtlog.CloseEventLog(h)
                    except Exception: pass
                    time.sleep(4)
                    try:
                        h    = win32evtlog.OpenEventLog(None, 'Security')
                        seen = win32evtlog.GetNumberOfEventLogRecords(h)
                    except Exception: pass
        except Exception as e:
            log(f'Failed-login monitor error: {e}')

    threading.Thread(target=_run, daemon=True, name='EvtLog').start()

# ════════════════════════════════════════════════════════
#  AUTOSTART  — registry Run key (no UAC, runs as normal user)
# ════════════════════════════════════════════════════════
TASK_NAME = 'PCLoginMonitor'

def set_autostart(on=True):
    python   = sys.executable
    script   = os.path.abspath(__file__)
    computer = os.environ.get('COMPUTERNAME', 'PC')
    user     = os.environ.get('USERNAME', '')

    # Enable audit policy while we have admin (needed for wrong-password events)
    if is_admin():
        for sub in ['Logon', 'Credential Validation']:
            try:
                subprocess.run(
                    ['auditpol', '/set', f'/subcategory:{sub}', '/failure:enable'],
                    capture_output=True, timeout=10)
            except: pass
        log('Audit policy: logon failures enabled')

    # Remove old HKCU Run entry (switching to Task Scheduler)
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_SET_VALUE)
        try: winreg.DeleteValue(k, TASK_NAME)
        except: pass
        winreg.CloseKey(k)
    except: pass

    if not on:
        subprocess.run(['schtasks', '/delete', '/f', '/tn', TASK_NAME],
                       capture_output=True, timeout=15)
        return

    # XML task — handles spaces in paths perfectly, RunLevel Highest = no UAC for Admins
    xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <UserId>{computer}\\{user}</UserId>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{computer}\\{user}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{python}</Command>
      <Arguments>"{script}"</Arguments>
    </Exec>
  </Actions>
</Task>'''

    tmp = os.path.join(os.environ.get('TEMP', os.getcwd()), '_pclm_task.xml')
    try:
        with open(tmp, 'w', encoding='utf-16') as f:
            f.write(xml)
        r = subprocess.run(
            ['schtasks', '/create', '/tn', TASK_NAME, '/xml', tmp, '/f'],
            capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            log('Autostart: Task Scheduler XML — no UAC at startup')
        else:
            log(f'Task Scheduler error: {r.stderr.strip()[:200]}')
    except Exception as e:
        log(f'Autostart error: {e}')
    finally:
        try: os.unlink(tmp)
        except: pass

# ════════════════════════════════════════════════════════
#  SYSTEM TRAY
# ════════════════════════════════════════════════════════
def start_tray(on_exit, on_change_email=None):
    def _go():
        try:
            import pystray
            from PIL import Image, ImageDraw
            img = Image.new('RGBA', (64,64), (0,0,0,0))
            d   = ImageDraw.Draw(img)
            d.ellipse([24,30,40,46], fill=(180,0,0))
            d.ellipse([26,20,38,32], fill=(180,0,0))
            d.ellipse([27,22,30,25], fill='white')
            d.ellipse([34,22,37,25], fill='white')
            d.line([(24,34),(8,24)],  fill='white', width=2)
            d.line([(24,38),(6,36)],  fill='white', width=2)
            d.line([(24,42),(10,52)], fill='white', width=2)
            d.line([(40,34),(56,24)], fill='white', width=2)
            d.line([(40,38),(58,36)], fill='white', width=2)
            d.line([(40,42),(54,52)], fill='white', width=2)
            d.line([(32,20),(32,4)],  fill='white', width=2)
            cfg = cfg_load()
            email_line = cfg.get('gmail', 'not set')
            menu = pystray.Menu(
                pystray.MenuItem(f'🕷️  PC Login Monitor — Active', None, enabled=False),
                pystray.MenuItem(f'📧  Alerts → {email_line}', None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem('✏️  Change Email',
                    lambda i,it: on_change_email() if on_change_email else None),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem('📋  View Log',
                    lambda i,it: os.startfile(str(LOG_F)) if LOG_F.exists() else None),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem('❌  Exit', lambda i,it: on_exit()),
            )
            icon = pystray.Icon('PCLoginMonitor', img, f'PC Login Monitor — {email_line}', menu)
            icon.run()
        except Exception as e:
            log(f'Tray error: {e}')
    threading.Thread(target=_go, daemon=True, name='Tray').start()

# ════════════════════════════════════════════════════════
#  CHANGE EMAIL DIALOG  (opened from tray)
# ════════════════════════════════════════════════════════
def change_email_dialog(root):
    cfg = cfg_load()
    dlg = tk.Toplevel(root)
    dlg.title('Change Email — PC Login Monitor')
    dlg.configure(bg='#0d1117')
    dlg.resizable(False, False)
    dlg.lift(); dlg.focus_force()

    sw = dlg.winfo_screenwidth()
    sh = dlg.winfo_screenheight()
    dlg.geometry(f'460x400+{(sw-460)//2}+{(sh-400)//2}')

    # Header
    hdr = tk.Frame(dlg, bg='#1565C0')
    hdr.pack(fill='x')
    tk.Label(hdr, text='🕷️', bg='#1565C0', fg='white',
             font=('Segoe UI Emoji', 26)).pack(side='left', padx=16, pady=10)
    tk.Label(hdr, text='Change Email Settings',
             bg='#1565C0', fg='white',
             font=('Segoe UI', 15, 'bold')).pack(side='left')

    body = tk.Frame(dlg, bg='#0d1117', padx=24, pady=16)
    body.pack(fill='both', expand=True)

    tk.Label(body, text='Gmail address that receives alerts:',
             bg='#0d1117', fg='#8b949e',
             font=('Segoe UI', 10)).pack(anchor='w')
    e_gmail = tk.Entry(body, font=('Segoe UI', 12),
                       bg='#161b22', fg='#e6edf3',
                       insertbackground='white', relief='flat',
                       highlightbackground='#30363d', highlightthickness=1)
    e_gmail.insert(0, cfg.get('gmail', ''))
    e_gmail.pack(fill='x', ipady=8, pady=(3, 14))

    tk.Label(body, text='16-letter App Password (from Google):',
             bg='#0d1117', fg='#8b949e',
             font=('Segoe UI', 10)).pack(anchor='w')
    e_code = tk.Entry(body, font=('Segoe UI', 12),
                      bg='#161b22', fg='#00FF41',
                      insertbackground='#00FF41', relief='flat',
                      highlightbackground='#30363d', highlightthickness=1,
                      justify='center')
    e_code.insert(0, cfg.get('appcode', ''))
    e_code.pack(fill='x', ipady=8, pady=(3, 8))

    tk.Label(body,
             text='Need new code? → myaccount.google.com/apppasswords',
             bg='#0d1117', fg='#484f58',
             font=('Segoe UI', 8)).pack(anchor='w', pady=(0, 12))

    status = tk.Label(body, text='', bg='#0d1117', fg='#00FF41',
                      font=('Segoe UI', 10), wraplength=400)
    status.pack(anchor='w', pady=(0, 8))

    def save():
        g    = e_gmail.get().strip()
        code = e_code.get().strip().replace(' ', '')
        if not g or '@' not in g:
            status.config(text='❌ Enter a valid Gmail address.', fg='#FF4444'); return
        if len(code) < 16:
            status.config(text='❌ Paste the 16-letter App Password.', fg='#FF4444'); return
        btn.config(state='disabled')
        status.config(text='⏳ Testing connection...', fg='#FFA500')
        dlg.update()
        def _test():
            try:
                _smtp_send(g, code, '✅ PC Login Monitor — Email Updated',
                    f'<html><body style="background:#0d1117;color:#e6edf3;'
                    f'font-family:Segoe UI;padding:28px">'
                    f'<h2 style="color:#00FF41">✅ Email settings updated!</h2>'
                    f'<p>Future alerts will be sent to <b>{g}</b></p>'
                    f'</body></html>')
                new_cfg = {**cfg, 'gmail': g, 'appcode': code, 'ready': True}
                cfg_save(new_cfg)
                dlg.after(0, lambda: status.config(
                    text=f'✅ Saved! Confirmation sent to {g}', fg='#00FF41'))
                dlg.after(2200, dlg.destroy)
            except Exception as ex:
                dlg.after(0, lambda: status.config(text=f'❌ {ex}', fg='#FF4444'))
                dlg.after(0, lambda: btn.config(state='normal'))
        threading.Thread(target=_test, daemon=True).start()

    btn = tk.Button(body, text='💾   Save & Test',
                    command=save,
                    bg='#238636', fg='white',
                    font=('Segoe UI', 12, 'bold'),
                    relief='flat', cursor='hand2',
                    activebackground='#2ea043', activeforeground='white',
                    padx=16, pady=10)
    btn.pack(fill='x')
    dlg.protocol('WM_DELETE_WINDOW', dlg.destroy)

# ════════════════════════════════════════════════════════
#  SETUP WINDOW  — simple, auto-detects Gmail from Chrome
# ════════════════════════════════════════════════════════
def run_setup(root, cfg, on_done):
    auto_gmail = detect_chrome_gmail() or cfg.get('gmail', '')

    win = tk.Toplevel(root)
    win.title('PC Login Monitor — Setup')
    win.resizable(True, True)
    win.minsize(480, 540)
    win.configure(bg='#0d1117')

    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    W, H = min(600, sw-60), min(680, sh-60)
    win.geometry(f'{W}x{H}+{(sw-W)//2}+{(sh-H)//2}')
    win.lift()
    win.focus_force()

    # ── Header ──────────────────────────────────────────
    hdr = tk.Frame(win, bg='#1565C0')
    hdr.pack(fill='x')

    tk.Label(hdr, text='🕷️', bg='#1565C0', fg='white',
             font=('Segoe UI Emoji', 32)).pack(side='left', padx=20, pady=14)
    tk.Label(hdr, text='PC Login Monitor',
             bg='#1565C0', fg='white',
             font=('Segoe UI', 20, 'bold')).pack(side='left')

    # ── Fixed bottom bar (must pack before scrollable area) ─
    bottom_bar = tk.Frame(win, bg='#161b22', padx=32, pady=14)
    bottom_bar.pack(fill='x', side='bottom')

    # ── Scrollable body ─────────────────────────────────
    _outer = tk.Frame(win, bg='#0d1117')
    _outer.pack(fill='both', expand=True)

    _canvas = tk.Canvas(_outer, bg='#0d1117', highlightthickness=0, bd=0)
    _vsb = tk.Scrollbar(_outer, orient='vertical', command=_canvas.yview)
    _canvas.configure(yscrollcommand=_vsb.set)
    _vsb.pack(side='right', fill='y')
    _canvas.pack(side='left', fill='both', expand=True)

    body = tk.Frame(_canvas, bg='#0d1117')
    _body_id = _canvas.create_window((0, 0), window=body, anchor='nw')

    body.bind('<Configure>', lambda e: _canvas.configure(scrollregion=_canvas.bbox('all')))
    _canvas.bind('<Configure>', lambda e: _canvas.itemconfig(_body_id, width=e.width))
    _canvas.bind_all('<MouseWheel>',
        lambda e: _canvas.yview_scroll(int(-1*(e.delta/120)), 'units'))

    body_inner = tk.Frame(body, bg='#0d1117')
    body_inner.pack(fill='both', expand=True, padx=32, pady=20)
    body = body_inner

    # ── Gmail row ───────────────────────────────────────
    tk.Label(body, text='Your Gmail address:',
             bg='#0d1117', fg='#8b949e',
             font=('Segoe UI', 11), anchor='w').pack(fill='x', pady=(0, 4))

    gmail_frame = tk.Frame(body, bg='#0d1117')
    gmail_frame.pack(fill='x')

    e_gmail = tk.Entry(gmail_frame, font=('Segoe UI', 12),
                       bg='#161b22', fg='#e6edf3',
                       insertbackground='white', relief='flat',
                       highlightbackground='#30363d', highlightthickness=1)
    e_gmail.pack(side='left', fill='x', expand=True, ipady=9)
    if auto_gmail:
        e_gmail.insert(0, auto_gmail)
        e_gmail.config(fg='#00FF41')

    if auto_gmail:
        tk.Label(body, text='✓ Found from Chrome automatically',
                 bg='#0d1117', fg='#3fb950',
                 font=('Segoe UI', 9)).pack(anchor='w', pady=(3, 0))

    # ── Divider ─────────────────────────────────────────
    tk.Frame(body, bg='#21262d', height=1).pack(fill='x', pady=18)

    # ── Security code section ───────────────────────────
    tk.Label(body, text='Google Security Code  (one-time setup)',
             bg='#0d1117', fg='#e6edf3',
             font=('Segoe UI', 12, 'bold'), anchor='w').pack(fill='x')

    tk.Label(body,
             text='Google requires a 16-letter security code. You only do this once.',
             bg='#0d1117', fg='#6e7681',
             font=('Segoe UI', 10), justify='left').pack(anchor='w', pady=(4, 10))

    # Step 1 — Enable 2FA
    step1 = tk.Frame(body, bg='#1a2332', padx=14, pady=12)
    step1.pack(fill='x', pady=(0, 5))
    tk.Label(step1, text='Step 1 — Enable 2-Step Verification',
             bg='#1a2332', fg='#58a6ff',
             font=('Segoe UI', 10, 'bold')).pack(anchor='w')
    tk.Label(step1,
             text='Google App Passwords only work after 2-Step Verification is ON.\n'
                  'Click below → click "Get started" → follow the steps (uses your phone).',
             bg='#1a2332', fg='#8b949e',
             font=('Segoe UI', 10), wraplength=480, justify='left').pack(anchor='w', pady=(3, 6))
    tk.Button(step1,
        text='📱   Enable 2-Step Verification  →',
        command=lambda: webbrowser.open(
            'https://myaccount.google.com/signinoptions/two-step-verification/enroll-welcome'),
        bg='#0d419d', fg='white', font=('Segoe UI', 11, 'bold'),
        relief='flat', cursor='hand2',
        activebackground='#1565C0', activeforeground='white',
        padx=14, pady=9).pack(fill='x')

    # Step 2 — Get App Password
    step2 = tk.Frame(body, bg='#161b22', padx=14, pady=12)
    step2.pack(fill='x', pady=(0, 5))
    tk.Label(step2, text='Step 2 — Get App Password  (after Step 1 is done)',
             bg='#161b22', fg='#58a6ff',
             font=('Segoe UI', 10, 'bold')).pack(anchor='w')
    tk.Label(step2,
             text='Click below → on Google page: App name = type "PCMonitor" → click Create\n'
                  '→ Google shows a 16-letter code in a yellow box → copy it.',
             bg='#161b22', fg='#8b949e',
             font=('Segoe UI', 10), wraplength=480, justify='left').pack(anchor='w', pady=(3, 6))
    tk.Button(step2,
        text='🔑   Open App Passwords Page  →',
        command=lambda: webbrowser.open('https://myaccount.google.com/apppasswords'),
        bg='#1565C0', fg='white', font=('Segoe UI', 11, 'bold'),
        relief='flat', cursor='hand2',
        activebackground='#1976D2', activeforeground='white',
        padx=14, pady=9).pack(fill='x')

    # Step 3
    step3 = tk.Frame(body, bg='#161b22', padx=14, pady=12)
    step3.pack(fill='x', pady=(0, 10))
    tk.Label(step3, text='Step 3  — Paste the 16-letter code here:',
             bg='#161b22', fg='#58a6ff',
             font=('Segoe UI', 10, 'bold')).pack(anchor='w')

    e_code = tk.Entry(step3, font=('Segoe UI', 14),
                      bg='#0d1117', fg='#00FF41',
                      insertbackground='#00FF41', relief='flat',
                      highlightbackground='#30363d', highlightthickness=1,
                      justify='center')
    e_code.pack(fill='x', ipady=10, pady=(6, 0))
    if cfg.get('appcode'):
        e_code.insert(0, cfg['appcode'])

    tk.Label(body, text='Example:  abcd efgh ijkl mnop  (spaces are fine, Google adds them)',
             bg='#0d1117', fg='#484f58',
             font=('Segoe UI', 8)).pack(anchor='w', pady=(2, 0))

    # ── Status (in bottom bar so it's always visible) ───
    status = tk.Label(bottom_bar, text='', bg='#161b22', fg='#00FF41',
                      font=('Segoe UI', 10), wraplength=520, justify='left')
    status.pack(fill='x', pady=(0, 6))

    # ── Start button ────────────────────────────────────
    def start():
        g    = e_gmail.get().strip()
        code = e_code.get().strip().replace(' ', '')
        if not g or '@' not in g:
            messagebox.showerror('Error', 'Enter your Gmail address.', parent=win); return
        if len(code) < 16:
            messagebox.showerror('Error',
                'Paste the 16-letter code from Google.\n\n'
                'Click "Open Google App Passwords Page" above to get it.', parent=win); return

        status.config(text='⏳ Connecting to Gmail...', fg='#FFA500')
        btn_start.config(state='disabled')
        win.update()

        def _test():
            try:
                _smtp_send(g, code,
                    f'✅ PC Login Monitor is Active — {PC_NAME}',
                    f"""<html><body style="background:#0d1117;font-family:'Segoe UI';padding:30px">
<div style="background:#1565C0;padding:22px;border-radius:8px;color:white;text-align:center;max-width:400px;margin:auto">
  <div style="font-size:48px">🕷️</div>
  <h2 style="margin:8px 0">PC Login Monitor is Active!</h2>
  <p style="margin:4px 0;opacity:.85">Watching <b>{PC_NAME}</b> for you</p>
  <p style="margin:4px 0;opacity:.85">Alerts → <b>{g}</b></p>
</div></body></html>""")

                new_cfg = {'gmail': g, 'appcode': code, 'ready': True}
                cfg_save(new_cfg)
                set_autostart(True)

                win.after(0, lambda: status.config(
                    text=f'✅ Done!  Check your inbox at {g}', fg='#00FF41'))
                win.after(0, lambda: btn_start.config(
                    text='✅  Monitoring Active', bg='#1B5E20', state='disabled'))
                win.after(2500, lambda: on_done(new_cfg))

            except smtplib.SMTPAuthenticationError:
                win.after(0, lambda: status.config(
                    text='❌ Wrong code.  Make sure you copied the 16-letter code correctly.',
                    fg='#FF4444'))
                win.after(0, lambda: btn_start.config(state='normal'))
            except Exception as ex:
                win.after(0, lambda: status.config(text=f'❌ {ex}', fg='#FF4444'))
                win.after(0, lambda: btn_start.config(state='normal'))

        threading.Thread(target=_test, daemon=True).start()

    btn_start = tk.Button(bottom_bar,
        text='▶   Start Monitoring',
        command=start,
        bg='#238636', fg='white',
        font=('Segoe UI', 14, 'bold'),
        relief='flat', cursor='hand2',
        activebackground='#2ea043', activeforeground='white',
        padx=20, pady=13)
    btn_start.pack(fill='x')

    tk.Label(bottom_bar,
        text='App hides in system tray after setup  (bottom-right ▲ near clock)',
        bg='#161b22', fg='#3d444d',
        font=('Segoe UI', 9)).pack(pady=(6, 0))

    win.protocol('WM_DELETE_WINDOW', root.destroy)

# ════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════
def main():
    cfg = cfg_load()

    # ── Fire login alert IMMEDIATELY — before any other init ──
    # This runs in the background while tkinter / monitors load,
    # so the email arrives within seconds of Windows starting.
    if cfg.get('ready'):
        threading.Thread(
            target=email_login,
            args=(os.environ.get('USERNAME', ''),),
            daemon=True).start()

    # App needs admin to read Security event log (wrong-password detection)
    # Task Scheduler with RunLevel Highest runs it elevated silently (no UAC popup)
    # for users in the Administrators group. Only elevate manually on first run.
    if not is_admin():
        elevate(); return

    root = tk.Tk()
    root.withdraw()

    def begin(cfg):
        log(f'Monitoring started — {PC_NAME}')

        # Enable audit policy NOW (synchronous) so 4625 events are written immediately
        if is_admin():
            for sub in ['Logon', 'Credential Validation']:
                try:
                    subprocess.run(
                        ['auditpol', '/set', f'/subcategory:{sub}', '/failure:enable'],
                        capture_output=True, timeout=10)
                except Exception:
                    pass
            log('Audit policy: logon failures enabled')

        threading.Thread(target=set_autostart, args=(True,), daemon=True).start()

        def on_login(user, sid):
            log(f'LOGIN: {user}')
            email_login(user)

        def on_logoff(sid):
            log(f'LOGOFF: session {sid}')

        def on_failed(user):
            log(f'FAILED LOGIN: {user}')
            show_hack_popup(root)
            def _bg():
                photo = capture_photo()
                email_hacker(user, photo)
            threading.Thread(target=_bg, daemon=True).start()

        start_login_monitor(on_login, on_logoff)
        start_failedlogin_monitor(on_failed)
        start_tray(on_exit=root.destroy,
                   on_change_email=lambda: root.after(0, lambda: change_email_dialog(root)))

    if cfg.get('ready'):
        begin(cfg)
    else:
        run_setup(root, cfg, begin)

    root.mainloop()

# ════════════════════════════════════════════════════════
#  SETTINGS WINDOW  (launched via SETTINGS.bat)
# ════════════════════════════════════════════════════════
def run_settings():
    cfg = cfg_load()

    root = tk.Tk()
    root.title('PC Login Monitor — Settings & Update')
    root.configure(bg='#0d1117')
    root.resizable(True, True)
    root.minsize(520, 620)

    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    W, H = min(560, sw-60), min(700, sh-60)
    root.geometry(f'{W}x{H}+{(sw-W)//2}+{(sh-H)//2}')

    # ── Header ──────────────────────────────────────────
    hdr = tk.Frame(root, bg='#0d419d')
    hdr.pack(fill='x')
    tk.Label(hdr, text='🕷️', bg='#0d419d', fg='white',
             font=('Segoe UI Emoji', 30)).pack(side='left', padx=18, pady=12)
    hdr_txt = tk.Frame(hdr, bg='#0d419d')
    hdr_txt.pack(side='left')
    tk.Label(hdr_txt, text='PC Login Monitor',
             bg='#0d419d', fg='white',
             font=('Segoe UI', 18, 'bold')).pack(anchor='w')
    tk.Label(hdr_txt, text='Settings & Update',
             bg='#0d419d', fg='#90CAF9',
             font=('Segoe UI', 11)).pack(anchor='w')

    # ── Scrollable body ─────────────────────────────────
    _outer = tk.Frame(root, bg='#0d1117')
    _outer.pack(fill='both', expand=True)
    _canvas = tk.Canvas(_outer, bg='#0d1117', highlightthickness=0)
    _vsb = tk.Scrollbar(_outer, orient='vertical', command=_canvas.yview)
    _canvas.configure(yscrollcommand=_vsb.set)
    _vsb.pack(side='right', fill='y')
    _canvas.pack(side='left', fill='both', expand=True)
    _inner = tk.Frame(_canvas, bg='#0d1117')
    _bid = _canvas.create_window((0,0), window=_inner, anchor='nw')
    _inner.bind('<Configure>', lambda e: _canvas.configure(scrollregion=_canvas.bbox('all')))
    _canvas.bind('<Configure>', lambda e: _canvas.itemconfig(_bid, width=e.width))
    _canvas.bind_all('<MouseWheel>', lambda e: _canvas.yview_scroll(int(-1*(e.delta/120)), 'units'))

    body = tk.Frame(_inner, bg='#0d1117', padx=28, pady=18)
    body.pack(fill='both', expand=True)

    # ── Current Status ───────────────────────────────────
    is_ready = cfg.get('ready', False)
    current_email = cfg.get('gmail', 'Not set')

    status_bg = '#0d2b0d' if is_ready else '#2b0d0d'
    status_fg = '#00FF41' if is_ready else '#FF4444'
    status_txt = f'✅  Monitoring ACTIVE — alerts go to:  {current_email}' if is_ready else '❌  Not configured — run START.bat first'

    status_box = tk.Frame(body, bg=status_bg, padx=14, pady=12)
    status_box.pack(fill='x', pady=(0, 18))
    tk.Label(status_box, text=status_txt,
             bg=status_bg, fg=status_fg,
             font=('Segoe UI', 10, 'bold'),
             wraplength=460, justify='left').pack(anchor='w')

    # ── Section: Change Email ────────────────────────────
    tk.Label(body, text='Change Alert Email',
             bg='#0d1117', fg='#e6edf3',
             font=('Segoe UI', 13, 'bold')).pack(anchor='w', pady=(0,4))
    tk.Label(body,
             text='Update the Gmail address that receives login alerts.',
             bg='#0d1117', fg='#6e7681',
             font=('Segoe UI', 10)).pack(anchor='w', pady=(0,10))

    email_box = tk.Frame(body, bg='#161b22', padx=14, pady=14)
    email_box.pack(fill='x', pady=(0,6))

    tk.Label(email_box, text='Gmail address:',
             bg='#161b22', fg='#8b949e',
             font=('Segoe UI', 10)).pack(anchor='w')

    auto_gmail = detect_chrome_gmail()
    e_gmail = tk.Entry(email_box, font=('Segoe UI', 12),
                       bg='#0d1117', fg='#e6edf3',
                       insertbackground='white', relief='flat',
                       highlightbackground='#30363d', highlightthickness=1)
    e_gmail.insert(0, current_email)
    e_gmail.pack(fill='x', ipady=8, pady=(3,0))

    if auto_gmail and auto_gmail != current_email:
        tk.Label(email_box,
                 text=f'Chrome detected: {auto_gmail}',
                 bg='#161b22', fg='#3fb950',
                 font=('Segoe UI', 9),
                 cursor='hand2').pack(anchor='w', pady=(4,0))

    # ── Section: App Password ────────────────────────────
    tk.Label(body, text='',
             bg='#0d1117').pack(pady=4)

    tk.Label(body, text='Update App Password',
             bg='#0d1117', fg='#e6edf3',
             font=('Segoe UI', 13, 'bold')).pack(anchor='w', pady=(0,4))
    tk.Label(body,
             text='Paste a new 16-letter Google App Password below.\n'
                  'Leave blank to keep the current password.',
             bg='#0d1117', fg='#6e7681',
             font=('Segoe UI', 10), justify='left').pack(anchor='w', pady=(0,10))

    pass_box = tk.Frame(body, bg='#161b22', padx=14, pady=14)
    pass_box.pack(fill='x', pady=(0,6))

    tk.Label(pass_box, text='16-letter App Password  (spaces OK):',
             bg='#161b22', fg='#8b949e',
             font=('Segoe UI', 10)).pack(anchor='w')
    e_code = tk.Entry(pass_box, font=('Segoe UI', 13),
                      bg='#0d1117', fg='#00FF41',
                      insertbackground='#00FF41', relief='flat',
                      highlightbackground='#30363d', highlightthickness=1,
                      justify='center')
    e_code.pack(fill='x', ipady=10, pady=(3,6))
    tk.Label(pass_box,
             text='Get new code → myaccount.google.com/apppasswords',
             bg='#161b22', fg='#484f58',
             font=('Segoe UI', 8),
             cursor='hand2').pack(anchor='w')
    tk.Button(pass_box,
              text='🔑  Open App Passwords Page  →',
              command=lambda: webbrowser.open('https://myaccount.google.com/apppasswords'),
              bg='#1565C0', fg='white',
              font=('Segoe UI', 10, 'bold'),
              relief='flat', cursor='hand2',
              activebackground='#1976D2', activeforeground='white',
              padx=10, pady=6).pack(fill='x', pady=(8,0))

    # ── Section: Autostart ───────────────────────────────
    tk.Label(body, text='',
             bg='#0d1117').pack(pady=4)

    tk.Label(body, text='Auto-Start on Windows Login',
             bg='#0d1117', fg='#e6edf3',
             font=('Segoe UI', 13, 'bold')).pack(anchor='w', pady=(0,4))

    auto_box = tk.Frame(body, bg='#161b22', padx=14, pady=14)
    auto_box.pack(fill='x', pady=(0,18))

    def _task_exists():
        try:
            r = subprocess.run(
                ['schtasks', '/query', '/tn', TASK_NAME],
                capture_output=True, timeout=10)
            return r.returncode == 0
        except: return False

    task_ok = _task_exists()
    auto_status = ('✅  Auto-start is active — runs elevated automatically on every login'
                   if task_ok else
                   '⚠️  Auto-start not set — click Fix below')
    auto_color = '#00FF41' if task_ok else '#FFA500'

    task_lbl = tk.Label(auto_box, text=auto_status,
                        bg='#161b22', fg=auto_color,
                        font=('Segoe UI', 10),
                        wraplength=460, justify='left')
    task_lbl.pack(anchor='w', pady=(0,8))

    def reinstall_task():
        set_autostart(True)
        task_lbl.config(
            text='✅  Fixed! Auto-starts silently on next login (no UAC prompt)',
            fg='#00FF41')

    tk.Button(auto_box,
              text='🔄  Fix Auto-Start',
              command=reinstall_task,
              bg='#21262d', fg='#e6edf3',
              font=('Segoe UI', 10),
              relief='flat', cursor='hand2',
              activebackground='#30363d',
              padx=10, pady=6).pack(anchor='w')

    # ── Bottom bar ───────────────────────────────────────
    bottom = tk.Frame(root, bg='#161b22', padx=28, pady=14)
    bottom.pack(fill='x', side='bottom')

    save_status = tk.Label(bottom, text='', bg='#161b22', fg='#00FF41',
                           font=('Segoe UI', 10), wraplength=480)
    save_status.pack(fill='x', pady=(0,8))

    def save():
        g    = e_gmail.get().strip()
        raw  = e_code.get().strip()
        code = raw.replace(' ', '') if raw else cfg.get('appcode', '')

        if not g or '@' not in g:
            save_status.config(text='❌  Enter a valid Gmail address.', fg='#FF4444'); return
        if len(code) < 16:
            save_status.config(text='❌  Paste the 16-letter App Password (or leave blank to keep current).', fg='#FF4444'); return

        btn_save.config(state='disabled', text='⏳  Testing...')
        save_status.config(text='Connecting to Gmail...', fg='#FFA500')
        root.update()

        def _test():
            try:
                _smtp_send(g, code,
                    '✅ PC Login Monitor — Settings Updated',
                    f'<html><body style="background:#0d1117;color:#e6edf3;'
                    f'font-family:Segoe UI;padding:28px">'
                    f'<h2 style="color:#00FF41">✅ Settings saved!</h2>'
                    f'<p>Login alerts will be sent to <b>{g}</b></p>'
                    f'<p style="color:#6e7681;font-size:13px">PC Login Monitor is watching your PC.</p>'
                    f'</body></html>')
                new_cfg = {**cfg, 'gmail': g, 'appcode': code, 'ready': True}
                cfg_save(new_cfg)
                root.after(0, lambda: save_status.config(
                    text=f'✅  Saved! Confirmation sent to {g}', fg='#00FF41'))
                root.after(0, lambda: btn_save.config(
                    state='disabled', text='✅  Saved', bg='#1B5E20'))
                root.after(0, lambda: status_box.config(bg='#0d2b0d'))
            except smtplib.SMTPAuthenticationError:
                root.after(0, lambda: save_status.config(
                    text='❌  Wrong App Password. Get a new one from Google.', fg='#FF4444'))
                root.after(0, lambda: btn_save.config(state='normal', text='💾  Save & Test'))
            except Exception as ex:
                root.after(0, lambda: save_status.config(text=f'❌  {ex}', fg='#FF4444'))
                root.after(0, lambda: btn_save.config(state='normal', text='💾  Save & Test'))

        threading.Thread(target=_test, daemon=True).start()

    btn_save = tk.Button(bottom,
                         text='💾  Save & Test',
                         command=save,
                         bg='#238636', fg='white',
                         font=('Segoe UI', 13, 'bold'),
                         relief='flat', cursor='hand2',
                         activebackground='#2ea043', activeforeground='white',
                         padx=20, pady=12)
    btn_save.pack(fill='x')

    root.protocol('WM_DELETE_WINDOW', root.destroy)
    root.mainloop()


if __name__ == '__main__':
    if '--settings' in sys.argv:
        run_settings()
    else:
        main()
