---
title: Early Autism Detection
emoji: 🧩
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Early Autism Detection

A multimodal autism screening system that combines:

- Eye-Gaze Analysis
- Facial Feature Analysis
- Behavioral Questionnaire Assessment
- LLM-based Report Generation

## Features

### Level 1: Eye-Gaze Analysis
Extracts eye movement features and predicts autism-related patterns using a Random Forest classifier.

### Level 2: Facial Analysis
Uses a ResNet50-based deep learning model to identify facial characteristics associated with Autism Spectrum Disorder.

### Level 3: Behavioral Assessment
Uses a CatBoost classifier trained on autism screening questionnaire responses and demographic information.

### Report Generation
Combines predictions from all modules and generates an explainable autism screening report using Google's Gemini API.

## API Endpoints

### Health Check

```http
GET /
```

### Eye Analysis

```http
POST /predict-eye
```

### Face Analysis

```http
POST /predict-face
```

### Questionnaire Analysis

```http
POST /predict-ques
```

### Generate Report

```http
GET /generate-report
```

### Download PDF Report

```http
GET /download-report
```

## Technologies

- FastAPI
- PyTorch
- CatBoost
- Scikit-Learn
- Google Gemini
- ReportLab
- Docker

## Deployment

This application is deployed as a Docker-based Hugging Face Space.
