"""
Dashboard for the Roster Management System.
It includes three tabs:
  1. Employee Management (with improved controls including "days unavailable")
  2. Roster Creation (dynamic week display, calendar inputs, per–day duty assignment, PDF preview/edit/confirm, and print functionality)
  3. Change Password

Dependencies:
  - tkcalendar (install via: pip install tkcalendar)
  - reportlab, email_sender, pdf_generator (ensure these modules are available)

Note: Ensure that the database has been updated to store additional staff fields:
   available_dates, available_hours, max_hours, and days_unavailable.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
import os
import pdf_generator
import email_sender

# Import DateEntry for calendar widgets
try:
    from tkcalendar import DateEntry
except ImportError:
    messagebox.showerror("Dependency Missing", "tkcalendar not installed. Run: pip install tkcalendar")
    raise

# Global variable for current manager username (set on login)
current_manager = None
# Global variable for currently selected employee (for editing)
selected_employee_id = None

# Global dictionary for duty assignments by weekday.
# For example, global_duties["Monday"] is a list of duty dictionaries assigned for any Monday.
global_duties = {day: [] for day in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]}
# When displaying a week’s roster, we build a mapping (roster_duties) from each day’s date (YYYY-MM-DD) to
# the corresponding weekday’s duties.
roster_duties = {}

# Generate time options in HH:MM format (15-minute increments)
def generate_time_options():
    times = []
    t = datetime.datetime.strptime("00:00", "%H:%M")
    while t.day == 1:
        times.append(t.strftime("%H:%M"))
        t += datetime.timedelta(minutes=15)
    return times

TIME_OPTIONS = generate_time_options()


def launch_dashboard(manager_username):
    """Launch the main dashboard with a tabbed interface."""
    global current_manager
    current_manager = manager_username  # Save for later use

    dashboard_window = tk.Tk()
    dashboard_window.title("Roster Management Dashboard")
    dashboard_window.geometry("900x700")

    notebook = ttk.Notebook(dashboard_window)
    notebook.pack(expand=True, fill="both", padx=10, pady=10)

    # Create frames for each tab
    employee_tab = ttk.Frame(notebook)
    roster_tab = ttk.Frame(notebook)
    password_tab = ttk.Frame(notebook)

    notebook.add(employee_tab, text="Employee Management")
    notebook.add(roster_tab, text="Roster Creation")
    notebook.add(password_tab, text="Change Password")

    init_employee_tab(employee_tab)
    init_roster_tab(roster_tab)
    init_password_tab(password_tab)

    dashboard_window.mainloop()


#########################################
# Employee Management Tab
#########################################
def init_employee_tab(frame):
    """Initialize the Employee Management tab with employee form and list."""
    global selected_employee_id

    form_frame = ttk.LabelFrame(frame, text="Employee Details", padding=10)
    form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

    row = 0
    ttk.Label(form_frame, text="Employee Name:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
    name_entry = tk.Entry(form_frame, width=30)
    name_entry.grid(row=row, column=1, padx=5, pady=5)
    name_entry.insert(0, "Enter employee name")

    row += 1
    ttk.Label(form_frame, text="Email:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
    email_entry = tk.Entry(form_frame, width=30)
    email_entry.grid(row=row, column=1, padx=5, pady=5)
    email_entry.insert(0, "Enter employee email")

    row += 1
    ttk.Label(form_frame, text="Phone Number:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
    phone_entry = tk.Entry(form_frame, width=30)
    phone_entry.grid(row=row, column=1, padx=5, pady=5)
    phone_entry.insert(0, "Enter phone number")

    row += 1
    ttk.Label(form_frame, text="Available Date From:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
    date_from_entry = DateEntry(form_frame, width=27, date_pattern="yyyy-mm-dd")
    date_from_entry.grid(row=row, column=1, padx=5, pady=5)

    row += 1
    ttk.Label(form_frame, text="Available Date To:").grid(row=row, column=0, sticky="e", padx=5, pady=5)
    date_to_entry = DateEntry(form_frame, width=27, date_pattern="yyyy-mm-dd")
    date_to_entry.grid(row=row, column=1, padx=5, pady=5)

    row += 1
    ttk.Label(form_frame, text="Dates Unavailable (comma separated):").grid(row=row, column=0, sticky="e", padx=5, pady=5)
    dates_unavail_entry = tk.Entry(form_frame, width=30)
    dates_unavail_entry.grid(row=row, column=1, padx=5, pady=5)
    dates_unavail_entry.insert(0, "e.g., 2025-05-05,2025-05-06")

    row += 1
    ttk.Label(form_frame, text="Available Hours From (e.g., 09:00):").grid(row=row, column=0, sticky="e", padx=5, pady=5)
    hours_from_entry = tk.Entry(form_frame, width=30)
    hours_from_entry.grid(row=row, column=1, padx=5, pady=5)
    hours_from_entry.insert(0, "e.g., 09:00")

    row += 1
    ttk.Label(form_frame, text="Available Hours To (e.g., 17:00):").grid(row=row, column=0, sticky="e", padx=5, pady=5)
    hours_to_entry = tk.Entry(form_frame, width=30)
    hours_to_entry.grid(row=row, column=1, padx=5, pady=5)
    hours_to_entry.insert(0, "e.g., 17:00")

    row += 1
    ttk.Label(form_frame, text="Hours Unavailable (e.g., 13:00-14:00):").grid(row=row, column=0, sticky="e", padx=5, pady=5)
    hours_unavail_entry = tk.Entry(form_frame, width=30)
    hours_unavail_entry.grid(row=row, column=1, padx=5, pady=5)
    hours_unavail_entry.insert(0, "e.g., 13:00-14:00")

    row += 1
    ttk.Label(form_frame, text="Max Hours per Week (optional):").grid(row=row, column=0, sticky="e", padx=5, pady=5)
    max_hours_entry = tk.Entry(form_frame, width=30)
    max_hours_entry.grid(row=row, column=1, padx=5, pady=5)
    max_hours_entry.insert(0, "Leave blank for no limit")

    row += 1
    ttk.Label(form_frame, text="Days Unavailable:").grid(row=row, column=0, sticky="ne", padx=5, pady=5)
    days_frame = ttk.Frame(form_frame)
    days_frame.grid(row=row, column=1, sticky="w", padx=5, pady=5)
    day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    days_vars = {}
    for d in day_names:
        var = tk.IntVar()
        cb = ttk.Checkbutton(days_frame, text=d, variable=var)
        cb.pack(side="left", padx=2)
        days_vars[d] = var

    # Employee list frame
    list_frame = ttk.LabelFrame(frame, text="Registered Employees (Click to Edit)", padding=10)
    list_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
    employee_listbox = tk.Listbox(list_frame, width=60, height=10)
    employee_listbox.pack(fill="both", padx=5, pady=5)

    def refresh_employee_list():
        conn = sqlite3.connect('roster.db')
        cursor = conn.cursor()
        cursor.execute("SELECT staff_id, name FROM staff")
        employees = cursor.fetchall()
        conn.close()
        employee_listbox.delete(0, tk.END)
        for emp in employees:
            employee_listbox.insert(tk.END, f"ID:{emp[0]} - {emp[1]}")

    refresh_employee_list()

    def on_employee_select(event):
        global selected_employee_id
        selection = employee_listbox.curselection()
        if selection:
            index = selection[0]
            selected_text = employee_listbox.get(index)
            selected_id = selected_text.split(" - ")[0].split(":")[1]
            selected_employee_id = int(selected_id)
            conn = sqlite3.connect('roster.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name, email, phone_number, available_dates, available_hours, max_hours, days_unavailable FROM staff WHERE staff_id=?", (selected_employee_id,))
            record = cursor.fetchone()
            conn.close()
            if record:
                name_entry.delete(0, tk.END)
                name_entry.insert(0, record[0])
                email_entry.delete(0, tk.END)
                email_entry.insert(0, record[1])
                phone_entry.delete(0, tk.END)
                phone_entry.insert(0, record[2])
                if record[3] and "|" in record[3]:
                    parts = record[3].split("|")
                    date_range = parts[0].split(",")
                    unavail_dates = parts[1]
                    date_from_entry.set_date(date_range[0])
                    date_to_entry.set_date(date_range[1])
                    dates_unavail_entry.delete(0, tk.END)
                    dates_unavail_entry.insert(0, unavail_dates)
                else:
                    date_from_entry.set_date(datetime.date.today())
                    date_to_entry.set_date(datetime.date.today())
                    dates_unavail_entry.delete(0, tk.END)
                if record[4] and "|" in record[4]:
                    parts = record[4].split("|")
                    hour_range = parts[0].split(",")
                    unavail_hours = parts[1]
                    hours_from_entry.delete(0, tk.END)
                    hours_from_entry.insert(0, hour_range[0])
                    hours_to_entry.delete(0, tk.END)
                    hours_to_entry.insert(0, hour_range[1])
                    hours_unavail_entry.delete(0, tk.END)
                    hours_unavail_entry.insert(0, unavail_hours)
                else:
                    hours_from_entry.delete(0, tk.END)
                    hours_to_entry.delete(0, tk.END)
                    hours_unavail_entry.delete(0, tk.END)
                max_hours_entry.delete(0, tk.END)
                max_hours_entry.insert(0, record[5] if record[5] is not None else "")
                for d in day_names:
                    days_vars[d].set(0)
                if record[6]:
                    for day in record[6].split(","):
                        day = day.strip()
                        if day in days_vars:
                            days_vars[day].set(1)

    employee_listbox.bind("<<ListboxSelect>>", on_employee_select)

    def save_employee():
        global selected_employee_id
        name = name_entry.get()
        email = email_entry.get()
        phone = phone_entry.get()
        available_dates = f"{date_from_entry.get_date()},{date_to_entry.get_date()}|{dates_unavail_entry.get()}"
        available_hours = f"{hours_from_entry.get()},{hours_to_entry.get()}|{hours_unavail_entry.get()}"
        max_hours = max_hours_entry.get().strip()
        max_hours = max_hours if max_hours != "" else None
        unavailable_days = [d for d, var in days_vars.items() if var.get() == 1]
        days_unavailable = ",".join(unavailable_days)
        conn = sqlite3.connect('roster.db')
        cursor = conn.cursor()
        if selected_employee_id:
            cursor.execute("""
                UPDATE staff 
                SET name=?, email=?, phone_number=?, available_dates=?, available_hours=?, max_hours=?, days_unavailable=?
                WHERE staff_id=?""",
                (name, email, phone, available_dates, available_hours, max_hours, days_unavailable, selected_employee_id))
            messagebox.showinfo("Updated", "Employee record updated successfully.")
        else:
            cursor.execute("""
                INSERT INTO staff (name, email, phone_number, available_dates, available_hours, max_hours, days_unavailable)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (name, email, phone, available_dates, available_hours, max_hours, days_unavailable))
            messagebox.showinfo("Added", "Employee added successfully.")
        conn.commit()
        conn.close()
        selected_employee_id = None
        name_entry.delete(0, tk.END)
        email_entry.delete(0, tk.END)
        phone_entry.delete(0, tk.END)
        date_from_entry.set_date(datetime.date.today())
        date_to_entry.set_date(datetime.date.today())
        dates_unavail_entry.delete(0, tk.END)
        hours_from_entry.delete(0, tk.END)
        hours_to_entry.delete(0, tk.END)
        hours_unavail_entry.delete(0, tk.END)
        max_hours_entry.delete(0, tk.END)
        for d in day_names:
            days_vars[d].set(0)
        refresh_employee_list()

    btn = tk.Button(form_frame, text="Add / Update Employee", command=save_employee)
    btn.grid(row=row + 1, column=0, columnspan=2, pady=10)


