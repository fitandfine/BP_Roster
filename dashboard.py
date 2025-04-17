"""
Dashboard for the Roster Management System
==========================================

Tabs
----
1. Employee Management
2. Roster Creation  (load‑previous, dynamic week, live hours, duty add/edit/remove,
                     special notes column, PDF preview/email/print)
3. Change Password

Deps
----
pip install tkcalendar
(plus your own pdf_generator and email_sender modules)
"""

import os, sqlite3, datetime, tkinter as tk
from tkinter import ttk, messagebox
import pdf_generator, email_sender

# --------------------------------------------------------------------------- #
#  1 ── basic helpers / globals                                               #
# --------------------------------------------------------------------------- #
try:
    from tkcalendar import DateEntry
except ImportError:
    messagebox.showerror("Dependency Missing",
                         "tkcalendar not installed.\n> pip install tkcalendar")
    raise

DB_PATH      = "roster.db"
ROSTERS_DIR  = "Rosters"
os.makedirs(ROSTERS_DIR, exist_ok=True)

current_manager     : str  = None          # set by login‑flow
selected_employee_id: int  = None          # editing helper

#   weekday‑template that holds *all* duties defined for a weekday
global_duties = {d: [] for d in
                 ["Sunday","Monday","Tuesday","Wednesday",
                  "Thursday","Friday","Saturday"]}
#   concrete week view:  YYYY‑MM‑DD  →  list[duty]
roster_duties = {}
#   special note for each concrete day (in current week view)
special_notes = {}

# HH:MM options every 15 min
def time_options():
    out, t = [], datetime.datetime.strptime("00:00","%H:%M")
    while t.day == 1:
        out.append(t.strftime("%H:%M"))
        t += datetime.timedelta(minutes=15)
    return out
TIME_OPTIONS = time_options()

# --------------------------------------------------------------------------- #
#  2 ── main app launcher                                                     #
# --------------------------------------------------------------------------- #
def launch_dashboard(manager_username:str):
    global current_manager
    current_manager = manager_username

    root = tk.Tk()
    root.title("Roster Management Dashboard")
    root.geometry("1050x720")

    nb = ttk.Notebook(root); nb.pack(expand=True, fill="both", padx=8, pady=8)

    emp_tab    = ttk.Frame(nb); nb.add(emp_tab,    text="Employee Management")
    roster_tab = ttk.Frame(nb); nb.add(roster_tab, text="Roster Creation")
    pass_tab   = ttk.Frame(nb); nb.add(pass_tab,   text="Change Password")

    init_employee_tab(emp_tab)
    init_roster_tab  (roster_tab)
    init_password_tab(pass_tab)

    root.mainloop()

