# Nguyen Van An

Senior Backend Engineer · Ho Chi Minh City, Vietnam · nguyen.van.an@example.com · +84 90 123 4567

## Summary

Backend engineer with 7 years building payment and banking systems in Python. Led the migration of a monolithic billing platform to microservices on Kubernetes and kept the checkout service above 99.95% availability.

## Experience

### Senior Backend Engineer - Vertex Payments (2021 - present)

- Led a team of 5 engineers rebuilding the payment gateway API in FastAPI; the service now processes 1.2M transactions per day with p99 latency under 180 ms.
- Designed idempotent Stripe and Adyen integrations handling 300K refunds per month with zero double-charges reported since launch.
- Migrated 14 services from a Django monolith to event-driven microservices on AWS EKS, cutting deployment time from 45 minutes to 6.
- Wrote Terraform modules for the EKS, RDS and ElastiCache infrastructure now used by 3 product teams.
- Added a Kafka-based event pipeline between checkout and settlement; reconciliation lag dropped from 2 hours to under 5 minutes.

### Backend Engineer - Saigon Digital Bank (2018 - 2021)

- Built REST APIs for account opening and KYC flows in Python with Django and FastAPI; API contract tests run in GitHub Actions on every pull request.
- Tuned PostgreSQL queries and introduced Redis caching for the customer profile service, reducing average response time from 900 ms to 120 ms.
- Containerised 9 legacy services with Docker and shipped them to a Kubernetes cluster managed with Helm.

### Junior Software Engineer - FPT Software (2016 - 2018)

- Developed internal tools in Python and built CI pipelines with GitHub Actions for 4 product teams.
- Maintained PostgreSQL schemas and wrote migration scripts for a customer data platform.

## Skills

Python, FastAPI, Django, PostgreSQL, Redis, Docker, Kubernetes, Helm, AWS (EKS, RDS, ElastiCache, Lambda), Terraform, Kafka, RabbitMQ, REST API design, microservices, GitHub Actions, Grafana, Stripe, Adyen

## Education

BSc Computer Science, University of Science, Ho Chi Minh City (2016)

## Certifications

AWS Certified Solutions Architect - Associate (2022) · CKA: Certified Kubernetes Administrator (2023)