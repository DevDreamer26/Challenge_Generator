FROM python:3.9

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python", "main.py"]
# Expose the port the app runs on
EXPOSE 8000 

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000   
# Use a non-root user to run the application
RUN useradd -m appuser
USER appuser
# Set the entrypoint to run the application
ENTRYPOINT ["python", "main.py"]   
# Use a non-root user to run the application
RUN useradd -m appuser
USER appuser

