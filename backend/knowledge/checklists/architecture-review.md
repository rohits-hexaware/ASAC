# Architecture Review Checklist

## Business Alignment
- [ ] Architecture supports stated business goals
- [ ] Non-functional requirements addressed (performance, scalability, availability)
- [ ] Total cost of ownership estimated
- [ ] Timeline feasibility validated

## Technical Design
- [ ] Clear separation of concerns and bounded contexts
- [ ] API contracts defined and versioned
- [ ] Data model and storage strategy documented
- [ ] Integration patterns specified (sync vs async)
- [ ] Error handling and retry strategies defined

## Scalability & Performance
- [ ] Horizontal scaling strategy defined
- [ ] Caching strategy documented
- [ ] Load testing plan included
- [ ] Performance SLAs defined

## Resilience & Availability
- [ ] Single points of failure identified and mitigated
- [ ] Disaster recovery plan documented
- [ ] RTO/RPO targets defined
- [ ] Circuit breaker and bulkhead patterns applied

## Operability
- [ ] Monitoring and alerting strategy defined
- [ ] Logging standards followed
- [ ] Deployment strategy (CI/CD) documented
- [ ] Runbooks for common operations

## Migration (if applicable)
- [ ] Migration strategy and phasing documented
- [ ] Rollback plan defined
- [ ] Data migration approach validated
- [ ] Parallel run period planned
