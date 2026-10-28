# Nila Security Lab

The mobile Security Lab is an **authorized, non-invasive learning checklist** for security reviews of systems you own or are explicitly permitted to test.

## Included
- Scope/permission acknowledgement before creating a review plan.
- OWASP-aligned checklists for attack-surface inventory, authentication/session handling, authorization and IDOR, input handling, configuration/secrets, APIs/business logic, dependencies/source review, and AI/LLM security.
- Local completion state and JSON report export.
- The target string is not fetched and no scan, exploit, login attempt, or network request is performed by this module.

## Suggested workflow
1. Define written scope, approved hosts/apps, testing window, excluded assets, and request limits.
2. Use staging and synthetic accounts/data where possible.
3. Review source code and dependency findings; validate hypotheses carefully in the authorized environment.
4. Document evidence, impact, remediation and retest results.
5. Add regression tests for confirmed bugs.

## References
- OWASP Web Security Testing Guide: https://owasp.org/projects/web-security-testing-guide
- OWASP WSTG testing should stay within the engagement's defined scope.

This feature teaches methodology and tracks a review plan. It is not a vulnerability scanner and does not claim that a target is secure.
