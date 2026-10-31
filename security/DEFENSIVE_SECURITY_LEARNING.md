# Nila Defensive Security Learning Pack

This pack teaches Nila to understand defensive cybersecurity findings. It does not turn Nila into an autonomous attack agent.

## Approved scope

- Only Nila's own repository, systems the user owns, or targets for which the user has explicit written permission.
- Prefer static analysis and passive checks first.
- Any network scan must have an explicitly supplied target and a human authorization step.
- Findings are evidence to review, not proof that a vulnerability is exploitable.
- Nila may summarize, classify, explain, suggest fixes, and create human-reviewed improvement proposals.
- Nila must not execute exploit payloads, brute-force logins, steal credentials, deploy malware, evade detection, or scan arbitrary public targets.

## Tools to learn

| Tool | Defensive purpose | Safe learning task |
|---|---|---|
| Semgrep | Static application security testing (SAST) | Explain insecure code patterns and suggest a patch |
| CodeQL | Code scanning / data-flow analysis | Explain an alert and trace the risky data flow |
| Trivy | Dependency, filesystem, container and configuration scanning | Prioritize vulnerable dependencies and misconfigurations |
| OWASP ZAP Baseline | Passive web application checks | Explain passive alerts for an explicitly authorized URL |

Official documentation:
- Semgrep: https://semgrep.dev/docs/
- CodeQL: https://docs.github.com/en/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning-with-codeql
- Trivy: https://www.trivy.dev/docs/latest/
- OWASP ZAP Automation: https://www.zaproxy.org/docs/automate/automation-framework/

## Nila learning cycle

1. Collect a report from an approved scanner.
2. Store the tool name, version, scan time, target scope, rule/CVE identifier, severity, evidence, and report reference.
3. Explain the finding in plain language, including uncertainty and possible false positives.
4. Suggest a minimal defensive fix and a regression test.
5. Require human review before applying any code change.
6. Re-scan after the fix and record whether the finding was resolved.
7. Evaluate explanation quality and false-positive handling; do not self-promote unverified fixes.

## Safety gates

- No scan runs from Nila's chat response alone.
- Network scanning requires a human-triggered workflow, a target URL, and confirmation that the target is authorized.
- ZAP in this starter pack is the passive Baseline scan only; do not silently change it to an active scan.
- Scanner credentials, API tokens, database passwords, and reports containing secrets must not be committed.
- Do not send private source code or scan reports to an external LLM unless the user explicitly approves that data transfer.

## Manual local commands

Run these only against the local Nila checkout:

```bash
semgrep scan --config auto .
trivy fs --scanners vuln,misconfig,secret .
```

Review every finding before treating it as a confirmed vulnerability. These tools are not a substitute for secure design, code review, or a professional penetration test.
