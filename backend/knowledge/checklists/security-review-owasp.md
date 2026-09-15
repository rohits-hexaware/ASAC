# OWASP Security Review Checklist

## OWASP API Security Top 10

### API1: Broken Object Level Authorization
- [ ] Authorization checks on every object access
- [ ] User can only access their own resources
- [ ] Admin endpoints separately protected

### API2: Broken Authentication
- [ ] Strong authentication mechanisms (OAuth2/OIDC)
- [ ] Token expiration and rotation implemented
- [ ] Brute force protection enabled

### API3: Broken Object Property Level Authorization
- [ ] Response filtering prevents mass assignment
- [ ] Sensitive fields excluded from responses
- [ ] Input validation on all properties

### API4: Unrestricted Resource Consumption
- [ ] Rate limiting on all endpoints
- [ ] Request size limits enforced
- [ ] Pagination on list endpoints

### API5: Broken Function Level Authorization
- [ ] Role-based access on all functions
- [ ] Admin functions require elevated privileges
- [ ] Function-level authorization tested

### API6: Unrestricted Access to Sensitive Business Flows
- [ ] Business logic abuse prevention
- [ ] Transaction limits and velocity checks
- [ ] Bot detection on sensitive flows

### API7: Server Side Request Forgery (SSRF)
- [ ] URL validation on external requests
- [ ] Allowlist for outbound connections
- [ ] Network segmentation limits blast radius

### API8: Security Misconfiguration
- [ ] Security headers configured
- [ ] Default credentials changed
- [ ] Unnecessary features disabled

### API9: Improper Inventory Management
- [ ] API inventory maintained
- [ ] Deprecated endpoints sunset plan
- [ ] Version management strategy

### API10: Unsafe Consumption of APIs
- [ ] Third-party API responses validated
- [ ] HTTPS enforced for external calls
- [ ] Timeout and retry limits set
