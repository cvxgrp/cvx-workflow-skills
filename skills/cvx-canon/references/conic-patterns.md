# Exact conic patterns

Use the selected backend's cone ordering and packing. The formulas below specify
slack expressions; convert every affine cone expression `F*x+g in K` to
`A=-F,b=g`. Cone membership uses the closed cone, including its boundary.

| Original expression | Native representation and assumptions |
|---|---|
| `G*x<=h`; `E*x=f` | Slack `h-G*x` nonnegative; slack `f-E*x` zero |
| `||F*x+g||₂<=a.T*x+b` | SOC slack `[a.T*x+b; F*x+g]`; first coordinate automatically nonnegative |
| `||u||₁<=t` | Auxiliaries `v>=u`, `v>=-u`, `sum(v)<=t` |
| `||u||∞<=t` | `-t<=u<=t`, using broadcast scalar `t` deliberately |
| `u.T@Q@u<=t`, `Q=R.T@R` PSD | SOC `[t+1; 2*R@u; t-1]`; factor orientation matters |
| `||u||²<=t*v`, `t,v>=0` | SOC `[t+v; 2*u; t-v]`; rotated SOC encoded as ordinary SOC |
| `exp(u)<=t` | Exponential cone `(u,1,t)` |
| `log(sum(exp(u_i)))<=t` | Auxiliaries `v_i`, cones `(u_i-t,1,v_i)`, and `sum(v)<=1` |
| `u*log(u/v)<=t`, `u,v>=0` | Exponential cone `(-t,u,v)`, with the closed relative-entropy domain |
| `u^alpha*v^(1-alpha)>=abs(w)` | Power cone `(u,v,w)`, `u,v>=0`, `0<alpha<1` |
| `X=F0+sum(x_i*Fi) PSD` | Cone slack `svec(X)`; symmetric `Fi` and backend-specific `svec` |

For `||u||²/v<=t` on `v>0`, the rotated-SOC closure additionally permits `v=0`
only when `u=0,t>=0`. Use that closure only if it matches the original extended
function/domain. Do not replace a strict positive domain with its closure without
justification. Strict inequalities are not directly imposed by these solvers;
an epsilon bound changes the problem unless requested or mathematically justified.

For a PSD quadratic factor use Cholesky only when positive definite; use a
rank-revealing factorization for semidefinite matrices. Numerical PSD tolerance
does not authorize an unreported alteration of the objective. Preserve native
quadratic objectives when efficient; epigraphs are useful for quadratic constraints
or when a factor/operator representation avoids a dense Hessian.

Weighted geometric means: discard zero weights, require positive remaining
weights summing to one, and nonnegative bases. A single remaining weight reduces
to a linear relation. Moreau's generalized power cone
can represent `prod(u_i**alpha_i)>=||w||₂` directly. With a scalar nonnegative
hypograph variable `t`, its absolute-value cone is valid; if `t` can be negative,
do not replace `t<=geomean(u)` with `abs(t)<=geomean(u)`. A positive-weight
power-cone tree is another exact representation; combine subproducts with the
ratios of their total weights. Do not rationalize requested exponents into an
undisclosed approximation.

Complex affine expressions can be split into real and imaginary coordinates
when justified. For complex Hermitian PSD matrices, use SCS's documented complex
packing or the exact real block embedding `[[Re X,-Im X],[Im X,Re X]] PSD`.
Do not apply the real packing helper directly to complex inputs.

Compare representations by auxiliaries, row counts, cone sizes, fill-in, and
conditioning, then measure if performance matters. SOC-to-PSD embeddings and
large dense Gram matrices can be much more expensive than the original structure.

The [SOCP example](../assets/native_socp.py) preserves a changing quadratic
objective offset and original-variable recovery on Moreau and SCS.
