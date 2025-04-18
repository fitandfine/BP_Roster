"""
Dashboard – Roster Management System
------------------------------------
✓ Employee Management
✓ Roster Creation
✓ Change Password
✓ About
"""

import os, sqlite3, datetime, tkinter as tk
from   tkinter import ttk, messagebox
import pdf_generator                              # your own module

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

DAYNAMES   = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
_MIN_T     = datetime.time(5,15)    # 05:15
_MAX_T     = datetime.time(20,15)   # 20:15
TIME_OPTIONS=[]
t=datetime.datetime.combine(datetime.date(1900,1,1),_MIN_T)
end=datetime.datetime.combine(datetime.date(1900,1,1),_MAX_T)
while t<=end:
    TIME_OPTIONS.append(t.strftime("%H:%M"))
    t+=datetime.timedelta(minutes=15)

# ───────────────────────── global state ────────────────────────────────────
current_manager      = None
selected_employee_id = None

global_duties = {d: [] for d in DAYNAMES}   # weekday template
roster_duties = {}                          # concrete week (date‑keyed)
special_notes = {}                          # date → note string


# ═════════════════════════ launch ══════════════════════════════════════════
def launch_dashboard(manager_username: str):
    global current_manager
    current_manager = manager_username

    root = tk.Tk()
    root.title("Roster Dashboard BP Eltham")
    root.geometry("1050x720")

    nb   = ttk.Notebook(root); nb.pack(fill="both", expand=True, padx=8, pady=8)

    emp_tab   = ttk.Frame(nb); nb.add(emp_tab , text="Employee Management")
    rost_tab  = ttk.Frame(nb); nb.add(rost_tab, text="Roster Creation")
    pwd_tab   = ttk.Frame(nb); nb.add(pwd_tab , text="Change Password")
    
    about_tab = ttk.Frame(nb); nb.add(about_tab, text="About")

    # so employee tab can trigger live refresh of roster view
    rost_tab._refresh_week = None

    init_employee_tab(emp_tab , rost_tab)
    init_roster_tab  (rost_tab)
    init_password_tab(pwd_tab)
    help_tab = ttk.Frame(nb); nb.add(help_tab, text="Help")
    init_help_tab(help_tab)
    init_about_tab(about_tab)
    
    

   

    root.mainloop()


