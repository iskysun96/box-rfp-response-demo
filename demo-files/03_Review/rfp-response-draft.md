# Kestrel Ridge Systems

## Security & Integration Response

**Solicitation:** MCSO-RFP-2026-081  
**Issued by:** Meridian Civic Services Office  
**Response status:** Ready to share with the customer

Thank you for the opportunity to respond. The answers below are based on Kestrel Ridge Systems’ approved company materials. Where the approved materials do not specify a requested implementation detail, this response does not make an assumption or commitment.

## Q1 — Enterprise identity and administrator controls
**Response:** The service supports SAML 2.0 and OpenID Connect single sign-on. Customer administrators can configure identity-provider metadata, domain restrictions, and role mappings in the administrative console, including mapping identity-provider groups to workspace roles. Administrators can disable users and revoke API credentials from the administrative console. Privileged administrative access is restricted to authorized personnel and is subject to audit logging and periodic access review. Administrative configuration changes and API credential events are recorded in the workspace audit trail. The approved materials do not specify MFA, SCIM, delegated administration, or other federation protocols beyond SAML/OIDC.
**Source:** product-and-integration-overview.pdf; security-and-access-controls.pdf

## Q2 — Encryption and handling of customer content in transit and at rest
**Response:** Customer content is protected in transit using TLS 1.2 or higher. Production customer content is encrypted at rest using AES-256 encryption. The approved materials do not specify customer-controlled key management, backup-encryption details, or encryption treatment for metadata.
**Source:** security-and-access-controls.pdf

## Q3 — Retention, deletion, and customer-request handling for content
**Response:** Customer content remains under the customer’s control. Workspace administrators may delete content and manage member access through the administrative console. Content is retained while the workspace remains active, subject to customer-directed deletion. Deleted content is removed from active service systems and scheduled for removal from routine backups within 30 days. Following verified account closure, content is scheduled for deletion under the same backup-removal period unless a documented legal or security hold applies. Support personnel access customer content only when necessary to resolve a support request and under role-based access controls. The approved materials do not specify the customer-request submission workflow or timelines for non-routine or archival backups.
**Source:** data-handling-and-retention-policy.pdf

## Q4 — Recovery objectives and testing of business continuity readiness
**Response:** Recovery targets are an 8-hour recovery time objective (RTO) and a 4-hour recovery point objective (RPO) for restoring the Knowledge Workspace. The continuity plan defines incident command, customer communication, restoration priorities, and post-incident review. The plan is exercised annually; recovery controls and contact paths are reviewed quarterly, with findings tracked through the technology risk-management process. These recovery objectives are targets, not a guarantee of uninterrupted service. Customer responsibilities include maintaining current identity-provider configuration, designated administrators, and export procedures. The approved materials do not specify test results, third-party validation, or SLA commitments tied to the RTO/RPO.
**Source:** business-continuity-plan.pdf

## Q5 — API integration controls and operational monitoring
**Response:** The product provides a versioned REST API for approved integrations. API credentials are issued per integration, scoped to configured permissions, and can be revoked by a customer administrator. Administrative configuration changes and API credential events are recorded in the workspace audit trail. Service health and integration failures are monitored by the operations team and routed through the incident process. Role mapping and least-privilege assignment are customer administrative responsibilities. The approved materials do not specify API authentication methods, token types, rate limits, or integration SLAs and alert thresholds.
**Source:** product-and-integration-overview.pdf; security-and-access-controls.pdf

## Approved source materials

- product-and-integration-overview.pdf
- security-and-access-controls.pdf
- data-handling-and-retention-policy.pdf
- business-continuity-plan.pdf
