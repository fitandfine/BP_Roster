"""
Dashboard – Roster Management System
------------------------------------

✓ Employee Management  (copy‑all‑emails)
✓ Roster Creation      (load previous, live hours, per‑day notes,
                        top‑bar Finalize Roster button)
✓ Change Password
"""

import os, sqlite3, datetime, tkinter as tk
from   tkinter import ttk, messagebox
import pdf_generator                                   # your own module

# ───────────────────────── constants ───────────────────────────────────────
DB          = "roster.db"
ROSTERS_DIR = "Rosters"
os.makedirs(ROSTERS_DIR, exist_ok=True)

try:
    from tkcalendar import DateEntry
except ImportError:
    messagebox.showerror("Missing lib",
                         "tkcalendar not installed.\n$  pip install tkcalendar")
    raise

DAYNAMES     = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
TIME_OPTIONS = [(datetime.datetime(1900,1,1)+datetime.timedelta(minutes=15*i)
                ).strftime("%H:%M") for i in range(96)]

# ───────────────────────── global state ────────────────────────────────────
current_manager      = None
selected_employee_id = None

global_duties = {d: [] for d in DAYNAMES}   # template for each weekday
roster_duties = {}                          # concrete week (date‑keyed)
special_notes = {}                          # date → note string

# ═════════════════════════ launch ══════════════════════════════════════════
def launch_dashboard(manager_username: str):
    global current_manager
    current_manager = manager_username

    root = tk.Tk()
    root.title("Roster Dashboard")
    root.geometry("1050x720")

    nb   = ttk.Notebook(root); nb.pack(fill="both", expand=True, padx=8, pady=8)
    emp  = ttk.Frame(nb); nb.add(emp,  text="Employee Management")
    rost = ttk.Frame(nb); nb.add(rost, text="Roster Creation")
    passwd=ttk.Frame(nb); nb.add(passwd,text="Change Password")

    init_employee_tab(emp)
    init_roster_tab  (rost)
    init_password_tab(passwd)

    root.mainloop()

# ═════════════════════════ employees ═══════════════════════════════════════
def init_employee_tab(tab: tk.Frame):
    global selected_employee_id

    # ── form ────────────────────────────────────────────────────────────────
    form = ttk.LabelFrame(tab, text="Employee Details", padding=10)
    form.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

    row=0
    ttk.Label(form, text="Name").grid   (row=row, column=0, sticky="e")
    name_e = ttk.Entry(form, width=30); name_e.grid(row=row, column=1, padx=4)
    row+=1
    ttk.Label(form, text="Email").grid  (row=row, column=0, sticky="e")
    mail_e = ttk.Entry(form, width=30); mail_e.grid(row=row, column=1, padx=4)
    row+=1
    ttk.Label(form, text="Phone").grid  (row=row, column=0, sticky="e")
    phone_e= ttk.Entry(form, width=30); phone_e.grid(row=row, column=1, padx=4)
    row+=1
    ttk.Label(form, text="Max hrs/wk").grid(row=row, column=0, sticky="e")
    max_e  = ttk.Entry(form, width=30); max_e.grid (row=row, column=1, padx=4)

    # days‑unavailable tick‑boxes
    row+=1
    ttk.Label(form,text="Days unavailable").grid(row=row,column=0,sticky="ne")
    dv_frame = ttk.Frame(form); dv_frame.grid(row=row,column=1,sticky="w")
    day_vars={d: tk.IntVar() for d in DAYNAMES}
    for d in DAYNAMES:
        ttk.Checkbutton(dv_frame,text=d,variable=day_vars[d]
                       ).pack(side="left", padx=2)

    # ── list box ────────────────────────────────────────────────────────────
    list_fr = ttk.LabelFrame(tab,text="Registered Employees",padding=8)
    list_fr.grid(row=1,column=0,sticky="nsew",padx=10,pady=5)
    tab.rowconfigure(1,weight=1); tab.columnconfigure(0,weight=1)
    lb = tk.Listbox(list_fr); lb.pack(fill="both", expand=True)

    def refresh_list():
        lb.delete(0,tk.END)
        with sqlite3.connect(DB) as con:
            for sid,n in con.execute("SELECT staff_id,name FROM staff ORDER BY name"):
                lb.insert(tk.END,f"{sid}:{n}")
    refresh_list()

    def populate_form(_=None):
        global selected_employee_id
        sel=lb.curselection()
        if not sel: return
        sid=int(lb.get(sel[0]).split(":")[0])
        selected_employee_id=sid
        with sqlite3.connect(DB) as con:
            n,e,p,m,du=con.execute("""SELECT name,email,phone_number,max_hours,days_unavailable
                                       FROM staff WHERE staff_id=?""",(sid,)).fetchone()
        for widget,val in zip((name_e,mail_e,phone_e,max_e),(n,e,p,m or "")):
            widget.delete(0,tk.END); widget.insert(0,val)
        for v in day_vars.values(): v.set(0)
        if du:
            for d in du.split(","):
                if d.strip() in day_vars: day_vars[d.strip()].set(1)
    lb.bind("<<ListboxSelect>>", populate_form)

    def save_employee():
        global selected_employee_id
        data = dict(
            n  = name_e.get().strip(),
            e  = mail_e.get().strip(),
            p  = phone_e.get().strip(),
            mx = max_e.get().strip() or None,
            du = ",".join([d for d,v in day_vars.items() if v.get()==1])
        )
        with sqlite3.connect(DB) as con:
            cur=con.cursor()
            if selected_employee_id:
                cur.execute("""UPDATE staff
                               SET name=?,email=?,phone_number=?,max_hours=?,days_unavailable=?
                               WHERE staff_id=?""",
                            (data['n'],data['e'],data['p'],data['mx'],data['du'],
                             selected_employee_id))
            else:
                cur.execute("""INSERT INTO staff(name,email,phone_number,max_hours,days_unavailable)
                               VALUES(?,?,?,?,?)""",
                            (data['n'],data['e'],data['p'],data['mx'],data['du']))
        selected_employee_id=None
        for w in (name_e,mail_e,phone_e,max_e): w.delete(0,tk.END)
        for v in day_vars.values(): v.set(0)
        refresh_list(); messagebox.showinfo("Saved","Employee record saved.")

    ttk.Button(form,text="Add / Update",command=save_employee
              ).grid(row=row+1,column=0,columnspan=2,pady=6)

    # copy‑emails button
    def copy_emails():
        with sqlite3.connect(DB) as con:
            emails=",".join(e for e, in con.execute("SELECT email FROM staff"))
        tab.clipboard_clear(); tab.clipboard_append(emails)
        messagebox.showinfo("Copied",f"{len(emails.split(','))} addresses copied.")
    ttk.Button(tab,text="Copy ALL emails",command=copy_emails
              ).grid(row=2,column=0,pady=(0,10))