# ═════════════════════════ employees ═══════════════════════════════════════
def init_employee_tab(tab: tk.Frame, roster_tab_ref: tk.Frame):
    global selected_employee_id

    # form ------------------------------------------------------------------
    form = ttk.LabelFrame(tab,text="Employee Details",padding=10)
    form.grid(row=0,column=0,sticky="ew",padx=10,pady=10)

    row=0
    ttk.Label(form,text="Name").grid(row=row,column=0,sticky="e")
    name_e=ttk.Entry(form,width=30); name_e.grid(row=row,column=1,padx=4)
    row+=1
    ttk.Label(form,text="Email").grid(row=row,column=0,sticky="e")
    mail_e=ttk.Entry(form,width=30); mail_e.grid(row=row,column=1,padx=4)
    row+=1
    ttk.Label(form,text="Phone").grid(row=row,column=0,sticky="e")
    phone_e=ttk.Entry(form,width=30); phone_e.grid(row=row,column=1,padx=4)
    row+=1
    ttk.Label(form,text="Max hrs/wk").grid(row=row,column=0,sticky="e")
    max_e =ttk.Entry(form,width=30); max_e.grid(row=row,column=1,padx=4)

    # days unavailable
    row+=1
    ttk.Label(form,text="Days unavailable").grid(row=row,column=0,sticky="ne")
    dv_fr=ttk.Frame(form); dv_fr.grid(row=row,column=1,sticky="w")
    day_vars={d:tk.IntVar() for d in DAYNAMES}
    for d in DAYNAMES:
        ttk.Checkbutton(dv_fr,text=d,variable=day_vars[d]).pack(side="left",padx=2)

    # listbox ---------------------------------------------------------------
    lst_fr=ttk.LabelFrame(tab,text="Registered Employees",padding=8)
    lst_fr.grid(row=1,column=0,sticky="nsew",padx=10,pady=5)
    tab.rowconfigure(1,weight=1); tab.columnconfigure(0,weight=1)
    lb=tk.Listbox(lst_fr); lb.pack(fill="both",expand=True)

    def _refresh_list():
        lb.delete(0,tk.END)
        with sqlite3.connect(DB) as con:
            for sid,n in con.execute("SELECT staff_id,name FROM staff ORDER BY name"):
                lb.insert(tk.END,f"{sid}:{n}")
    _refresh_list()

    def _fill(_=None):
        global selected_employee_id
        sel=lb.curselection()
        if not sel: return
        sid=int(lb.get(sel[0]).split(":")[0]); selected_employee_id=sid
        with sqlite3.connect(DB) as con:
            n,e,p,m,du=con.execute("""SELECT name,email,phone_number,max_hours,days_unavailable
                                       FROM staff WHERE staff_id=?""",(sid,)).fetchone()
        for w,v in zip((name_e,mail_e,phone_e,max_e),(n,e,p,m or "")):
            w.delete(0,tk.END); w.insert(0,v)
        for v in day_vars.values(): v.set(0)
        if du:
            for d in du.split(","):
                if d.strip() in day_vars: day_vars[d.strip()].set(1)
    lb.bind("<<ListboxSelect>>",_fill)

    # helpers ---------------------------------------------------------------
    def _clear_entries():
        for w in (name_e,mail_e,phone_e,max_e): w.delete(0,tk.END)
        for v in day_vars.values(): v.set(0)

    # save / update ---------------------------------------------------------
    def _save():
        global selected_employee_id
        data=dict(
            n =name_e.get().strip(),
            e =mail_e.get().strip(),
            p =phone_e.get().strip(),
            mx=max_e.get().strip() or None,
            du=",".join([d for d,v in day_vars.items() if v.get()==1])
        )
        with sqlite3.connect(DB) as con:
            cur=con.cursor()
            if selected_employee_id:
                cur.execute("""UPDATE staff SET name=?,email=?,phone_number=?,max_hours=?,days_unavailable=?
                               WHERE staff_id=?""",(data['n'],data['e'],data['p'],data['mx'],data['du'],
                                                    selected_employee_id))
            else:
                cur.execute("""INSERT INTO staff(name,email,phone_number,max_hours,days_unavailable)
                               VALUES(?,?,?,?,?)""",(data['n'],data['e'],data['p'],data['mx'],data['du']))
        selected_employee_id=None
        _clear_entries(); _refresh_list()
        messagebox.showinfo("Saved","Employee record saved.",parent=tab)
        if roster_tab_ref._refresh_week: roster_tab_ref._refresh_week()

    ttk.Button(form,text="Add / Update",command=_save
              ).grid(row=row+1,column=0,columnspan=2,pady=6)

    # delete ---------------------------------------------------------------
    def _delete():
        sel=lb.curselection()
        if not sel:
            messagebox.showinfo("Select","Choose employee to delete.",parent=tab); return
        sid_s,nm=lb.get(sel[0]).split(":",1)
        if not messagebox.askyesno("Confirm",f"Delete {nm}?",parent=tab): return
        with sqlite3.connect(DB) as con:
            con.execute("DELETE FROM staff WHERE staff_id=?",(int(sid_s),))
        for lst in global_duties.values():
            lst[:]=[d for d in lst if d['employee']!=nm]
        _refresh_list(); _clear_entries()
        messagebox.showinfo("Deleted","Employee removed.",parent=tab)
        if roster_tab_ref._refresh_week: roster_tab_ref._refresh_week()
    ttk.Button(form,text="Delete",command=_delete
              ).grid(row=row+2,column=0,columnspan=2,pady=(2,8))

    # copy mails -----------------------------------------------------------
    def _copy():
        with sqlite3.connect(DB) as con:
            mails=",".join(e for e, in con.execute("SELECT email FROM staff"))
        tab.clipboard_clear(); tab.clipboard_append(mails)
        messagebox.showinfo("Copied",f"{len(mails.split(','))} addresses copied.",parent=tab)
    ttk.Button(tab,text="Copy ALL emails",command=_copy
              ).grid(row=2,column=0,pady=(0,10))


