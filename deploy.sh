#!/bin/bash
# Document Review RAG - Cloud Run Deployment Script

PROJECT_ID="document-review-478514"
REGION="asia-northeast3"
SERVICE_NAME="document-review-rag"
API_KEY="AIzaSyC--9NkP3eVCZMHbvxpqDXTlWmo92KOYUs"

echo "========================================="
echo "Deploying Document Review RAG to Cloud Run"
echo "========================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "========================================="

# Enable required APIs
echo "Enabling Cloud Build and Cloud Run APIs..."
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com --project=$PROJECT_ID

# Submit build to Cloud Build
echo "Starting Cloud Build..."
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_GOOGLE_API_KEY="$API_KEY" \
  --project=$PROJECT_ID

echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo "Service URL:"
gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID --format='value(status.url)'
