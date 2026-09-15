# Cloud-Native Microservices Pattern

## Overview
Cloud-native microservices decompose applications into independently deployable services, each owning a bounded context. Services communicate via well-defined APIs and async events.

## When to Use
- Large, complex domains requiring team autonomy
- Need for independent scaling of components
- Cloud-first deployment with container orchestration (Kubernetes, ECS)

## Key Principles
1. **Single Responsibility** - Each service owns one business capability
2. **Decentralized Data** - Database per service pattern
3. **Smart Endpoints, Dumb Pipes** - Logic in services, not middleware
4. **Design for Failure** - Circuit breakers, retries, bulkheads

## Reference Architecture
- API Gateway for external traffic
- Service mesh for inter-service communication (optional)
- Container orchestration platform
- Centralized logging and distributed tracing
- CI/CD pipelines per service

## Trade-offs
| Benefit | Cost |
|---------|------|
| Independent deployment | Operational complexity |
| Technology diversity | Integration testing harder |
| Fault isolation | Network latency |
| Team scalability | Data consistency challenges |

## Anti-patterns
- Distributed monolith (tight coupling between services)
- Shared database across services
- Chatty interfaces with excessive inter-service calls