# ═════════════════════════ roster tab ═══════════════════════════════════════
def init_roster_tab(tab: tk.Frame):
    global global_duties, roster_duties, special_notes

    # top bar ---------------------------------------------------------------
    top=ttk.Frame(tab); top.pack(fill="x",padx=10,pady=6)
    ttk.Label(top,text="Previous").grid(row=0,column=0,sticky="e")
    prev_v=tk.StringVar()
    prev_cb=ttk.Combobox(top,textvariable=prev_v,state="readonly",width=38)
    prev_cb.grid(row=0,column=1,padx=5)

    ttk.Label(top,text="Start").grid(row=0,column=2,sticky="e")
    start_e=DateEntry(top,width=12,date_pattern="yyyy-mm-dd"); start_e.grid(row=0,column=3,padx=2)

    ttk.Label(top,text="End").grid(row=0,column=4,sticky="e")
    end_e=DateEntry(top,width=12,date_pattern="yyyy-mm-dd",state="disabled"); end_e.grid(row=0,column=5,padx=2)

    finalize_btn = ttk.Button(top,text="Finalize Roster"); finalize_btn.grid(row=0,column=6,padx=(16,2))
    start_new_btn=ttk.Button(top,text="Start New");       start_new_btn.grid(row=0,column=7)

        # ---------------------------------------------------------------
    def _refresh_hist():
        """
        Populate the 'Previous' combobox with ALL roster versions,
        even those with identical dates, using created_at timestamp to uniquely label.
        """
        with sqlite3.connect(DB) as con:
            rows = con.execute("""
                SELECT roster_id, start_date, end_date, created_at
                FROM roster
            ORDER BY created_at DESC
            """).fetchall()

        # Format: "123: 2024-04-01 → 2024-04-07 @ 2024-04-01 15:30:42"
        values = [
            f"{rid}: {sd} → {ed} @ {ts}"
            for rid, sd, ed, ts in rows
        ]

        prev_cb["values"] = values



    # main split ------------------------------------------------------------
    main=ttk.Frame(tab); main.pack(fill="both",expand=True,padx=10,pady=5)
    week_fr=ttk.LabelFrame(main,text="Week Duties"); week_fr.pack(side="left",fill="both",expand=True)
    side_fr=ttk.LabelFrame(main,text="Weekly Hours"); side_fr.pack(side="left",fill="y",padx=(6,0))
    hours_lb=tk.Listbox(side_fr,width=28); hours_lb.pack(fill="y",expand=True,padx=5,pady=5)

    day_lbs,note_entries={},{}
    _refresh_hist()

    # ----------------------------------------------------------------------
    def recalc_hours():
        hours_lb.delete(0,tk.END)
        totals={}
        for dl in roster_duties.values():
            for d in dl:
                dur=(datetime.datetime.strptime(d['end'],"%H:%M")-
                     datetime.datetime.strptime(d['start'],"%H:%M")).seconds/3600
                totals[d['employee']]=totals.get(d['employee'],0)+dur
        for emp,hrs in sorted(totals.items(),key=lambda x:x[1],reverse=True):
            hours_lb.insert(tk.END,f"{emp}: {hrs:.1f} h")

    def refresh_day(ds):
        lb=day_lbs[ds]; lb.delete(0,tk.END)
        for d in roster_duties[ds]:
            lb.insert(tk.END,f"{d['employee']} ({d['start']}-{d['end']})")
        if not roster_duties[ds]:
            lb.insert(tk.END,"(No duties)")

    def build_week():
        for w in week_fr.winfo_children(): w.destroy()
        day_lbs.clear(); note_entries.clear()
        sd=start_e.get_date()
        end_e.configure(state="normal"); end_e.set_date(sd+datetime.timedelta(days=6)); end_e.configure(state="disabled")

        for i in range(7):
            d=sd+datetime.timedelta(days=i); ds=d.strftime("%Y-%m-%d"); wd=d.strftime("%A")
            roster_duties[ds]=list(global_duties[wd]); special_notes.setdefault(ds,"")

            cell=ttk.Frame(week_fr,borderwidth=1,relief="solid",padding=4)
            cell.grid(row=i//2,column=i%2,sticky="nsew",padx=4,pady=4)
            ttk.Label(cell,text=f"{wd}, {ds}",font=("Helvetica",10,"bold")).pack(anchor="w")

            lb=tk.Listbox(cell,width=40,height=4); lb.pack(); day_lbs[ds]=lb
            refresh_day(ds)
            lb.bind("<Double-Button-1>",lambda _,d=ds: edit_duty(d))

            bf=ttk.Frame(cell); bf.pack(pady=2)
            ttk.Button(bf,text="Add",command=lambda d=ds: add_duty(d)).pack(side="left",padx=2)
            ttk.Button(bf,text="Remove",command=lambda d=ds: rm_duty(d)).pack(side="left",padx=2)

            ttk.Label(cell,text="Note:").pack(anchor="w")
            en=tk.Entry(cell,width=40); en.pack(fill="x")
            en.insert(0,special_notes[ds])
            en.bind("<FocusOut>",lambda ev,d=ds,e=en: special_notes.__setitem__(d,e.get()))
            note_entries[ds]=en
        recalc_hours()

    tab._refresh_week=build_week

    # helpers ---------------------------------------------------------------
    def _duration(a,b):
        return (datetime.datetime.strptime(b,"%H:%M")-
                datetime.datetime.strptime(a,"%H:%M")).seconds/3600

    def _total_hours(emp,delta=0):
        tot=0.0
        for lst in global_duties.values():
            for d in lst:
                if d['employee']==emp:
                    tot+=_duration(d['start'],d['end'])
        return tot+delta

    def _max_hours(emp):
        with sqlite3.connect(DB) as con:
            r=con.execute("SELECT max_hours FROM staff WHERE name=?",(emp,)).fetchone()
        try: return float(r[0]) if r and r[0] else None
        except: return None

    def available_staff(wd):
        with sqlite3.connect(DB) as con:
            return [n for n,du in con.execute("SELECT name,days_unavailable FROM staff")
                    if not du or wd not in du.split(",")]

    # duty crud -------------------------------------------------------------
    def add_duty(ds):
        wd=datetime.datetime.strptime(ds,"%Y-%m-%d").strftime("%A")
        av=available_staff(wd)
        if not av: messagebox.showinfo("Info",f"No staff available on {wd}.",parent=tab); return
        w=tk.Toplevel(); w.title("Add Duty"); w.grab_set()
        emp=tk.StringVar(value=av[0]); st=tk.StringVar(value=TIME_OPTIONS[0]); et=tk.StringVar(value=TIME_OPTIONS[-1])
        ttk.Label(w,text="Employee").grid(row=0,column=0,sticky='e')
        ttk.Combobox(w,values=av,textvariable=emp,state="readonly").grid(row=0,column=1,padx=4,pady=2)
        ttk.Label(w,text="Start").grid(row=1,column=0,sticky='e')
        ttk.Combobox(w,values=TIME_OPTIONS,textvariable=st,width=8).grid(row=1,column=1)
        ttk.Label(w,text="End").grid(row=2,column=0,sticky='e')
        ttk.Combobox(w,values=TIME_OPTIONS,textvariable=et,width=8).grid(row=2,column=1)

        def sv():
            s,e=st.get(),et.get()
            if (s not in TIME_OPTIONS) or (e not in TIME_OPTIONS):
                messagebox.showerror("Err","Time outside 05:15–20:15",parent=w); return
            if datetime.datetime.strptime(e,"%H:%M")<=datetime.datetime.strptime(s,"%H:%M"):
                messagebox.showerror("Err","End must be after Start",parent=w); return
            dur=_duration(s,e)
            mx=_max_hours(emp.get())
            if mx and _total_hours(emp.get(),dur)>mx:
                messagebox.showwarning("Max hours exceeded",
                    f"{emp.get()} would have more than {mx:.1f} h.\n"
                    "Change Max hrs in Employee tab if needed.",
                    parent=w)
            global_duties[wd].append({"employee":emp.get(),"start":s,"end":e})
            build_week(); w.destroy()
        ttk.Button(w,text="Save",command=sv).grid(row=3,column=0,columnspan=2,pady=6)

    def edit_duty(ds):
        lb=day_lbs[ds]; sel=lb.curselection()
        if not sel: return
        idx=sel[0]; duty=roster_duties[ds][idx]
        wd=datetime.datetime.strptime(ds,"%Y-%m-%d").strftime("%A")
        av=available_staff(wd)
        w=tk.Toplevel(); w.title("Edit Duty"); w.grab_set()
        emp=tk.StringVar(value=duty['employee']); st=tk.StringVar(value=duty['start']); et=tk.StringVar(value=duty['end'])
        ttk.Label(w,text="Employee").grid(row=0,column=0,sticky='e')
        ttk.Combobox(w,values=av,textvariable=emp,state="readonly").grid(row=0,column=1,padx=4,pady=2)
        ttk.Label(w,text="Start").grid(row=1,column=0,sticky='e')
        ttk.Combobox(w,values=TIME_OPTIONS,textvariable=st,width=8).grid(row=1,column=1)
        ttk.Label(w,text="End").grid(row=2,column=0,sticky='e')
        ttk.Combobox(w,values=TIME_OPTIONS,textvariable=et,width=8).grid(row=2,column=1)

        def sv():
            s,e=st.get(),et.get()
            if (s not in TIME_OPTIONS) or (e not in TIME_OPTIONS):
                messagebox.showerror("Err","Time outside 05:15–20:15",parent=w); return
            if datetime.datetime.strptime(e,"%H:%M")<=datetime.datetime.strptime(s,"%H:%M"):
                messagebox.showerror("Err","End must be after Start",parent=w); return
            delta=_duration(s,e)-_duration(duty['start'],duty['end'])
            mx=_max_hours(emp.get())
            if mx and _total_hours(emp.get(),delta)>mx:
                messagebox.showwarning("Max hours exceeded",
                    f"{emp.get()} would have more than {mx:.1f} h.\n"
                    "Change Max hrs in Employee tab if needed.",
                    parent=w)
            duty.update(employee=emp.get(),start=s,end=e); global_duties[wd][idx]=duty.copy()
            build_week(); w.destroy()
        ttk.Button(w,text="Save",command=sv).grid(row=3,column=0,columnspan=2,pady=6)

    def rm_duty(ds):
        lb=day_lbs[ds]; sel=lb.curselection()
        if sel:
            wd=datetime.datetime.strptime(ds,"%Y-%m-%d").strftime("%A")
            global_duties[wd].pop(sel[0]); build_week()

    # start new -------------------------------------------------------------
    def start_new():
        for v in global_duties.values(): v.clear()
        roster_duties.clear(); special_notes.clear()
        build_week()
    start_new_btn.configure(command=start_new)

    # load previous ---------------------------------------------------------
        # ── load previous roster (now guaranteed to bring in ONLY the rows that
    #    belong to the selected roster_id – even if several rosters were
    #    created for the same start / end date) ────────────────────────────
    def load_prev(_=None):
        sel = prev_v.get()
        if not sel:                                  # nothing selected
            return

        try:
            rid = int(sel.split(":")[0].strip())
        except ValueError:
            messagebox.showerror("Error", "Failed to parse selected roster ID.")
            return


        # 1) completely reset every in‑memory container  ───────────────────
        #    (re‑creating the dict avoids “dangling” list references that
        #     were the real cause of the duplicated lines seen on screen)
        global global_duties, roster_duties, special_notes
        global_duties  = {d: [] for d in DAYNAMES}
        roster_duties.clear()
        special_notes.clear()

        # 2) pull duties / notes only for THAT roster_id  ──────────────────
        with sqlite3.connect(DB) as con:
            cur   = con.cursor()
            rows  = cur.execute("""
                    SELECT duty_date, employee, start_time, end_time, note
                      FROM roster_duties
                     WHERE roster_id = ?""", (rid,)).fetchall()

            sd_s, ed_s = cur.execute("""
                    SELECT start_date, end_date
                      FROM roster
                     WHERE roster_id = ?""", (rid,)).fetchone()

        # 3) copy the rows into the weekday template (no cross‑pollination)
        seen = set()
        for ds, emp, st, et, note in rows:
            key = (ds, emp, st, et)
            if key in seen:               # safeguard against accidental dupes
                continue
            seen.add(key)

            wd = datetime.datetime.strptime(ds, "%Y-%m-%d").strftime("%A")
            global_duties[wd].append(
                {"employee": emp, "start": st, "end": et}
            )
            special_notes[ds] = note or ""

        # 4) re‑display the selected week
        start_e.set_date(datetime.datetime.strptime(sd_s, "%Y-%m-%d").date())
        end_e.configure(state="normal")
        end_e.set_date(start_e.get_date() + datetime.timedelta(days=6))
        end_e.configure(state="disabled")

        build_week()

        # 5) restore the notes in their entry boxes
        for ds, txt in special_notes.items():
            if ds in note_entries:
                note_entries[ds].delete(0, tk.END)
                note_entries[ds].insert(0, txt)

    prev_cb.bind("<<ComboboxSelected>>", load_prev)


    # finalize --------------------------------------------------------------
    def finalize():
        # Prevent duplicate finalize calls in rapid clicks
        finalize_btn.configure(state="disabled")
        tab.after(3000, lambda: finalize_btn.configure(state="normal"))  # Re-enable after 3s

        # Check if this roster (same duties + notes) is already saved
        with sqlite3.connect(DB) as con:
            existing_rows = con.execute("""
                SELECT duty_date, employee, start_time, end_time
                FROM roster_duties
                WHERE roster_id = (SELECT MAX(roster_id) FROM roster)
            """).fetchall()

            current_rows = []
            for ds, dl in roster_duties.items():
                for d in dl:
                    current_rows.append((ds, d['employee'], d['start'], d['end']))

            if set(existing_rows) == set(current_rows):
                messagebox.showinfo("Duplicate Detected", "This roster already exists. Not saving again.")
                return

        for ds,en in note_entries.items(): special_notes[ds]=en.get()
        sd=start_e.get_date(); ed=end_e.get_date()
        sd_s,ed_s=sd.strftime("%Y-%m-%d"),ed.strftime("%Y-%m-%d")
        with sqlite3.connect(DB) as con:
            cur=con.cursor()
            cur.execute("INSERT INTO roster(start_date,end_date,pdf_file) VALUES(?,?,?)",(sd_s,ed_s,""))
            rid=cur.lastrowid
            for ds,dl in roster_duties.items():
                note=special_notes.get(ds,"")
                for d in dl:
                    cur.execute("""INSERT INTO roster_duties
                                   (roster_id,duty_date,employee,start_time,end_time,note)
                                   VALUES(?,?,?,?,?,?)""",(rid,ds,d['employee'],d['start'],d['end'],note))
        _refresh_hist()

        # pdf ----------------------------------------------------------------
        with sqlite3.connect(DB) as con:
            emp_names=[e for e, in con.execute("SELECT name FROM staff")]
        header=["Day/Name"]+emp_names+["Note"]; totals={e:0.0 for e in emp_names}; table=[header]
        for i in range(7):
            d=sd+datetime.timedelta(days=i); ds=d.strftime("%Y-%m-%d"); wd=d.strftime("%A")
            row=[f"{wd}, {ds}"]
            for emp in emp_names:
                seg=[x for x in roster_duties[ds] if x['employee']==emp]
                txt=""; hrs=0
                for s in seg:
                    txt+=f"{s['start']}-{s['end']}\n"
                    hrs+=_duration(s['start'],s['end'])
                if hrs: txt+=f"({hrs:.1f} h)"; totals[emp]+=hrs
                row.append(txt)
            row.append(special_notes.get(ds,"")); table.append(row)
        table.append(["Weekly Total"]+[f"{totals[e]:.1f} h" for e in emp_names]+[""])

        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        pdf_path = os.path.abspath(os.path.join(
            ROSTERS_DIR, f"roster_{timestamp}.pdf"))

        title_line=f"Roster for BP Eltham from {sd_s} to {ed_s}"
        # try title kw, fall back if pdf_generator doesn't accept it
        try:
            pdf_generator.generate_roster_pdf(table,filename=pdf_path,title=title_line)
        except TypeError:
            pdf_generator.generate_roster_pdf(table,filename=pdf_path)

        # popup -------------------------------------------------------------
        pv=tk.Toplevel(); pv.title("Roster PDF")
        ttk.Label(pv,text=pdf_path,font=("Helvetica",9,"bold")).pack(padx=10,pady=10)
        bf=ttk.Frame(pv); bf.pack(pady=6)
        open_pdf=lambda: os.startfile(pdf_path) if os.name=="nt" else os.system(f'xdg-open \"{pdf_path}\"')
        def copy_mails():
            with sqlite3.connect(DB) as con:
                mails=",".join(e for e, in con.execute("SELECT email FROM staff"))
            pv.clipboard_clear(); pv.clipboard_append(mails)
            messagebox.showinfo("Copied",f"{len(mails.split(','))} addresses copied.",parent=pv)
        def open_folder():
            os.startfile(os.path.abspath(ROSTERS_DIR)) if os.name=="nt" else os.system(f'xdg-open \"{ROSTERS_DIR}\"')

        for txt,cmd,col in (("View",open_pdf,0),
                            ("Copy emails",copy_mails,1),
                            ("Open folder",open_folder,2),
                            ("Close",pv.destroy,3)):
            ttk.Button(bf,text=txt,command=cmd).grid(row=0,column=col,padx=4)

    finalize_btn.configure(command=finalize)

    # first draw
    start_e.set_date(datetime.date.today()); build_week()
    start_e.bind("<<DateEntrySelected>>",lambda _ : build_week())


# ═════════════════════ password tab ════════════════════════════════════════
def init_password_tab(tab: tk.Frame):
    ttk.Label(tab,text="Current").grid(row=0,column=0,sticky="e",padx=4,pady=4)
    cur=ttk.Entry(tab,show="*"); cur.grid(row=0,column=1,padx=4)
    ttk.Label(tab,text="New").grid    (row=1,column=0,sticky="e",padx=4)
    new=ttk.Entry(tab,show="*"); new.grid(row=1,column=1,padx=4)
    ttk.Label(tab,text="Confirm").grid(row=2,column=0,sticky="e",padx=4)
    cnf=ttk.Entry(tab,show="*"); cnf.grid(row=2,column=1,padx=4)
    def chg():
        if new.get()!=cnf.get():
            messagebox.showerror("Err","Mismatch",parent=tab); return
        with sqlite3.connect(DB) as con:
            pw=con.execute("SELECT password FROM managers WHERE username=?", (current_manager,)).fetchone()
            if not pw or pw[0]!=cur.get():
                messagebox.showerror("Err","Wrong current",parent=tab); return
            con.execute("UPDATE managers SET password=? WHERE username=?", (new.get(),current_manager))
        messagebox.showinfo("OK","Password changed.",parent=tab)
        for e in (cur,new,cnf): e.delete(0,tk.END)
    ttk.Button(tab,text="Change",command=chg).grid(row=3,column=0,columnspan=2,pady=8)


# ═════════════════════ help tab (User Manual) ════════════════════════════════════════════
def init_help_tab(tab: tk.Frame):
    help_text = """
📘 Roster Management System – User Manual

🔹 Main Features:
- Manage employees (add, update, delete)
- Create new weekly rosters
- View/edit previously created rosters
- Export rosters to PDF with automatic summaries
- Add daily special notes for each day
- View employee workload summary
- Change admin password

───────────────────────────────────────
👤 Employee Management Tab:
- Use the form to enter employee name, email, phone, weekly hour limit, and unavailable days.
- Press 'Add / Update' to save or update employee records.
- Select an employee from the list and press 'Delete' to remove them.
- 'Copy ALL emails' lets you copy all staff emails at once for quick use.

📅 Roster Creation Tab:
- Use the start date picker to define the week. The end date auto-fills.
- View and assign staff duties per day using the 'Add' button. You can also 'Edit' or 'Remove'.
- Notes can be added for each day.
- Press 'Finalize Roster' to save and generate a PDF. The file is auto-timestamped to avoid overwrites.
- Use the 'Previous' dropdown to load any saved roster (even if the dates are same – timestamp is used).

🔑 Change Password Tab:
- Change the current admin password after validating the current one.

🆘 Help Tab:
- Shows this user manual.

ℹ️ About Tab:
- Shows contact and author information with clickable URL and phone number.

──────────────
🔒 Security Tip:
Use unique and strong passwords for your admin account.
"""
    text_box = tk.Text(tab, wrap="word", font=("Consolas", 10), padx=10, pady=10)
    text_box.insert("1.0", help_text)
    text_box.configure(state="disabled")
    text_box.pack(fill="both", expand=True)



# ═════════════════════ about tab (Updated, no popups) ════════════════════════════════════
def init_about_tab(tab: tk.Frame):
    about_text = (
        "👨‍💻 Developed by Anup Chapain for BP Eltham, Taranaki\n\n"
        "🌐 Website:\nhttps://fitandfine.github.io/anup\n\n"
        "📧 Email:\nemailofanup@gmail.com\n\n"
        "📞 Phone:\n0273276110"
    )

    lbl = tk.Label(tab, text=about_text, justify="left", anchor="nw", font=("Segoe UI", 10), fg="#0000ee", cursor="hand2")
    lbl.pack(padx=10, pady=10, anchor="nw")

    def open_url(event):
        import webbrowser
        webbrowser.open("https://fitandfine.github.io/anup")

    lbl.bind("<Button-1>", open_url)



# ═════════════════════ standalone test ═════════════════════════════════════
if __name__=="__main__":
    launch_dashboard("admin")
