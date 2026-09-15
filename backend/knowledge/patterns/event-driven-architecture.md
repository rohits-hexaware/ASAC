# Event-Driven Architecture Pattern

## Overview
Event-driven architecture (EDA) uses events to trigger and communicate between decoupled services. Producers publish events to an event bus; consumers react asynchronously.

## When to Use
- Need for loose coupling between services
- Real-time data processing requirements
- Complex workflows spanning multiple domains
- Audit trails and event sourcing scenarios

## Core Components
1. **Event Producers** - Services that emit domain events
2. **Event Bus/Broker** - Kafka, Azure Event Hubs, AWS EventBridge
3. **Event Consumers** - Services that react to events
4. **Event Store** - Optional persistence for event sourcing

## Event Types
- **Domain Events** - Business-significant occurrences (OrderPlaced, PointsEarned)
- **Integration Events** - Cross-boundary communication
- **Notification Events** - Alerts and triggers

## Patterns
- **Event Notification** - Lightweight, fire-and-forget
- **Event-Carried State Transfer** - Events carry full data payload
- **Event Sourcing** - State derived from event log

## Considerations
- Eventual consistency must be acceptable
- Idempotent consumers required
- Schema evolution and versioning strategy needed
- Dead letter queues for failed processing
