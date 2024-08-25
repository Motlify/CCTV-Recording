# Use an official Linux base image
FROM debian:bookworm

# Set the working directory
WORKDIR /app

# Update packages and install necessary dependencies
RUN apt-get update && apt-get install -y \
    cron ffmpeg python3 python3-venv python3-pip

# Create a virtual environment
RUN python3 -m venv venv

# Activate the virtual environment
ENV PATH="/app/venv/bin:$PATH"

# Copy the requirements file (if you have one)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

RUN chmod 0755 /app/delete_old_cctv.sh
RUN chmod 0755 /app/cctv_recording/create_dirs_cctv.py

# Give execution rights on the cron job
ENV cron_dirs="0 23 * * * /app/cctv_recording/create_dirs_cctv.py"
ENV retention_days=30
ENV cron_retention_script="0 23 * * * /app/delete_old_cctv.sh"

# Apply cron job and Set the entry point command
CMD echo "${cron_dirs}" > /etc/cron.d/cctv-cron \
    && echo "${cron_retention_script} ${retention_days} \n" >> /etc/cron.d/cctv-cron \
    && chmod 0644 /etc/cron.d/cctv-cron \
    && crontab /etc/cron.d/cctv-cron \
    && cron && python3 cctv_recording/main.py