# --------------------------------------------------------------------------- #
#  3 ── EMPLOYEE MANAGEMENT TAB                                               #
# --------------------------------------------------------------------------- #
def init_employee_tab(frame:tk.Frame):
    global selected_employee_id

    # ── form ────────────────────────────────────────────────────────────────
    f = ttk.LabelFrame(frame, text="Employee Details", padding=10)
    f.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

    row=0
    ttk.Label(f,text="Name").grid         (row=row, column=0, sticky="e", padx=5, pady=3)
    name_e  = ttk.Entry(f, width=30); name_e.grid (row=row, column=1, padx=5)

    row+=1
    ttk.Label(f,text="Email").grid        (row=row, column=0, sticky="e", padx=5, pady=3)
    email_e = ttk.Entry(f, width=30); email_e.grid(row=row, column=1, padx=5)

    row+=1
    ttk.Label(f,text="Phone").grid        (row=row, column=0, sticky="e", padx=5, pady=3)
    phone_e = ttk.Entry(f, width=30); phone_e.grid(row=row, column=1, padx=5)

    row+=1
    ttk.Label(f,text="Max hrs / week").grid(row=row, column=0, sticky="e", padx=5, pady=3)
    maxhrs_e= ttk.Entry(f, width=30); maxhrs_e.grid(row=row, column=1, padx=5)

    # days unavailable (check‑boxes)
    row+=1
    ttk.Label(f,text="Days Unavailable").grid(row=row, column=0, sticky="ne", padx=5, pady=3)
    days_frame = ttk.Frame(f); days_frame.grid(row=row, column=1, sticky="w")
    DAYNAMES = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
    day_vars  = {d: tk.IntVar() for d in DAYNAMES}
    for d in DAYNAMES:
        ttk.Checkbutton(days_frame,text=d,variable=day_vars[d]
                       ).pack(side="left", padx=2)

    # ── list ────────────────────────────────────────────────────────────────
    list_fr = ttk.LabelFrame(frame, text="Registered Employees", padding=8)
    list_fr.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
    frame.rowconfigure(1, weight=1); frame.columnconfigure(0, weight=1)

    emp_list = tk.Listbox(list_fr); emp_list.pack(expand=True, fill="both")
    def refresh_list():
        emp_list.delete(0,tk.END)
        with sqlite3.connect(DB_PATH) as con:
            for sid,name in con.execute("SELECT staff_id,name FROM staff ORDER BY name"):
                emp_list.insert(tk.END, f"{sid}:{name}")
    refresh_list()

    def fill_form(event=None):
        global selected_employee_id
        sel = emp_list.curselection()
        if not sel: return
        sid = int(emp_list.get(sel[0]).split(":")[0])
        selected_employee_id=sid
        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            cur.execute("""SELECT name,email,phone_number,max_hours,days_unavailable
                           FROM staff WHERE staff_id=?""",(sid,))
            n,e,p,mh,du = cur.fetchone()
        name_e.delete (0,tk.END); name_e.insert (0,n)
        email_e.delete(0,tk.END); email_e.insert(0,e)
        phone_e.delete(0,tk.END); phone_e.insert(0,p)
        maxhrs_e.delete(0,tk.END); maxhrs_e.insert(0,mh or "")
        for d in DAYNAMES: day_vars[d].set(0)
        if du:
            for d in du.split(","): day_vars[d.strip()].set(1)
    emp_list.bind("<<ListboxSelect>>", fill_form)

    # ── save / update ───────────────────────────────────────────────────────
    def save_emp():
        global selected_employee_id
        vals = { "name":  name_e.get().strip(),
                 "email": email_e.get().strip(),
                 "phone": phone_e.get().strip(),
                 "maxh":  maxhrs_e.get().strip() or None,
                 "du":    ",".join([d for d,v in day_vars.items() if v.get()==1]) }
        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            if selected_employee_id:
                cur.execute("""UPDATE staff
                               SET name=?,email=?,phone_number=?,max_hours=?,days_unavailable=?
                               WHERE staff_id=?""",
                            (vals["name"],vals["email"],vals["phone"],
                             vals["maxh"],vals["du"], selected_employee_id))
            else:
                cur.execute("""INSERT INTO staff(name,email,phone_number,max_hours,days_unavailable)
                               VALUES(?,?,?,?,?)""",
                            (vals["name"],vals["email"],vals["phone"],vals["maxh"],vals["du"]))
        selected_employee_id=None
        for e in (name_e,email_e,phone_e,maxhrs_e): e.delete(0,tk.END)
        for v in day_vars.values(): v.set(0)
        refresh_list()
        messagebox.showinfo("Saved","Employee record saved.")

    ttk.Button(f,text="Add / Update Employee", command=save_emp
              ).grid(row=row+1, column=0, columnspan=2, pady=8)

