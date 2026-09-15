# Data Classification Standard

## Classification Levels

### Public
- Information approved for public release
- No encryption requirements beyond standard TLS
- Example: marketing materials, public API documentation

### Internal
- Business information not intended for external parties
- Encryption at rest recommended
- Access restricted to employees and authorized contractors
- Example: internal reports, architecture documents

### Confidential
- Sensitive business data requiring protection
- Encryption at rest and in transit mandatory
- Access on need-to-know basis with audit logging
- Example: customer PII, financial records, loyalty transaction data

### Restricted
- Highly sensitive data with regulatory requirements
- Strongest encryption and access controls
- Data loss prevention (DLP) policies enforced
- Example: payment card data (PCI), health records (HIPAA)

## Handling Requirements by Level
| Control | Public | Internal | Confidential | Restricted |
|---------|--------|----------|--------------|------------|
| Encryption at Rest | Optional | Recommended | Required | Required + HSM |
| Encryption in Transit | TLS | TLS | TLS 1.2+ | TLS 1.3 + mTLS |
| Access Logging | No | Recommended | Required | Required + Alerting |
| Data Retention | N/A | Per policy | Per policy + Legal hold | Regulatory minimum |

## Labeling
All data stores and API responses must include classification metadata tags for automated policy enforcement.
