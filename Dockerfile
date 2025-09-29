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