# --------------------------------------------------------------------------- #
#  4 ── ROSTER CREATION TAB                                                   #
# --------------------------------------------------------------------------- #
def init_roster_tab(frame:tk.Frame):
    global roster_duties, global_duties, special_notes

    # ── top bar : previous roster selector + date range ─────────────────────
    top = ttk.Frame(frame); top.pack(fill="x", padx=10, pady=5)

    ttk.Label(top,text="Load Previous Roster").grid(row=0,column=0,sticky="e")
    prev_var  = tk.StringVar()
    prev_combo= ttk.Combobox(top,textvariable=prev_var,width=35,state="readonly")
    prev_combo.grid(row=0,column=1,padx=5)

    ttk.Label(top,text="Start").grid(row=0,column=2,sticky="e")
    start_e = DateEntry(top,width=12,date_pattern="yyyy-mm-dd"); start_e.grid(row=0,column=3,padx=3)
    ttk.Label(top,text="End").grid(row=0,column=4,sticky="e")
    end_e   = DateEntry(top,width=12,date_pattern="yyyy-mm-dd");   end_e.grid  (row=0,column=5,padx=3)

    def populate_history():
        with sqlite3.connect(DB_PATH) as con:
            rows = con.execute("""SELECT roster_id,start_date,end_date
                                  FROM roster ORDER BY roster_id DESC""").fetchall()
        prev_combo["values"]=[f"{r[0]}: {r[1]} → {r[2]}" for r in rows]
    populate_history()

    # ── main split : week grid + sidebar ────────────────────────────────────
    main = ttk.Frame(frame); main.pack(expand=True,fill="both", padx=10, pady=5)
    week_fr = ttk.LabelFrame(main,text="Week Duties"); week_fr.pack(side="left",expand=True,fill="both")
    side_fr = ttk.LabelFrame(main,text="Hours / Notes"); side_fr.pack(side="left",fill="y",padx=(5,0))

    hours_lb = tk.Listbox(side_fr,width=28); hours_lb.pack(expand=True,fill="y",padx=5,pady=5)
    notes_container = ttk.Frame(side_fr); notes_container.pack(fill="x",padx=5)

    day_lbs = {}   # concrete‑day listboxes (for refresh)

    # ---------- helper ----------------------------------------------------- #
    def refresh_hours():
        hours_lb.delete(0,tk.END)
        with sqlite3.connect(DB_PATH) as con:
            emps=[r[0] for r in con.execute("SELECT name FROM staff")]
        totals={e:0.0 for e in emps}
        for duties in global_duties.values():
            for d in duties:
                dur=(datetime.datetime.strptime(d["end"],"%H:%M")
                     -datetime.datetime.strptime(d["start"],"%H:%M")).seconds/3600.0
                totals[d["employee"]]+=dur
        for e in emps:
            hours_lb.insert(tk.END,f"{e}: {totals[e]:.1f} hr")

    def refresh_day(ds):
        lb=day_lbs[ds]; lb.delete(0,tk.END)
        items=roster_duties.get(ds,[])
        if not items: lb.insert(tk.END,"(No duties)")
        for it in items:
            lb.insert(tk.END,f"{it['employee']} ({it['start']}-{it['end']})")

    # ---------- build / rebuild week view ---------------------------------- #
    def build_week():
        for w in week_fr.winfo_children(): w.destroy()
        for w in notes_container.winfo_children(): w.destroy()
        day_lbs.clear(); special_notes.clear()

        sd=start_e.get_date(); end_e.set_date(sd+datetime.timedelta(days=6))

        for i in range(7):
            d = sd+datetime.timedelta(days=i)
            ds=d.strftime("%Y-%m-%d"); wd=d.strftime("%A")
            roster_duties[ds]=list(global_duties[wd])  # copy
            special_notes[ds]=""

            cell=ttk.Frame(week_fr,borderwidth=1,relief="solid",padding=4)
            cell.grid(row=i//2,column=i%2,sticky="nsew",padx=4,pady=4)
            ttk.Label(cell,text=f"{wd}, {ds}",font=("Helvetica",10,"bold")).pack(anchor="w")

            lb=tk.Listbox(cell,width=40,height=4); lb.pack()
            day_lbs[ds]=lb; refresh_day(ds)
            lb.bind("<Double-Button-1>",lambda e,ds=ds: edit_duty(ds))

            bf=ttk.Frame(cell); bf.pack(pady=3)
            ttk.Button(bf,text="Add",
                       command=lambda ds=ds: add_duty(ds)).pack(side="left",padx=2)
            ttk.Button(bf,text="Remove",
                       command=lambda ds=ds: remove_duty(ds)).pack(side="left",padx=2)

            # note input line in sidebar
            nt=tk.Entry(notes_container,width=26)
            nt.pack(fill="x",pady=1)
            nt.insert(0,"")  # blank
            def save_note(ev,ds=ds,e=nt): special_notes[ds]=e.get()
            nt.bind("<FocusOut>",save_note)

        refresh_hours()

    # ---------- add / Edit / remove duties --------------------------------- #
    def _available_employee_list(wday):
        with sqlite3.connect(DB_PATH) as con:
            rows=con.execute("SELECT name,days_unavailable FROM staff").fetchall()
        return [n for n,du in rows if not du or wday not in du.split(",")]

    def add_duty(ds):
        wday=datetime.datetime.strptime(ds,"%Y-%m-%d").strftime("%A")
        avail=_available_employee_list(wday)
        if not avail:
            messagebox.showinfo("Info",f"No employees available on {wday}."); return
        win=tk.Toplevel(); win.title(f"Add ({ds})"); win.grab_set()

        ttk.Label(win,text="Employee").grid(row=0,column=0,padx=5,pady=4,sticky="e")
        emp_var=tk.StringVar(value=avail[0])
        ttk.Combobox(win,textvariable=emp_var,values=avail,state="readonly"
                    ).grid(row=0,column=1,padx=5,pady=4)

        ttk.Label(win,text="Start").grid(row=1,column=0,sticky="e")
        st_var=tk.StringVar(value="09:00")
        ttk.Combobox(win,textvariable=st_var,values=TIME_OPTIONS,width=8
                    ).grid(row=1,column=1)

        ttk.Label(win,text="End").grid(row=2,column=0,sticky="e")
        et_var=tk.StringVar(value="17:00")
        ttk.Combobox(win,textvariable=et_var,values=TIME_OPTIONS,width=8
                    ).grid(row=2,column=1)

        def save():
            s,e=st_var.get(),et_var.get()
            if datetime.datetime.strptime(e,"%H:%M")<=datetime.datetime.strptime(s,"%H:%M"):
                messagebox.showerror("Error","End must be after Start"); return
            global_duties[wday].append({"employee":emp_var.get(),"start":s,"end":e})
            build_week(); win.destroy()
        ttk.Button(win,text="Save",command=save).grid(row=3,column=0,columnspan=2,pady=6)

    def edit_duty(ds):
        lb=day_lbs[ds]; sel=lb.curselection()
        if not sel: return
        idx=sel[0]
        duty=roster_duties[ds][idx]
        wday=datetime.datetime.strptime(ds,"%Y-%m-%d").strftime("%A")
        avail=_available_employee_list(wday)
        win=tk.Toplevel(); win.title(f"Edit ({ds})"); win.grab_set()

        emp_var=tk.StringVar(value=duty["employee"])
        st_var=tk.StringVar(value=duty["start"])
        et_var=tk.StringVar(value=duty["end"])

        ttk.Label(win,text="Employee").grid(row=0,column=0,padx=5,pady=4,sticky="e")
        ttk.Combobox(win,textvariable=emp_var,values=avail,state="readonly"
                    ).grid(row=0,column=1,padx=5,pady=4)
        ttk.Label(win,text="Start").grid(row=1,column=0,sticky="e")
        ttk.Combobox(win,textvariable=st_var,values=TIME_OPTIONS,width=8
                    ).grid(row=1,column=1)
        ttk.Label(win,text="End").grid(row=2,column=0,sticky="e")
        ttk.Combobox(win,textvariable=et_var,values=TIME_OPTIONS,width=8
                    ).grid(row=2,column=1)

        def save():
            s,e=st_var.get(),et_var.get()
            if datetime.datetime.strptime(e,"%H:%M")<=datetime.datetime.strptime(s,"%H:%M"):
                messagebox.showerror("Error","End must be after Start"); return
            duty.update(employee=emp_var.get(),start=s,end=e)
            global_duties[wday][idx]=duty.copy()
            build_week(); win.destroy()
        ttk.Button(win,text="Save",command=save).grid(row=3,column=0,columnspan=2,pady=6)

    def remove_duty(ds):
        lb=day_lbs[ds]; sel=lb.curselection()
        if not sel: return
        wday=datetime.datetime.strptime(ds,"%Y-%m-%d").strftime("%A")
        global_duties[wday].pop(sel[0])
        build_week()

    # ---------- load previous roster --------------------------------------- #
    def load_prev(event=None):
        sel=prev_var.get()
        if not sel: return
        rid=int(sel.split(":")[0])
        for lst in global_duties.values(): lst.clear()
        with sqlite3.connect(DB_PATH) as con:
            cur=con.cursor()
            cur.execute("""SELECT duty_date,employee,start_time,end_time,note
                           FROM roster_duties WHERE roster_id=?""",(rid,))
            for ds,emp,st,et,note in cur.fetchall():
                wd=datetime.datetime.strptime(ds,"%Y-%m-%d").strftime("%A")
                global_duties[wd].append({"employee":emp,"start":st,"end":et})
                special_notes[ds]=note or ""
            cur.execute("SELECT start_date,end_date FROM roster WHERE roster_id=?", (rid,))
            sd,ed=cur.fetchone()
        start_e.set_date(datetime.datetime.strptime(sd,"%Y-%m-%d").date())
        end_e.set_date  (datetime.datetime.strptime(ed,"%Y-%m-%d").date())
        build_week()
        # re‑inject notes text boxes
        for ds, txt in special_notes.items():
            if ds in notes_container.children:
                notes_container.children[ds].delete(0,tk.END)
                notes_container.children[ds].insert(0,txt)
    prev_combo.bind("<<ComboboxSelected>>", load_prev)

    # ---------- finalize & generate pdf ------------------------------------ #
    def finalize():
        sd=start_e.get_date(); ed=end_e.get_date()
        sd_s,ed_s=sd.strftime("%Y-%m-%d"),ed.strftime("%Y-%m-%d")
        with sqlite3.connect(DB_PATH) as con:
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
                                (rid,ds,d["employee"],d["start"],d["end"],note))
        populate_history()

        # build PDF table
        with sqlite3.connect(DB_PATH) as con:
            emp_names=[r[0] for r in con.execute("SELECT name FROM staff")]
        header=["Day/Name"]+emp_names+["Note"]
        totals={e:0.0 for e in emp_names}
        table=[header]
        for i in range(7):
            d=sd+datetime.timedelta(days=i)
            ds=d.strftime("%Y-%m-%d"); wd=d.strftime("%A")
            row=[f"{wd}, {ds}"]
            for emp in emp_names:
                seg=[x for x in roster_duties[ds] if x['employee']==emp]
                text=""; day_sum=0.0
                for s in seg:
                    text+=f"{s['start']}-{s['end']}\n"
                    day_sum+=(datetime.datetime.strptime(s['end'],"%H:%M")
                              -datetime.datetime.strptime(s['start'],"%H:%M")).seconds/3600
                if day_sum: text+=f"({day_sum:.1f} hr)"
                totals[emp]+=day_sum
                row.append(text)
            row.append(special_notes.get(ds,""))
            table.append(row)
        table.append(["Weekly Total"]+[f"{totals[e]:.1f} hr" for e in emp_names]+[""])

        pdf_path=f"{ROSTERS_DIR}/roster_{sd.strftime('%Y%m%d')}_{ed.strftime('%Y%m%d')}.pdf"
        pdf_generator.generate_roster_pdf(table,filename=pdf_path)

        # preview window
        pv=tk.Toplevel(); pv.title("Roster PDF")
        ttk.Label(pv,text=f"Saved: {pdf_path}",font=("Helvetica",9,"bold")
                 ).pack(padx=10,pady=10)
        bf=ttk.Frame(pv); bf.pack(pady=6)
        def _view():  os.startfile(pdf_path) if os.name=="nt" else os.system(f'xdg-open "{pdf_path}"')
        def _print(): os.startfile(pdf_path,"print") if os.name=="nt" else None
        def _email():
            with sqlite3.connect(DB_PATH) as con:
                emails=[r[0] for r in con.execute("SELECT email FROM staff")]
            email_sender.open_email_client(emails,
                f"Roster {sd_s} to {ed_s}","See attached roster",attachment_path=pdf_path)
        ttk.Button(bf,text="View", command=_view ).grid(row=0,column=0,padx=4)
        ttk.Button(bf,text="Print",command=_print).grid(row=0,column=1,padx=4)
        ttk.Button(bf,text="Email",command=_email).grid(row=0,column=2,padx=4)
        ttk.Button(bf,text="Close",command=pv.destroy).grid(row=0,column=3,padx=4)

    ttk.Button(frame,text="Finalize Roster",command=finalize
              ).pack(side="bottom",fill="x", padx=10, pady=8)

    # first build
    start_e.set_date(datetime.date.today())
    build_week()
    start_e.bind("<<DateEntrySelected>>", lambda e: build_week())

