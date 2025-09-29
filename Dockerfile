# ───────────── Base Python image ─────────────
FROM python:3.11-slim

# ───────────── Install Tkinter + X11 support ─────────────
RUN apt-get update && apt-get install -y \
    python3-tk \
    tk-dev \
    x11-apps \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# ───────────── Set working directory ─────────────
WORKDIR /app

# ───────────── Copy project files ─────────────
COPY . /app

# ───────────── Install Python dependencies ─────────────
RUN pip install --no-cache-dir -r requirements.txt

# ───────────── Create folders if not exist ─────────────
RUN mkdir -p /app/Rosters

# ───────────── Run the main Tkinter app ─────────────
CMD ["python", "main.py"]
