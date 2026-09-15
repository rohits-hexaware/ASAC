# API Gateway Best Practices

## Purpose
Central entry point for all client requests, providing cross-cutting concerns: authentication, rate limiting, routing, and monitoring.

## Key Responsibilities
1. **Request Routing** - Direct traffic to appropriate backend services
2. **Authentication** - Validate tokens, API keys
3. **Rate Limiting** - Protect backends from overload
4. **Request/Response Transformation** - Protocol translation, header manipulation
5. **Caching** - Cache responses for read-heavy endpoints
6. **Monitoring** - Request logging, metrics, tracing

## Security Controls
- TLS termination at gateway
- JWT/OAuth2 token validation
- IP allowlisting for B2B partners
- Request size limits
- WAF integration

## Patterns
- **Backend for Frontend (BFF)** - Separate gateways per client type
- **API Composition** - Aggregate multiple backend calls
- **Circuit Breaker** - Fail fast when backends unhealthy

## Cloud Options
- AWS API Gateway + Lambda authorizers
- Azure API Management
- Kong / Apigee for hybrid deployments

## Anti-patterns
- Business logic in gateway (keep it thin)
- Single gateway for all environments
- Missing request correlation IDs
