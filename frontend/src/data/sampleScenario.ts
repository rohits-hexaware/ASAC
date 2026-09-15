import type { AnalyzeRequest } from '../types';

export const SAMPLE_SCENARIO: AnalyzeRequest = {
  project_name: 'Customer Loyalty Platform Modernization',
  domain: 'Retail / Customer Loyalty',
  business_goals:
    'Modernize legacy loyalty platform to support omnichannel engagement, ' +
    'real-time points accrual, personalized offers, and 40% reduction in operational costs. ' +
    'Target 2M active members with sub-200ms API response times.',
  functional_requirements:
    'Member registration and profile management\n' +
    'Real-time points earn and burn at POS, e-commerce, and mobile\n' +
    'Tier-based rewards program with automatic upgrades\n' +
    'Partner coalition integration (airlines, hotels)\n' +
    'Personalized offer engine based on purchase history\n' +
    'Self-service portal for members to view balance and redeem rewards\n' +
    'Admin dashboard for campaign management and reporting\n' +
    'Migration of 1.5M existing member records from legacy system',
  constraints: {
    cloud: 'Azure (existing enterprise agreement)',
    budget: '$1.2M over 18 months',
    timeline: 'Phase 1 MVP in 6 months, full migration in 18 months',
  },
  non_functional_requirements:
    '99.95% availability for earn/burn operations\n' +
    'API latency < 200ms p95 for balance queries\n' +
    'Support 10K transactions/minute at peak\n' +
    'GDPR and CCPA compliance for member data\n' +
    'RPO 1 hour, RTO 4 hours for disaster recovery\n' +
    'Horizontal scaling for seasonal traffic spikes',
  compliance:
    'GDPR, CCPA, PCI-DSS (for points-as-payment), SOC 2 Type II, ' +
    'enterprise data classification (Confidential for PII)',
};