# ═════════════════════════ roster tab ═══════════════════════════════════════
def init_roster_tab(tab: tk.Frame):
    global global_duties, roster_duties, special_notes

    # ── top bar (Finalize button lives here) ────────────────────────────────
    top = ttk.Frame(tab); top.pack(fill="x", padx=10, pady=6)

    ttk.Label(top,text="Previous").grid(row=0,column=0,sticky="e")
    prev_var=tk.StringVar()
    prev_cb=ttk.Combobox(top,textvariable=prev_var,state="readonly",width=38)
    prev_cb.grid(row=0,column=1,padx=5)

    ttk.Label(top,text="Start").grid(row=0,column=2,sticky="e")
    start_e=DateEntry(top,width=12,date_pattern="yyyy-mm-dd")
    start_e.grid(row=0,column=3,padx=2)
    ttk.Label(top,text="End").grid(row=0,column=4,sticky="e")
    end_e=DateEntry(top,width=12,date_pattern="yyyy-mm-dd")
    end_e.grid(row=0,column=5,padx=2)

    # Finalize button **now on the same bar**
    finalize_btn = ttk.Button(top,text="Finalize Roster")
    finalize_btn.grid(row=0,column=6,padx=(16,0))   # a little spacing

    def refresh_history():
        with sqlite3.connect(DB) as con:
            rows=con.execute("SELECT roster_id,start_date,end_date FROM roster ORDER BY roster_id DESC").fetchall()
        prev_cb["values"]=[f"{r[0]}: {r[1]} → {r[2]}" for r in rows]
    refresh_history()

    # ── main split (week grid + hours) ──────────────────────────────────────
    main=ttk.Frame(tab); main.pack(fill="both",expand=True,padx=10,pady=5)
    week_fr=ttk.LabelFrame(main,text="Week Duties"); week_fr.pack(side="left",fill="both",expand=True)
    side_fr=ttk.LabelFrame(main,text="Weekly Hours"); side_fr.pack(side="left",fill="y",padx=(6,0))
    hours_lb=tk.Listbox(side_fr,width=28); hours_lb.pack(fill="y",expand=True,padx=5,pady=5)

    day_lbs, note_entries = {}, {}

    # ── helper: hours calc ─────────────────────────────────────────────────
    def recalc_hours():
        hours_lb.delete(0,tk.END)
        with sqlite3.connect(DB) as con:
            emps=[e for e, in con.execute("SELECT name FROM staff")]
        totals={e:0.0 for e in emps}
        for duties in global_duties.values():
            for d in duties:
                dur=(datetime.datetime.strptime(d['end'],"%H:%M")
                     -datetime.datetime.strptime(d['start'],"%H:%M")).seconds/3600
                totals[d['employee']]+=dur
        for e in emps:
            hours_lb.insert(tk.END,f"{e}: {totals[e]:.1f} h")

    # ── helper: refresh single day listbox ─────────────────────────────────-
    def refresh_day(ds):
        lb=day_lbs[ds]; lb.delete(0,tk.END)
        if roster_duties[ds]:
            for d in roster_duties[ds]:
                lb.insert(tk.END,f"{d['employee']} ({d['start']}-{d['end']})")
        else:
            lb.insert(tk.END,"(No duties)")

    # ── build / rebuild week grid ─────────────────────────────────────────--
    def build_week():
        for w in week_fr.winfo_children(): w.destroy()
        day_lbs.clear(); note_entries.clear()

        sd=start_e.get_date(); end_e.set_date(sd+datetime.timedelta(days=6))

        for i in range(7):
            d     = sd+datetime.timedelta(days=i)
            ds    = d.strftime("%Y-%m-%d")
            wd    = d.strftime("%A")
            roster_duties[ds]=list(global_duties[wd])
            special_notes.setdefault(ds,"")

            cell=ttk.Frame(week_fr,borderwidth=1,relief="solid",padding=4)
            cell.grid(row=i//2,column=i%2,sticky="nsew",padx=4,pady=4)
            ttk.Label(cell,text=f"{wd}, {ds}",font=("Helvetica",10,"bold")).pack(anchor="w")

            lb=tk.Listbox(cell,width=40,height=4); lb.pack()
            day_lbs[ds]=lb; refresh_day(ds)
            lb.bind("<Double-Button-1>",lambda _,d=ds: edit_duty(d))

            bf=ttk.Frame(cell); bf.pack(pady=2)
            ttk.Button(bf,text="Add",command=lambda d=ds: add_duty(d)).pack(side="left",padx=2)
            ttk.Button(bf,text="Remove", command=lambda d=ds: rm_duty(d)).pack(side="left",padx=2)

            ttk.Label(cell,text="Note:").pack(anchor="w")
            en=tk.Entry(cell,width=40)
            en.pack(fill="x"); en.insert(0,special_notes[ds])
            en.bind("<FocusOut>",lambda ev,d=ds,e=en: special_notes.__setitem__(d,e.get()))
            note_entries[ds]=en
        recalc_hours()

    # ── helper: available staff --------------------------------------------
    def available_staff(wd):
        with sqlite3.connect(DB) as con:
            return [n for n,du in con.execute("SELECT name,days_unavailable FROM staff")
                    if not du or wd not in du.split(",")]

    # ── duty CRUD -----------------------------------------------------------
    def add_duty(ds):
        wd=datetime.datetime.strptime(ds,"%Y-%m-%d").strftime("%A")
        av=available_staff(wd)
        if not av: messagebox.showinfo("Info",f"No staff available on {wd}."); return
        win=tk.Toplevel(); win.title("Add Duty"); win.grab_set()
        emp=tk.StringVar(value=av[0]); st=tk.StringVar(value="09:00"); et=tk.StringVar(value="17:00")
        ttk.Label(win,text="Employee").grid(row=0,column=0,sticky="e")
        ttk.Combobox(win,values=av,textvariable=emp,state="readonly").grid(row=0,column=1,padx=4,pady=2)
        ttk.Label(win,text="Start").grid(row=1,column=0,sticky="e")
        ttk.Combobox(win,values=TIME_OPTIONS,textvariable=st,width=8).grid(row=1,column=1)
        ttk.Label(win,text="End").grid  (row=2,column=0,sticky="e")
        ttk.Combobox(win,values=TIME_OPTIONS,textvariable=et,width=8).grid(row=2,column=1)
        def sv():
            if datetime.datetime.strptime(et.get(),"%H:%M")<=datetime.datetime.strptime(st.get(),"%H:%M"):
                messagebox.showerror("Err","End after start"); return
            global_duties[wd].append({"employee":emp.get(),"start":st.get(),"end":et.get()})
            build_week(); win.destroy()
        ttk.Button(win,text="Save",command=sv).grid(row=3,column=0,columnspan=2,pady=6)

    def edit_duty(ds):
        lb=day_lbs[ds]; sel=lb.curselection()
        if not sel: return
        idx=sel[0]; duty=roster_duties[ds][idx]
        wd=datetime.datetime.strptime(ds,"%Y-%m-%d").strftime("%A")
        av=available_staff(wd)
        win=tk.Toplevel(); win.title("Edit Duty"); win.grab_set()
        emp=tk.StringVar(value=duty['employee']); st=tk.StringVar(value=duty['start']); et=tk.StringVar(value=duty['end'])
        ttk.Label(win,text="Employee").grid(row=0,column=0,sticky="e")
        ttk.Combobox(win,values=av,textvariable=emp,state="readonly").grid(row=0,column=1,padx=4,pady=2)
        ttk.Label(win,text="Start").grid(row=1,column=0,sticky="e")
        ttk.Combobox(win,values=TIME_OPTIONS,textvariable=st,width=8).grid(row=1,column=1)
        ttk.Label(win,text="End").grid  (row=2,column=0,sticky="e")
        ttk.Combobox(win,values=TIME_OPTIONS,textvariable=et,width=8).grid(row=2,column=1)
        def sv():
            if datetime.datetime.strptime(et.get(),"%H:%M")<=datetime.datetime.strptime(st.get(),"%H:%M"):
                messagebox.showerror("Err","End after start"); return
            duty.update(employee=emp.get(),start=st.get(),end=et.get())
            global_duties[wd][idx]=duty.copy()
            build_week(); win.destroy()
        ttk.Button(win,text="Save",command=sv).grid(row=3,column=0,columnspan=2,pady=6)

    def rm_duty(ds):
        lb=day_lbs[ds]; sel=lb.curselection()
        if sel:
            wd=datetime.datetime.strptime(ds,"%Y-%m-%d").strftime("%A")
            global_duties[wd].pop(sel[0]); build_week()

    # ── load previous roster (dedup duties) ---------------------------------
    def load_previous(_=None):
        sel=prev_var.get()
        if not sel: return
        rid=int(sel.split(":")[0])
        for lst in global_duties.values(): lst.clear()
        special_notes.clear()

        with sqlite3.connect(DB) as con:
            cur=con.cursor()
            rows=cur.execute("""SELECT duty_date,employee,start_time,end_time,note
                                FROM roster_duties WHERE roster_id=?""",(rid,)).fetchall()
            sd_s,ed_s=cur.execute("SELECT start_date,end_date FROM roster WHERE roster_id=?",
                                   (rid,)).fetchone()

        # install duties (skip duplicates)
        seen=set()
        for ds,emp,st,et,note in rows:
            key=(ds,emp,st,et)
            if key in seen: continue
            seen.add(key)
            wd=datetime.datetime.strptime(ds,"%Y-%m-%d").strftime("%A")
            global_duties[wd].append({"employee":emp,"start":st,"end":et})
            special_notes[ds]=note or ""

        start_e.set_date(datetime.datetime.strptime(sd_s,"%Y-%m-%d").date())
        end_e  .set_date(datetime.datetime.strptime(ed_s,"%Y-%m-%d").date())
        build_week()
        for ds,txt in special_notes.items():
            if ds in note_entries:
                note_entries[ds].delete(0,tk.END); note_entries[ds].insert(0,txt)
    prev_cb.bind("<<ComboboxSelected>>", load_previous)

    # ── finalize roster -----------------------------------------------------
    def finalize():
        for ds,en in note_entries.items(): special_notes[ds]=en.get()

        sd=start_e.get_date(); ed=end_e.get_date()
        sd_s,ed_s=sd.strftime("%Y-%m-%d"),ed.strftime("%Y-%m-%d")

        with sqlite3.connect(DB) as con:
            cur=con.cursor()
            cur.execute("INSERT INTO roster(start_date,end_date,pdf_file) VALUES(?,?,?)",
                        (sd_s,ed_s,""))
            rid=cur.lastrowid
            for ds,dlist in roster_duties.items():
                note=special_notes.get(ds,"")
                for d in dlist:
                    cur.execute("""INSERT INTO roster_duties
                                   (roster_id,duty_date,employee,start_time,end_time,note)
                                   VALUES(?,?,?,?,?,?)""",
                                (rid,ds,d['employee'],d['start'],d['end'],note))
        refresh_history()

        # build PDF
        with sqlite3.connect(DB) as con:
            emp_names=[e for e, in con.execute("SELECT name FROM staff")]
        header=["Day/Name"]+emp_names+["Note"]
        totals={e:0.0 for e in emp_names}
        table=[header]

        for i in range(7):
            d=sd+datetime.timedelta(days=i); ds=d.strftime("%Y-%m-%d"); wd=d.strftime("%A")
            row=[f"{wd}, {ds}"]
            for emp in emp_names:
                seg=[x for x in roster_duties[ds] if x['employee']==emp]
                txt=""; hrs=0
                for s in seg:
                    txt+=f"{s['start']}-{s['end']}\n"
                    hrs+=(datetime.datetime.strptime(s['end'],"%H:%M")
                          -datetime.datetime.strptime(s['start'],"%H:%M")).seconds/3600
                if hrs: txt+=f"({hrs:.1f} h)"; totals[emp]+=hrs
                row.append(txt)
            row.append(special_notes.get(ds,""))
            table.append(row)
        table.append(["Weekly Total"]+[f"{totals[e]:.1f} h" for e in emp_names]+[""])

        pdf_path=os.path.abspath(os.path.join(
            ROSTERS_DIR,
            f"roster_{sd.strftime('%Y%m%d')}_{ed.strftime('%Y%m%d')}.pdf"))
        pdf_generator.generate_roster_pdf(table,filename=pdf_path)

        # preview
        pv=tk.Toplevel(); pv.title("Roster PDF")
        ttk.Label(pv,text=pdf_path,font=("Helvetica",9,"bold")
                 ).pack(padx=10,pady=10)
        bf=ttk.Frame(pv); bf.pack(pady=6)
        open_pdf = lambda : os.startfile(pdf_path) if os.name=="nt" else os.system(f'xdg-open \"{pdf_path}\"')
        print_pdf= lambda : os.startfile(pdf_path,"print") if os.name=="nt" else None
        def copy_emails():
            with sqlite3.connect(DB) as con:
                mails=",".join(e for e, in con.execute("SELECT email FROM staff"))
            pv.clipboard_clear(); pv.clipboard_append(mails)
            messagebox.showinfo("Copied",f"{len(mails.split(','))} addresses copied.")
        for txt,cmd,col in (("View",open_pdf,0),("Print",print_pdf,1),
                            ("Copy emails",copy_emails,2),("Close",pv.destroy,3)):
            ttk.Button(bf,text=txt,command=cmd).grid(row=0,column=col,padx=4)

    # hook up the top‑bar button
    finalize_btn.configure(command=finalize)

    # initial view
    start_e.set_date(datetime.date.today())
    build_week()
    start_e.bind("<<DateEntrySelected>>", lambda _ : build_week())

# ═════════════════════ password tab ════════════════════════════════════════
def init_password_tab(tab: tk.Frame):
    ttk.Label(tab,text="Current").grid(row=0,column=0,sticky="e",padx=4,pady=4)
    cur=ttk.Entry(tab,show="*"); cur.grid(row=0,column=1,padx=4)
    ttk.Label(tab,text="New").grid    (row=1,column=0,sticky="e",padx=4)
    new=ttk.Entry(tab,show="*"); new.grid(row=1,column=1,padx=4)
    ttk.Label(tab,text="Confirm").grid(row=2,column=0,sticky="e",padx=4)
    cnf=ttk.Entry(tab,show="*"); cnf.grid(row=2,column=1,padx=4)
    def change_pw():
        if new.get()!=cnf.get(): messagebox.showerror("Err","Mismatch"); return
        with sqlite3.connect(DB) as con:
            pw=con.execute("SELECT password FROM managers WHERE username=?", (current_manager,)).fetchone()
            if not pw or pw[0]!=cur.get(): messagebox.showerror("Err","Wrong current"); return
            con.execute("UPDATE managers SET password=? WHERE username=?", (new.get(),current_manager))
        messagebox.showinfo("OK","Password changed.")
        for e in (cur,new,cnf): e.delete(0,tk.END)
    ttk.Button(tab,text="Change",command=change_pw
              ).grid(row=3,column=0,columnspan=2,pady=8)

# ═════════════════════ standalone test ═════════════════════════════════════
if __name__=="__main__":
    launch_dashboard("admin")
