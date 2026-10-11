# Locate the cost before changing the model

Use the supplied workload and separate construction, first compilation/setup,
parameter updates, solve-call wall time, and reported solver time. Some solver
statistics omit costs or use different boundaries. Distinguish one-shot latency
from repeated throughput. State unavailable measurements; a large problem alone
does not establish the bottleneck.

- Construction/compilation: inspect scalar loops, accidental broadcasting,
  dense identities/Gram matrices, unnecessary auxiliaries, and lost sparsity.
  Vectorization should preserve axes and the original constraints.
- Repeated solves: build once when structure is fixed, use Parameters for changing
  data, and check DPP. Compilation caching, warm starts, symbolic factorization,
  and numerical factorization reuse are distinct. Matrix changes can invalidate
  numerical reuse even when compilation is cached.
- Solver work: read [solver routing](solver-routing.md); inspect representation,
  conditioning, residuals, accuracy settings, and sparsity/fill-in. Polyhedrality
  is one signal, not proof that active-set methods win.

Bounds attributes can reduce explicit rows for particular interfaces, while
explicit constraints expose requested multipliers. Preserve dual requirements
when proposing that change. Fewer rows or a smaller cone do not by themselves
prove lower runtime. Read [quadratic representations](quadratics.md) before
changing a quadratic term; include factor/operator assembly and update costs.

Offer one justified improvement or a small comparison proportional to the issue.
Keep data, settings, versions, and timing boundaries reproducible, and compare
original-domain residuals and objective accuracy. Do not describe default
solver settings as equivalent accuracy across backends. If execution or relevant
hardware is unavailable, give a hypothesis and measurement plan, not a speedup.

Native deployment (`cvx-canon`) may help when modeling overhead is consequential;
it is not an automatic remedy for slow numerical convergence. Custom algorithm
implementation requires a separate request and evidence that existing interfaces
cannot meet the workload. These boundaries do not require sibling skills to be
installed.

Sources: [CVXPY solver features](https://www.cvxpy.org/tutorial/solvers/index.html),
[DPP](https://www.cvxpy.org/tutorial/dpp/index.html).
