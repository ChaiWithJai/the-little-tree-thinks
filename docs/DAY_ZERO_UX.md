# Bonsai Workbench: Day 0 UX

The first-use experience is organized around one capable agent and the work a person wants to finish, not around model modes or the harness that performs it.

## Canonical references translated into decisions

- Apple Human Interface Guidelines, Onboarding: make the first experience fast, optional, and useful immediately. Bonsai starts with one universal request and postpones model and pipeline detail.
- Apple Human Interface Guidelines, Design Principles: preserve agency and recovery. Every failed run keeps the prompt, offers a retry, and lets the person edit instead.
- GOV.UK Design System, Start using a service: explain what the service does before the first action and label actions for the outcome. The landing screen says what remains local, accepts any outcome in the user’s words, and treats journeys as optional examples.
- Microsoft Fluent 2, Onboarding: teach in context and set expectations. Guidance changes with the chosen job; progress explains what is happening and how long local work normally takes.
- WCAG 2.2: preserve logical focus, visible focus, and sufficiently large controls. State changes move focus to the prompt, error, or completed result instead of resetting the reading order.

## Experience states

1. **Orient** — ask the agent for any outcome, borrow a starter journey, or resume the latest work.
2. **Route** — infer the best local capability from the request without making the user choose a model mode.
3. **Prompt** — preserve the desired result and show only the one configuration that affects that job.
4. **Work** — show a short, plain-language plan and a realistic time expectation.
5. **Review** — lead with the artifact, then ask whether to keep, change, or restart it.
6. **Inspect** — reveal model, validation, and trace detail only on request.
7. **Use** — open or export the artifact from the same result view.

## Acceptance criteria

- A first-time user can describe any outcome without understanding models, corpora, adapters, or finite-state machinery.
- Starter journeys demonstrate breadth but never gate or narrow the universal request.
- Empty prompts cannot be submitted and explain what is needed inline.
- Failures preserve the prompt and offer both retry and edit paths.
- Completed work receives focus, exposes a clear decision, and can be exported without entering system configuration.
- Technical run detail remains available for expert inspection without competing with the primary result.
- The journey works at desktop and mobile content breakpoints and follows a logical keyboard order.
