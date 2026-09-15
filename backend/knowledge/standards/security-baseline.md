# Enterprise Security Baseline

## Overview
Minimum security controls required for all enterprise applications regardless of classification level.

## Identity & Access Management
- Centralized identity provider (OAuth2/OIDC)
- Multi-factor authentication for all users
- Role-based access control (RBAC)
- Principle of least privilege
- Regular access reviews (quarterly)

## Network Security
- TLS 1.2+ for all communications
- Network segmentation (VPC/VNet isolation)
- Web Application Firewall (WAF) on public endpoints
- DDoS protection enabled
- Private endpoints for backend services

## Data Protection
- Encryption at rest (AES-256) for all data stores
- Encryption in transit (TLS) for all connections
- Key management via cloud KMS/HSM
- Data classification tagging enforced
- Secure deletion procedures

## Application Security
- Secure SDLC with security gates
- Static and dynamic application security testing (SAST/DAST)
- Dependency vulnerability scanning
- Input validation and output encoding
- Security headers (CSP, HSTS, X-Frame-Options)

## Monitoring & Response
- Centralized logging to SIEM
- Security event alerting
- Incident response plan documented
- Regular penetration testing (annual minimum)
