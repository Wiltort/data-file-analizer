# data-file-analizer
Analytical API service for data processing and visualization


# Key Features
    📁 Upload CSV/XLSX files via API
    📊 Generate statistical reports
    📈 Create visualizations (histograms, scatter plots)
    🗄️ PostgreSQL database storage
    🐳 Docker containerization
# Technologies
- Backend: Python 3.12, Flask
- Database: PostgreSQL 13
- Processing: Pandas, Matplotlib
- Infrastructure: Docker, Docker Compose
# Quick Start
## Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
## Installation
- Clone repository
```bash
    git clone https://github.com/yourusername/data-file-analizer.git
    cd data-file-analizer
```

- Create environment file
```bash
    cp .env.example .env
```
- Build and start containers
```bash
    docker-compose up --build
```

## API Examples
- Upload file
```bash
    curl -X POST -F "file=@data.csv" http://localhost:5000/api/v1/upload
```
- Generate histogram
```bash
    curl -X GET http://localhost:5000/api/v1/data/12/plot \
        -H "Content-Type: application/json" \
        -d '{"column": "age", "plot_type": "histogram"}'
```

- Get file statistics
```bash
    curl http://localhost:5000/api/v1/data/12/stats
```
- Clean data
```bash
    curl -X POST http://localhost:5000/api/v1/data/12/clean \
        -H "Content-Type: application/json" \
        -d '{"handle_duplicates": "drop", "fill_missing": "mean"}'
```
## Database Migrations
```bash
# Create new migration
docker-compose run --rm web flask db migrate -m "init"

# Apply migrations
docker-compose run --rm web flask db upgrade
```

## Environment Configuration
    # Database Configuration
    DB_USER=your_db_user
    DB_PASSWORD=your_strong_password
    DB_HOST=db                 # Use 'localhost' for local dev without Docker
    DB_PORT=5432
    DB_NAME=analytics_db              # Database name for production environment
    TEST_DB_NAME=test_data_analytics  # Database name for testing

    # Application Settings
    SECRET_KEY=your_flask_secret_key
    UPLOAD_FOLDER=/app/uploads
    FLASK_ENV=production       # Set to 'development' for debug mode
