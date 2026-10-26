FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

<<<<<<< HEAD
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
=======
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
>>>>>>> 6e3223a6ded5d9270b477d86ae10eebc030470d2
