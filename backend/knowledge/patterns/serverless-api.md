# Serverless API Pattern

## Overview
Serverless APIs leverage managed compute (Functions-as-a-Service) for API endpoints, eliminating server management and scaling automatically with demand.

## When to Use
- Variable/unpredictable traffic patterns
- Simple CRUD or transformation APIs
- Cost optimization for low-traffic endpoints
- Rapid prototyping and MVP development

## Architecture
- API Gateway (AWS API Gateway, Azure API Management)
- Function runtime (Lambda, Azure Functions, Cloud Functions)
- Managed database (DynamoDB, Cosmos DB)
- Object storage for static assets

## Best Practices
1. Keep functions small and focused (single responsibility)
2. Minimize cold start impact (provisioned concurrency if needed)
3. Use environment variables for configuration
4. Implement proper error handling and DLQ
5. Set appropriate timeout and memory limits

## Limitations
- Execution time limits (typically 15 minutes max)
- Stateful operations require external storage
- Vendor lock-in considerations
- Debugging and local development complexity

## Hybrid Approach
Combine serverless for API layer with containers for complex business logic requiring longer execution or specific runtime dependencies.
