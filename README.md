
# Roster Management System – BP Eltham

### **Author**: Anup Chapain 
### **Contact**: [emailofanup@gmail.com](mailto:emailofanup@gmail.com)
---
## Overview
**I create this app while I was working at BP2go, Eltham Taranaki to assist in roster creation. Recently I revisited the code to dockerize it.**

**Roster Management System** is a Python Tkinter-based desktop application designed to manage employees, create weekly rosters, track working hours, and generate professional PDF schedules. It provides a user-friendly GUI that allows managers to handle all roster-related tasks efficiently.

### Key features include:

- Employee Management (Add, Update, Delete)
- Weekly Roster Creation with Start/End Times
- Daily Notes for Each Roster Day
- Automatic PDF Generation of Rosters
- Copy All Emails Feature
- Change Admin Password
- Viewing Previous Rosters
- Reusing and editing previous Rosters
- Fully functional on Windows, macOS, Linux, and inside Docker

---

## Built With

- **Python 3.11**: Core programming language.
- **Tkinter**: GUI framework for Python.
- **SQLite3**: Lightweight database for storing employees and roster data.
- **Tkcalendar**: Calendar widget for selecting dates in the roster.
- **pdf_generator (custom module)**: Handles PDF creation for rosters.
- **Docker**: Containerization to make the app environment-independent.
- **X11 Forwarding**: For GUI display inside Docker containers.
- **xdg-utils / Firefox**: To open PDFs and URLs from within Docker.

---

## Features and Implementation

### 1. Employee Management

- Form to add/update employee details: Name, Email, Phone, Max Hours, and Unavailable Days.
- `Listbox` shows all registered employees.
- Delete employee functionality updates both database and in-memory duty schedules.
- Copy all employee emails to clipboard with a single click.

**Python libraries used**: `sqlite3`, `tkinter`, `ttk`.

---

### 2. Roster Creation

- Define start date (end date auto-calculated for 7-day week).
- Add, Edit, Remove duties per day.
- Daily notes for special instructions.
- Automatic calculation of total hours per employee.
- Load previously created rosters using a dropdown.

**Logic Highlights:**

- `global_duties`: Template for weekly duties (Sunday-Saturday).
- `roster_duties`: Concrete week view containing actual assignments.
- `_duration()`: Calculates hours between start and end times.
- `_max_hours()` and `_total_hours()`: Ensures no employee exceeds allowed weekly hours.
- `available_staff()`: Returns staff available on a specific weekday.
- PDF generation logic loops through week, employees, and calculates totals.

---

### 3. PDF Generation

- Roster saved with timestamped filename in `Rosters/` folder.
- Includes header row (Day/Name), individual employee duties, daily notes, and weekly totals.
- Uses `pdf_generator.generate_roster_pdf()` for creating a clean PDF.

## Challenges faced:

Running the app inside Docker initially caused PDF and URL opening failures. This was due to the fact that `xdg-open` required a host environment, and without X11 forwarding or a browser installed, opening files silently failed.  

**Solution**:

1. Detect Docker environment using `RUNNING_IN_DOCKER` environment variable.
2. Fallback `xdg-open` calls to `firefox` inside the container.
3. Added proper X11 forwarding to allow GUI apps (Tkinter) to display.

---

### 4. Change Password

- Allows admin to update password securely.
- Validates current password before applying new password.
- Since there is no strong security of the database file, it is just a dummy feature for now.

**Python Libraries**: `sqlite3`, `tkinter.messagebox`.

---

### 5. About and Help Tabs

- About tab: Developer information with clickable URL and email (handled via `open_host()`).
- Help tab: Full user manual displayed using `tk.Text`.

---

## Docker Integration

To make the app fully functional inside Docker, the following steps were implemented:

### Dockerfile

```dockerfile
# ───────────── Base Python image ─────────────
FROM python:3.11-slim

# ───────────── Install Tkinter + minimal GUI + xdg-open ─────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    tk-dev \
    xdg-utils \
    firefox-esr \
    && rm -rf /var/lib/apt/lists/*

# ───────────── Set working directory ─────────────
WORKDIR /app

# ───────────── Copy project files ─────────────
COPY . /app

# ───────────── Install Python dependencies ─────────────
RUN pip install --no-cache-dir -r requirements.txt

# ───────────── Ensure rosters folder exists ─────────────
RUN mkdir -p /app/Rosters

# ───────────── Expose X11 (for GUI) ─────────────
ENV DISPLAY=:0
ENV RUNNING_IN_DOCKER=1

# ───────────── Run Tkinter app ─────────────
CMD ["python", "main.py"]

````



**Explanation of Docker Concepts Used:**

* `FROM python:3.11-slim`: Lightweight Python base image.
* `apt-get install -y python3-tk tk-dev x11-apps xdg-utils firefox-esr`: Install Tkinter GUI libraries, X11 apps, xdg-utils for opening files/URLs, and Firefox as fallback browser.
* `WORKDIR /app`: Sets the working directory inside the container.
* `COPY . /app`: Copies project files into container.
* `pip install --no-cache-dir -r requirements.txt`: Installs Python dependencies efficiently.
* `mkdir -p /app/Rosters`: Ensures folder for saving PDFs exists.
* `-v /tmp/.X11-unix:/tmp/.X11-unix`: Shares host X11 socket for GUI.
* `-v $HOME/.Xauthority:/root/.Xauthority:ro`: Allows authentication with host X server.
* `-v $(pwd):/app`: Mounts project directory for persistence.
* `RUNNING_IN_DOCKER==1`: Signals Python code to use `firefox` fallback in `open_host()`.

---

## Challenges and Learning Experience

1. **GUI in Docker**: Running Tkinter inside a container required X11 forwarding and mapping host sockets.
2. **PDF & URL Opening**: `xdg-open` failed in Docker without a host wrapper; solved by installing Firefox and adding fallback logic in `open_host()`.
3. **Cross-Platform Compatibility**: Ensuring `open_host()` works on Windows, macOS, Linux, and Docker was challenging; implemented OS detection using `platform.system()`.
4. **Database Management**: Learned to use SQLite3 effectively for storing relational data for staff and roster duties.

---

## Python Logic & Libraries Used

* **Tkinter & ttk**: For GUI forms, tabs, buttons, and listboxes.
* **tkcalendar**: DateEntry widget for picking dates.
* **sqlite3**: Store staff data and rosters.
* **datetime**: Handle dates and times for duty assignments.
* **subprocess & webbrowser**: Open PDFs and URLs.
* **os & platform**: Handle filesystem paths and OS detection.
* **Custom pdf_generator**: Generates weekly roster PDFs with headers, employee duty details, notes, and weekly totals.

---

## Usage

1. Clone repository:

```bash
git clone https://github.com/fitandfine/BP_Roster
cd BP_Roster
```

2. Build Docker image:

```bash
docker build -t roster-app .
```

3. Run the container (with GUI forwarding):

```bash
xhost +local:docker

docker run -it \
    --rm \
    -e DISPLAY=$DISPLAY \
    -e RUNNING_IN_DOCKER=1 \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $HOME/.Xauthority:/root/.Xauthority:ro \
    -v $(pwd):/app \
    roster-app
```

**Author**: Anup Chapain
**Contact**: [emailofanup@gmail.com](mailto:emailofanup@gmail.com)


