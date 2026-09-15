# Strangler Fig Migration Pattern

## Overview
The Strangler Fig pattern incrementally replaces a legacy system by routing functionality to new services while the legacy system remains operational.

## When to Use
- Modernizing monolithic legacy applications
- Risk-averse migration requiring gradual cutover
- Systems that cannot afford downtime

## Implementation Steps
1. Identify bounded contexts in the legacy system
2. Build new services alongside legacy
3. Route traffic incrementally via facade/proxy
4. Migrate data domain by domain
5. Decommission legacy components when fully replaced

## Key Components
- **Facade/Router** - Directs traffic to legacy or new system
- **Anti-Corruption Layer** - Translates between legacy and new models
- **Migration Pipeline** - Syncs data between systems during transition

## Benefits
- Reduced migration risk
- Continuous delivery of value
- Rollback capability at each step
- Team can learn new stack incrementally

## Common Pitfalls
- Running dual systems too long increases cost
- Data synchronization complexity
- Incomplete domain boundaries leading to tight coupling
