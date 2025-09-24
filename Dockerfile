FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py admin_bot.py ./
COPY templates templates/
COPY static static/

# Expose only port 5000 (no other ports!)
EXPOSE 5000

# Run both Flask and admin bot
CMD ["sh", "-c", "python admin_bot.py & python app.py"]