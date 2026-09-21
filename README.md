# Swiggy AI Data Engineering Project
> *From raw CSVs to an AI-powered warehouse — a complete modern data stack, built on one food-delivery dataset.*

## Overview
This project represents an end-to-end data engineering curriculum and implementation pipeline designed around a realistic food-delivery business domain (**Swiggy**). It covers the entire journey of data—starting from raw CSVs stored in Amazon S3, loaded and processed in Snowflake via a modern ELT framework using dbt, and orchestrated using Apache Airflow, Docker, and OpenAI for downstream AI applications (like RAG and Text-to-SQL).

---

## Tech Stack & Tools
* **Storage:** AWS S3 + IAM
* **Data Warehouse:** Snowflake (SQL, RBAC, Stages, File Formats, COPY INTO)
* **Transformation & Modeling:** dbt (Data Build Tool), Medallion Architecture (Bronze, Silver, Gold layers), Star Schema, Incremental Models
* **Orchestration & Containerization:** Apache Airflow, Docker
* **AI & Visualization:** Ollama (LLM enrichment, sentiment analysis, text-to-SQL), Streamlit ,Looker Studio
* **Version Control:** Git

---

## Data Modelling

<img width="2818" height="1644" alt="image" src="https://github.com/user-attachments/assets/f6a7adc2-e54c-440a-8313-02d76235e792" />


## Architecture & Medallion Design
The pipeline adopts the **Medallion Architecture**, ensuring high debuggability, data safety, and zero raw data loss:
1. **RAW (Bronze):** Untouched, append-only raw data loaded directly from S3 into Snowflake.
2. **STAGING (Silver):** Cleaned, typed, and standardized data models using dbt (`try_to_decimal`, `nullif`, `initcap`, etc.).
3. **MARTS (Gold):** Business-ready dimensional models (Star Schema with facts and dimensions) optimized for analytics, BI, and AI consumption.

---

## Dataset Domain (swiggy-data)
The core pipeline processes a massive volume of simulated food-delivery transactions:
* **Users:** Customer profile data (signup date, city).
* **Restaurants:** Merchant information (cuisine, location, ratings).
* **Menu Items:** Catalog data (item names, categories, pricing).
* **Orders:** Core fact tables (order status, timestamps, total amounts).
* **Order Items:** Line-item breakdowns.
* **Reviews:** Free-text customer feedback and ratings (acting as AI enrichment fuel).

---

## Key Implementation Steps

### 1. Data Ingestion to Amazon S3
* Structured using S3 buckets and prefixes (e.g., `s3://swiggy-data/raw/orders/`, `s3://swiggy-data/raw/reviews/`).
* Bulk syncing using AWS CLI

### 2. Loading into Snowflake Warehouse
Setting up external stages and file formats

### 3. Transformation with dbt
Modular data modeling utilizing source() and ref() functions to automatically build the Dependency Graph (DAG).

<img width="2940" height="1654" alt="image" src="https://github.com/user-attachments/assets/e94fbb0a-e64a-4209-a245-45b80374c346" />


Implementing efficient Incremental Models to process only new records for large-scale fact tables (avoiding full-table rebuilds on millions of rows).

Building a programmatic Date Spine calendar dimension to avoid missing days in time-series analytical reports.

## Dasboard, AI & Analytics Integration
### Text-to-SQL & RAG: 

Leveraging Ollama on top of the clean Gold/Silver data models to query operational metrics dynamically.
<img width="2920" height="1608" alt="image" src="https://github.com/user-attachments/assets/7362282d-9132-4d4e-8bc1-a7f53b5c014b" />



### Streamlit Dashboard:

Providing an interactive interface for stakeholders to inspect growth trends, delivery speeds, cancellation rates, and customer sentiment analytics.


<img width="2936" height="1614" alt="image" src="https://github.com/user-attachments/assets/8c020347-f39a-4354-9930-73f55963243b" />


### Looker Studio Dashboard:

An interactive business intelligence report built to track core operational metrics, delivery trends, and performance insights. You can view the live report here: Looker Studio Dashboard.

<img width="1172" height="875" alt="Screenshot 2026-09-22 at 4 18 16 AM" src="https://github.com/user-attachments/assets/1d3ea4bf-fada-467e-8e31-9d13edb10d50" />
