# Architecture Decision Record (ADR) Format

## Template

```markdown
# ADR-{number}: {Title}

## Status
{Proposed | Accepted | Deprecated | Superseded by ADR-XXX}

## Date
{YYYY-MM-DD}

## Context
What is the issue that we're seeing that is motivating this decision or change?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult because of this change?

### Positive
- {benefit 1}
- {benefit 2}

### Negative
- {trade-off 1}
- {trade-off 2}

### Neutral
- {observation}

## Alternatives Considered
1. **{Alternative 1}** - {Why rejected}
2. **{Alternative 2}** - {Why rejected}

## References
- {Link to related documents, RFCs, or discussions}
```

## Best Practices
- One decision per ADR
- Write ADRs before or during implementation, not after
- Keep ADRs immutable; supersede rather than edit
- Store ADRs in version control alongside code
- Reference ADRs in HLD and design documents

## Example ADR Topics
- Technology stack selection
- Architecture pattern choice
- Database selection
- Authentication approach
- Deployment strategy
- Integration protocol choice