# --------------------------------------------------------------------------- #
#  5 ── CHANGE PASSWORD TAB                                                   #
# --------------------------------------------------------------------------- #
def init_password_tab(frame:tk.Frame):
    ttk.Label(frame,text="Current").grid(row=0,column=0,sticky="e",padx=5,pady=4)
    cur_e=ttk.Entry(frame,show="*"); cur_e.grid(row=0,column=1,padx=5)
    ttk.Label(frame,text="New").grid    (row=1,column=0,sticky="e",padx=5)
    new_e=ttk.Entry(frame,show="*"); new_e.grid(row=1,column=1,padx=5)
    ttk.Label(frame,text="Confirm").grid(row=2,column=0,sticky="e",padx=5)
    conf_e=ttk.Entry(frame,show="*"); conf_e.grid(row=2,column=1,padx=5)

    def change_pw():
        cur,new,cf=cur_e.get(),new_e.get(),conf_e.get()
        if new!=cf: messagebox.showerror("Err","Mismatch"); return
        with sqlite3.connect(DB_PATH) as con:
            pw=con.execute("SELECT password FROM managers WHERE username=?",
                           (current_manager,)).fetchone()
            if not pw or pw[0]!=cur:
                messagebox.showerror("Err","Wrong current"); return
            con.execute("UPDATE managers SET password=? WHERE username=?", (new,current_manager))
            messagebox.showinfo("Ok","Password changed.")
        for e in (cur_e,new_e,conf_e): e.delete(0,tk.END)
    ttk.Button(frame,text="Change",command=change_pw
              ).grid(row=3,column=0,columnspan=2,pady=8)

# --------------------------------------------------------------------------- #
#  6 ── quick‑launch for standalone testing                                   #
# --------------------------------------------------------------------------- #
if __name__=="__main__":
    launch_dashboard("admin")
