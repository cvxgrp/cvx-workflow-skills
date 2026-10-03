# Convex-concave procedure

Use for a requested local approach to an appropriate difference-of-convex (DC)
problem. Prefer an exact convex reformulation when one exists. A DC decomposition
is an implementation choice with effects on conditioning/convergence, not proof
that a nonconvex problem has become convex.

Write a minimization objective `f0(x)-g0(x)` and inequalities
`fi(x)-gi(x)<=0`, with each `f,g` convex on the retained domain. At `xk` replace
`gi` with its affine **underestimator**
`gi_hat(x)=gi(xk)+grad(gi(xk)).T@(x-xk)`.
Then solve the convex subproblem with objective `f0-g0_hat`
and constraints `fi-gi_hat<=0`. This upper-bounds each original DC expression;
linearizing the wrong sign gives an outer relaxation instead. The approximation
must be tangent at `xk`. Fixed affine/convex constraints and variable domains stay
in every subproblem. Represent suitable DC equalities as two inequalities if
needed, accounting for the resulting feasibility/initialization difficulty.

## Native loop

1. Choose a start in the functions' domains; for ordinary CCP require original
   feasibility. Assemble the convex parts once when possible.
2. Evaluate values/gradients at the current original variables. Update **all**
   affected native costs, rows, RHS values, and offsets. Moreau can reset matrix
   values on a fixed compiled structure; SCS needs a new workspace when rows change.
3. Solve with an explicit inner accuracy and iteration/time bound. Handle inner
   failure before interpreting or accepting a new iterate.
4. Recover original variables, evaluate the original objective and violations,
   and check both scaled iterate/objective change and original feasibility.
   Retain a best original-feasible candidate separately from the last iterate.

For infeasible starts, penalty CCP introduces `si>=0` and
`fi-gi_hat<=si`, penalizing `rho*sum(si)` in the convex objective. State the
initial penalty, bounded increase rule, iteration cap, and original-feasibility
target. Positive slacks mean the iterate need not satisfy the original problem.
Do not report a stable penalized iterate as a feasible original solution.
Nonconvex domains still need valid starts; penalty slacks do not fix undefined logs.

Damping/proximal terms or trust regions can help unstable steps. Specify their
effect and preserve domains; they are not automatic global convergence guarantees.
With inexact inner solves, verify feasibility and observed objective behavior
rather than asserting exact monotone descent. A stalled or failed run is a local
method outcome, not proof of global infeasibility or optimality.

## Worked constraint

For `min 0.5*||x-a||²` subject to `||x||²>=r²`, `r>0`, take
`f(x)=r²`, `g(x)=||x||²`. The CCP inequality is
`r²+||xk||²-2*xk.T@x<=0`; its native nonnegative-cone row has
`A=-2*xk.T`, `b=-(r²+||xk||²)`.
With `xk` feasible it is an inner half-space containing `xk`. At `xk=0` it is
infeasible; choose a nonzero feasible start or use penalty CCP deliberately.
The [native loop example](../assets/ccp_outside_ball.py) demonstrates this ordinary
CCP path and checks original feasibility. It is not a general nonconvex solver.

Background: [Lipp and Boyd, Variations and extension of the convex-concave
procedure](https://link.springer.com/article/10.1007/s11081-015-9294-x).