#########################################
# Roster Creation Tab
#########################################
def init_roster_tab(frame):
    """Initialize the Roster Creation tab with dynamic week display, duty assignment, and editing capability."""
    global roster_duties
    roster_duties = {}

    # Top frame for roster date range selection
    top_frame = ttk.LabelFrame(frame, text="Select Roster Date Range", padding=10)
    top_frame.pack(fill="x", padx=10, pady=5)

    ttk.Label(top_frame, text="Roster Start Date:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    start_date_entry = DateEntry(top_frame, width=15, date_pattern="yyyy-mm-dd")
    start_date_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(top_frame, text="Roster End Date:").grid(row=0, column=2, sticky="e", padx=5, pady=5)
    end_date_entry = DateEntry(top_frame, width=15, date_pattern="yyyy-mm-dd")
    end_date_entry.grid(row=0, column=3, padx=5, pady=5)

    # Week view frame
    week_frame = ttk.LabelFrame(frame, text="Week Duties", padding=10)
    week_frame.pack(fill="both", expand=True, padx=10, pady=5)

    # Dictionary to hold Listbox widgets for each day (key: date string)
    day_listboxes = {}

    def refresh_day_listbox(date_str):
        lb = day_listboxes.get(date_str)
        if lb is not None:
            lb.delete(0, tk.END)
            duties_list = roster_duties.get(date_str, [])
            if duties_list:
                for duty in duties_list:
                    lb.insert(tk.END, f"{duty['employee']} ({duty['start']}-{duty['end']})")
            else:
                lb.insert(tk.END, "(No duties assigned)")

    def update_week_display():
        for widget in week_frame.winfo_children():
            widget.destroy()
        day_listboxes.clear()
        roster_duties.clear()
        sd = start_date_entry.get_date()
        for i in range(7):
            d = sd + datetime.timedelta(days=i)
            date_str = d.strftime("%Y-%m-%d")
            weekday = d.strftime("%A")
            # Get existing duties for this weekday (if any) from global_duties
            roster_duties[date_str] = global_duties.get(weekday, []).copy()
            day_frame = ttk.Frame(week_frame, borderwidth=1, relief="solid", padding=5)
            day_frame.grid(row=i // 2, column=i % 2, padx=5, pady=5, sticky="nsew")
            header = f"{weekday}, {date_str}"
            ttk.Label(day_frame, text=header, font=("Helvetica", 10, "bold")).pack(anchor="w")
            lb = tk.Listbox(day_frame, width=40, height=4)
            lb.pack(padx=5, pady=5)
            day_listboxes[date_str] = lb
            refresh_day_listbox(date_str)
            # Bind double-click on duty to edit it.
            lb.bind("<Double-Button-1>", lambda event, ds=date_str: edit_duty(event, ds))
            btn = tk.Button(day_frame, text="Add Duty", command=lambda ds=date_str: open_add_duty_window(ds))
            btn.pack(padx=5, pady=5)

    def update_end_date(*args):
        try:
            sd = start_date_entry.get_date()
            ed = sd + datetime.timedelta(days=6)
            end_date_entry.set_date(ed)
            update_week_display()
        except Exception as e:
            print("Error updating end date:", e)

    start_date_entry.bind("<<DateEntrySelected>>", update_end_date)
    update_end_date()

    def open_add_duty_window(date_str):
        weekday = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
        ad_window = tk.Toplevel(frame)
        ad_window.title(f"Add Duty for {weekday}, {date_str}")
        ad_window.grab_set()

        ttk.Label(ad_window, text="Select Employee:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        conn = sqlite3.connect('roster.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, days_unavailable FROM staff")
        emp_records = cursor.fetchall()
        conn.close()
        available_emps = []
        for rec in emp_records:
            emp_name = rec[0]
            days_unavail = rec[1] if rec[1] else ""
            if weekday in [d.strip() for d in days_unavail.split(",") if d.strip()]:
                continue
            available_emps.append(emp_name)
        if not available_emps:
            messagebox.showerror("No Available Employees", f"No employees available on {weekday}.")
            ad_window.destroy()
            return
        emp_var = tk.StringVar(ad_window)
        emp_var.set(available_emps[0])
        emp_menu = ttk.OptionMenu(ad_window, emp_var, available_emps[0], *available_emps)
        emp_menu.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(ad_window, text="Duty Start Time:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        start_time_cb = ttk.Combobox(ad_window, values=TIME_OPTIONS, width=8)
        start_time_cb.grid(row=1, column=1, padx=5, pady=5)
        start_time_cb.set("09:00")

        ttk.Label(ad_window, text="Duty End Time:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        end_time_cb = ttk.Combobox(ad_window, values=TIME_OPTIONS, width=8)
        end_time_cb.grid(row=2, column=1, padx=5, pady=5)
        end_time_cb.set("12:00")

        def save_duty():
            duty_start = start_time_cb.get()
            duty_end = end_time_cb.get()
            try:
                fmt = "%H:%M"
                t_start = datetime.datetime.strptime(duty_start, fmt)
                t_end = datetime.datetime.strptime(duty_end, fmt)
                if t_end <= t_start:
                    messagebox.showerror("Invalid Time", "Duty End Time must be later than Start Time.")
                    return
            except Exception as e:
                messagebox.showerror("Invalid Time Format", "Please ensure times are in HH:MM format.")
                return
            duty = {"employee": emp_var.get(), "start": duty_start, "end": duty_end}
            wkday = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
            global_duties[wkday].append(duty)
            sd = start_date_entry.get_date()
            for i in range(7):
                d = sd + datetime.timedelta(days=i)
                if d.strftime("%A") == wkday:
                    key = d.strftime("%Y-%m-%d")
                    roster_duties[key] = global_duties[wkday].copy()
                    if key in day_listboxes:
                        refresh_day_listbox(key)
            ad_window.destroy()

        ttk.Button(ad_window, text="Save Duty", command=save_duty).grid(row=3, column=0, columnspan=2, pady=10)

    # Function to edit an assigned duty when double-clicked in a listbox.
    def edit_duty(event, date_str):
        lb = day_listboxes.get(date_str)
        if lb is None:
            return
        selection = lb.curselection()
        if not selection:
            return
        index = selection[0]
        # Retrieve the duty from the roster_duties list for that date.
        duty = roster_duties.get(date_str)[index]
        weekday = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
        ed_window = tk.Toplevel(frame)
        ed_window.title(f"Edit Duty for {weekday}, {date_str}")
        ed_window.grab_set()

        ttk.Label(ed_window, text="Select Employee:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        conn = sqlite3.connect('roster.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, days_unavailable FROM staff")
        emp_records = cursor.fetchall()
        conn.close()
        available_emps = []
        for rec in emp_records:
            emp_name = rec[0]
            days_unavail = rec[1] if rec[1] else ""
            if weekday in [d.strip() for d in days_unavail.split(",") if d.strip()]:
                continue
            available_emps.append(emp_name)
        if not available_emps:
            messagebox.showerror("No Available Employees", f"No employees available on {weekday}.")
            ed_window.destroy()
            return
        emp_var = tk.StringVar(ed_window)
        # Preselect the current employee
        if duty["employee"] in available_emps:
            emp_var.set(duty["employee"])
        else:
            emp_var.set(available_emps[0])
        emp_menu = ttk.OptionMenu(ed_window, emp_var, emp_var.get(), *available_emps)
        emp_menu.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(ed_window, text="Duty Start Time:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        start_time_cb = ttk.Combobox(ed_window, values=TIME_OPTIONS, width=8)
        start_time_cb.grid(row=1, column=1, padx=5, pady=5)
        start_time_cb.set(duty["start"])

        ttk.Label(ed_window, text="Duty End Time:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        end_time_cb = ttk.Combobox(ed_window, values=TIME_OPTIONS, width=8)
        end_time_cb.grid(row=2, column=1, padx=5, pady=5)
        end_time_cb.set(duty["end"])

        def save_edited_duty():
            new_start = start_time_cb.get()
            new_end = end_time_cb.get()
            try:
                fmt = "%H:%M"
                t_start = datetime.datetime.strptime(new_start, fmt)
                t_end = datetime.datetime.strptime(new_end, fmt)
                if t_end <= t_start:
                    messagebox.showerror("Invalid Time", "Duty End Time must be later than Start Time.")
                    return
            except Exception as e:
                messagebox.showerror("Invalid Time Format", "Please ensure times are in HH:MM format.")
                return
            # Update the duty entry with the new values.
            duty["employee"] = emp_var.get()
            duty["start"] = new_start
            duty["end"] = new_end
            wkday = weekday  # already computed
            # Update global_duties for the weekday: find the duty at same index and update it.
            if len(global_duties[wkday]) > index:
                global_duties[wkday][index] = duty.copy()
            # Now update the display for every day in the week with same weekday.
            sd = start_date_entry.get_date()
            for i in range(7):
                d = sd + datetime.timedelta(days=i)
                if d.strftime("%A") == wkday:
                    key = d.strftime("%Y-%m-%d")
                    roster_duties[key] = global_duties[wkday].copy()
                    if key in day_listboxes:
                        refresh_day_listbox(key)
            ed_window.destroy()

        ttk.Button(ed_window, text="Save Changes", command=save_edited_duty).grid(row=3, column=0, columnspan=2, pady=10)

    # Finalize Roster Section with Print button included
    def finalize_roster():
        conn = sqlite3.connect('roster.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, email FROM staff")
        all_emps = cursor.fetchall()
        conn.close()
        emp_names = [emp[0] for emp in all_emps]

        header_row = ["Day/Name"] + emp_names + ["Weekly Total"]
        emp_week_total = {name: 0.0 for name in emp_names}
        roster_table = [header_row]

        sd = start_date_entry.get_date()
        for i in range(7):
            d = sd + datetime.timedelta(days=i)
            date_str = d.strftime("%Y-%m-%d")
            weekday = d.strftime("%A")
            row_cells = [f"{weekday}, {date_str}"]
            duties = global_duties.get(weekday, [])
            for emp in emp_names:
                emp_duties = [duty for duty in duties if duty["employee"] == emp]
                if emp_duties:
                    cell_text = "\n".join([f"{duty['start']}-{duty['end']}" for duty in emp_duties])
                    day_total = 0.0
                    for duty in emp_duties:
                        t_start = datetime.datetime.strptime(duty["start"], "%H:%M")
                        t_end = datetime.datetime.strptime(duty["end"], "%H:%M")
                        day_total += (t_end - t_start).seconds / 3600.0
                    emp_week_total[emp] += day_total
                    cell_text += f"\n({day_total:.1f} hr)"
                else:
                    cell_text = ""
                row_cells.append(cell_text)
            row_cells.append("")
            roster_table.append(row_cells)
        total_row = ["Weekly Total"]
        for emp in emp_names:
            total_row.append(f"{emp_week_total[emp]:.1f} hr" if emp_week_total[emp] > 0 else "")
        total_row.append("")
        roster_table.append(total_row)

        pdf_filename = f"final_roster_{sd.strftime('%Y-%m-%d')}_to_{end_date_entry.get_date().strftime('%Y-%m-%d')}.pdf"
        pdf_generator.generate_roster_pdf(roster_table, filename=pdf_filename)

        preview_window = tk.Toplevel(frame)
        preview_window.title("Roster Preview")
        preview_window.geometry("450x250")
        ttk.Label(preview_window, text=f"Roster PDF generated:\n{pdf_filename}", font=("Helvetica", 10, "bold")).pack(padx=10, pady=10)
        btn_frame = ttk.Frame(preview_window)
        btn_frame.pack(pady=10)

        def view_pdf():
            try:
                os.startfile(pdf_filename)
            except Exception as ex:
                messagebox.showerror("Error", f"Could not open PDF: {ex}")

        def print_pdf():
            try:
                os.startfile(pdf_filename, "print")
            except Exception as ex:
                messagebox.showerror("Error", f"Could not print PDF: {ex}")

        def edit_roster():
            preview_window.destroy()

        def confirm_roster():
            conn = sqlite3.connect('roster.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO roster (start_date, end_date, pdf_file) VALUES (?, ?, ?)",
                           (sd.strftime("%Y-%m-%d"), end_date_entry.get_date().strftime("%Y-%m-%d"), pdf_filename))
            conn.commit()
            conn.close()
            preview_window.destroy()
            conn = sqlite3.connect('roster.db')
            cur = conn.cursor()
            cur.execute("SELECT email FROM staff")
            emails = [row[0] for row in cur.fetchall()]
            conn.close()
            subject = f"Roster for {sd.strftime('%Y-%m-%d')} to {end_date_entry.get_date().strftime('%Y-%m-%d')}"
            body = "Please find attached the finalized roster."
            email_sender.open_email_client(emails, subject, body, attachment_path=pdf_filename)
            messagebox.showinfo("Roster Confirmed", "Roster saved and email client launched.")

        ttk.Button(btn_frame, text="View PDF", command=view_pdf).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Print", command=print_pdf).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Edit", command=edit_roster).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Confirm", command=confirm_roster).grid(row=0, column=3, padx=5)

    # Place Finalize Roster button
    finalize_frame = ttk.Frame(frame, padding=10)
    finalize_frame.pack(fill="x", padx=10, pady=10)
    ttk.Button(finalize_frame, text="Finalize Roster", command=finalize_roster).pack()


#########################################
# Change Password Tab
#########################################
def init_password_tab(frame):
    """Initialize the Change Password tab."""
    ttk.Label(frame, text="Current Password:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    current_pass_entry = tk.Entry(frame, width=20, show="*")
    current_pass_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(frame, text="New Password:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    new_pass_entry = tk.Entry(frame, width=20, show="*")
    new_pass_entry.grid(row=1, column=1, padx=5, pady=5)

    ttk.Label(frame, text="Confirm New Password:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
    confirm_pass_entry = tk.Entry(frame, width=20, show="*")
    confirm_pass_entry.grid(row=2, column=1, padx=5, pady=5)

    def change_password():
        current_password = current_pass_entry.get()
        new_password = new_pass_entry.get()
        confirm_password = confirm_pass_entry.get()
        if new_password != confirm_password:
            messagebox.showerror("Error", "New passwords do not match.")
            return

        conn = sqlite3.connect('roster.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM managers WHERE username=?", (current_manager,))
        current_db_pass = cursor.fetchone()
        if not current_db_pass:
            messagebox.showerror("Error", "Manager record not found.")
            conn.close()
            return

        if current_password != current_db_pass[0]:
            messagebox.showerror("Error", "Current password is incorrect.")
            conn.close()
            return

        cursor.execute("UPDATE managers SET password=? WHERE username=?", (new_password, current_manager))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Password changed successfully.")
        current_pass_entry.delete(0, tk.END)
        new_pass_entry.delete(0, tk.END)
        confirm_pass_entry.delete(0, tk.END)

    ttk.Button(frame, text="Change Password", command=change_password).grid(row=3, column=0, columnspan=2, pady=10)


# End of dashboard.py
