FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p reports

# Run tests with coverage
CMD ["pytest", "--cov=src", "--cov-report=html:reports/coverage_html", \
     "--cov-report=xml:reports/coverage.xml", "--junit-xml=reports/junit.xml", "-v"]
