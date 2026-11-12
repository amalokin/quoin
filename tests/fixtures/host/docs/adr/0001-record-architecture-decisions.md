# 1. Record architecture decisions

## Status

Accepted

## Context

Choices about how svc is built are made in review threads and then forgotten. The next maintainer has to guess why the
code is the way it is, and a decision made once is easily made again the other way.

## Decision

We record each decision that shapes the service as an architecture decision record (ADR): a short file in `docs/adr/`,
named `NNNN-title.md` and numbered in the order the decisions are made. An ADR has four parts: Status, Context,
Decision and Consequences. An accepted ADR is not rewritten. A later ADR that changes the decision supersedes it, and
both say so in their Status.

## Consequences

A reviewer can ask for an ADR when a change makes a decision, and a newcomer can read the records in order to see how
the service got its shape. A record costs a few minutes to write and is easy to skip, so a change that makes a decision
without one is sent back in review.
