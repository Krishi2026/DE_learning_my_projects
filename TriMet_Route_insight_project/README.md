# 🚍 TriMet Route Insight – Real-Time Transit Data Pipeline (GCP)

A real-time data engineering project designed to collect, validate, and visualize GPS data from TriMet public transit vehicles using Google Cloud Platform (GCP).

---

## 📌 Project Overview

This project simulates and processes real-time transit data using Google Cloud services. It fetches GPS breadcrumb data from TriMet’s public API, publishes it via Pub/Sub, validates and enriches the data, and stores it in a PostgreSQL database. Processed data is then visualized using Mapbox GL on interactive maps.

---

## 🧩 Key Features

- 🔄 **Real-Time Ingestion**: Publish TriMet vehicle GPS data to Google Cloud Pub/Sub
- 🧪 **Data Validation & Enrichment**:
  - GPS bounds checks
  - Negative value handling
  - Trip ID and timestamp consistency
  - Speed calculation and outlier detection using z-score
- 🗃️ **Storage**:
  - Processed data stored in `Trip` and `Breadcrumb` tables in PostgreSQL
- 🗺️ **Visualization**:
  - Visualize vehicle routes and speeds using **Mapbox GL** and **GeoJSON**

---

## ⚙️ Technologies Used

- **Google Cloud Platform**
  - Pub/Sub (for streaming)
  - Service Accounts (authentication)
- **Python**
  - Pandas, JSON, threading
- **PostgreSQL**
  - Tables: `Trip`, `Breadcrumb`
- **Mapbox GL**
  - For dynamic route mapping
- **GeoJSON**
  - Format for spatial data
- **Git / GitHub** for version control

---

## 📁 Project Structure

```bash
.
├── publisher.py         # Pulls TriMet API data and publishes to GCP Pub/Sub
├── Subscriber.py        # Subscriber with validation, enrichment, and PostgreSQL ingestion
├── subscriber.py        # Writes raw messages to file
├── processjson.py       # Data validation, speed calc, DB insertions from JSON files
├── pub.sh               # Shell script to run the publisher
├── vehicle_ids.csv      # Input list of vehicle IDs to track
├── received_msg/        # Directory for storing raw JSON messages
