# `sqlite-vec`

[![](https://dcbadge.vercel.app/api/server/VCtQ8cGhUs)](https://discord.gg/Ve7WeCJFXk)

An extremely small, "fast enough" vector search SQLite extension that runs
anywhere! A successor to [`sqlite-vss`](https://github.com/asg017/sqlite-vss)

<!-- deno-fmt-ignore-start -->

> [!IMPORTANT]
> _`sqlite-vec` is a pre-v1, so expect breaking changes!_

<!-- deno-fmt-ignore-end -->

- Store and query float, int8, and binary vectors in `vec0` virtual tables
- Written in pure C, no dependencies, runs anywhere SQLite runs
  (Linux/MacOS/Windows, in the browser with WASM, Raspberry Pis, etc.)
- Store non-vector data in metadata, auxiliary, or partition key columns

<p align="center">
  <a href="https://hacks.mozilla.org/2024/06/sponsoring-sqlite-vec-to-enable-more-powerful-local-ai-applications/">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./.github/logos/mozilla.dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="./.github/logos/mozilla.svg">
    <img alt="Mozilla Builders logo" width=400>
  </picture>
  </a>
</p>

<p align="center">
<i>
<code>sqlite-vec</code> is a
<a href="https://hacks.mozilla.org/2024/06/sponsoring-sqlite-vec-to-enable-more-powerful-local-ai-applications/">Mozilla Builders project</a>,
with additional sponsorship from
<a href="https://fly.io/"><img width=14px src="./.github/logos/flyio.small.ico"/> Fly.io </a>,
<a href="https://tur.so/sqlite-vec"><img width=14px src="./.github/logos/turso.small.ico"/> Turso</a>,
<a href="https://sqlitecloud.io/"><img width=14px src="./.github/logos/sqlitecloud.small.svg"/> SQLite Cloud</a>, and
<a href="https://shinkai.com/"><img width=14px src="./.github/logos/shinkai.small.svg"/> Shinkai</a>.
See <a href="#sponsors">the Sponsors section</a> for more details.
</i>
</p>

## Installing

See [Installing `sqlite-vec`](https://alexgarcia.xyz/sqlite-vec/installation.html)
for more details.

| Language       | Install                                              | More Info                                                                             |                                                                                                                                                                                                    |
| -------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Python         | `pip install sqlite-vec`                             | [`sqlite-vec` with Python](https://alexgarcia.xyz/sqlite-vec/python.html)             | [![PyPI](https://img.shields.io/pypi/v/sqlite-vec.svg?color=blue&logo=python&logoColor=white)](https://pypi.org/project/sqlite-vec/)                                                               |
| Node.js        | `npm install sqlite-vec`                             | [`sqlite-vec` with Node.js](https://alexgarcia.xyz/sqlite-vec/js.html)            | [![npm](https://img.shields.io/npm/v/sqlite-vec.svg?color=green&logo=nodedotjs&logoColor=white)](https://www.npmjs.com/package/sqlite-vec)                                                         |
| Ruby           | `gem install sqlite-vec`                             | [`sqlite-vec` with Ruby](https://alexgarcia.xyz/sqlite-vec/ruby.html)                 | ![Gem](https://img.shields.io/gem/v/sqlite-vec?color=red&logo=rubygems&logoColor=white)                                                                       |
| Go             | `go get -u github.com/asg017/sqlite-vec/bindings/go` | [`sqlite-vec` with Go](https://alexgarcia.xyz/sqlite-vec/go.html)                     | [![Go Reference](https://pkg.go.dev/badge/github.com/asg017/sqlite-vec-go-bindings/cgo.svg)](https://pkg.go.dev/github.com/asg017/asg017/sqlite-vec-go-bindings/cgo)                                              |
| Rust           | `cargo add sqlite-vec`                               | [`sqlite-vec` with Rust](https://alexgarcia.xyz/sqlite-vec/rust.html)                 | [![Crates.io](https://img.shields.io/crates/v/sqlite-vec?logo=rust)](https://crates.io/crates/sqlite-vec)                                                                                          |
| Datasette      | `datasette install datasette-sqlite-vec`             | [`sqlite-vec` with Datasette](https://alexgarcia.xyz/sqlite-vec/datasette.html)       | [![Datasette](https://img.shields.io/pypi/v/datasette-sqlite-vec.svg?color=B6B6D9&label=Datasette+plugin&logoColor=white&logo=python)](https://datasette.io/plugins/datasette-sqlite-vec)          |
| rqlite         | `rqlited -extensions-path=sqlite-vec.tar.gz`         | [`sqlite-vec` with rqlite](https://alexgarcia.xyz/sqlite-vec/rqlite.html)                        | [![rqlite](https://img.shields.io/badge/rqlite-sqlite_extensions-blue)](https://rqlite.io/docs/guides/extensions/)           |
| `sqlite-utils` | `sqlite-utils install sqlite-utils-sqlite-vec`       | [`sqlite-vec` with sqlite-utils](https://alexgarcia.xyz/sqlite-vec/sqlite-utils.html) | [![sqlite-utils](https://img.shields.io/pypi/v/sqlite-utils-sqlite-vec.svg?color=B6B6D9&label=sqlite-utils+plugin&logoColor=white&logo=python)](https://datasette.io/plugins/datasette-sqlite-vec) |
| Github Release |                                                      |                                                                                       | ![GitHub tag (latest SemVer pre-release)](https://img.shields.io/github/v/tag/asg017/sqlite-vec?color=lightgrey&include_prereleases&label=Github+release&logo=github)                              |


## Sample usage

```sql
.load ./vec0

create virtual table vec_examples using vec0(
  sample_embedding float[8]
);

-- vectors can be provided as JSON or in a compact binary format
insert into vec_examples(rowid, sample_embedding)
  values
    (1, '[-0.200, 0.250, 0.341, -0.211, 0.645, 0.935, -0.316, -0.924]'),
    (2, '[0.443, -0.501, 0.355, -0.771, 0.707, -0.708, -0.185, 0.362]'),
    (3, '[0.716, -0.927, 0.134, 0.052, -0.669, 0.793, -0.634, -0.162]'),
    (4, '[-0.710, 0.330, 0.656, 0.041, -0.990, 0.726, 0.385, -0.958]');


-- KNN style query
select
  rowid,
  distance
from vec_examples
where sample_embedding match '[0.890, 0.544, 0.825, 0.961, 0.358, 0.0196, 0.521, 0.175]'
order by distance
limit 2;
/*
┌───────┬──────────────────┐
│ rowid │     distance     │
├───────┼──────────────────┤
│ 2     │ 2.38687372207642 │
│ 1     │ 2.38978505134583 │
└───────┴──────────────────┘
*/
```

## GitHub Actions workflows (this fork)

> [!NOTE]
> Every workflow in `.github/workflows/` is **manual-trigger only**
> (`workflow_dispatch`). Nothing runs automatically on push, on a tag, or when a
> release is published — start a run from the
> [Actions tab](https://github.com/peerf-eco/sqlite-vec/actions).

This fork exists to publish
[`sqlite-vec-win-arm64`](https://pypi.org/project/sqlite-vec-win-arm64/), a
`win_arm64` wheel that upstream `sqlite-vec` does not ship. Upstream publishes
only `win_amd64` and no sdist, so `pip install sqlite-vec` fails outright on
Windows on ARM. Install ours with `pip install sqlite-vec-win-arm64`, then
`import sqlite_vec` as usual.

| Workflow | Use it when | Expected result |
| --- | --- | --- |
| [`sqlite-vec-win-arm64`](#sqlite-vec-win-arm64) | You changed C code or the build and want proof it still compiles and works on Windows ARM64 | One green run, artifact `sqlite-vec-win-arm64-wheel`. Nothing is published. |
| [`publish`](#publish) | You are cutting a release | Builds the wheel, then attaches it to a GitHub Release and/or uploads it to PyPI |
| [`Test`](#test) | You want upstream's full cross-platform build + test matrix before a release | 12 jobs; extensions for Linux, macOS, Windows, Android, iOS, WASM, plus `make test-loadable` |
| [`Release`](#release) | Only to run upstream's full multi-ecosystem release | **Fails as configured** — see below |
| [`Deploy Site`](#deploy-site) | You changed `site/`, `VERSION` or `reference.yaml` | **Fails as configured** until GitHub Pages is enabled |
| [`Fuzz`](#fuzz) | You want to fuzz the C code | `fuzz-linux` is the only job whose result is meaningful |

### sqlite-vec-win-arm64

Native build of the Windows ARM64 wheel, no publishing.

- **Runner:** GitHub-hosted `windows-11-arm` (free on this public repo), MSVC
  ARM64 toolchain, native ARM64 CPython.
- **Inputs:** `ref` (branch/tag/SHA, default the dispatch ref), `dist_name`,
  `cache_ttl_minutes`.
- **Pipeline:** fetch SQLite amalgamation → generate `sqlite-vec.h` → compile
  `vec0.dll` → package a `py3-none-win_arm64` wheel → `twine check` → functional
  smoke test (float32 KNN + int8 hamming) → upload artifact → purge stale caches.
- **SIMD:** built without `SQLITE_VEC_ENABLE_NEON`, because MSVC ARM64 ships
  `arm64_neon.h` rather than the `arm_neon.h` the NEON kernels include. MSVC
  auto-vectorizes the portable kernels at `/O2`.
- **Safety net:** `scripts/build-win-arm64-wheel.py` parses the PE header and
  refuses to package anything that is not an ARM64 image, so an accidental x64
  build can never be published.

### publish

The release path. Builds once, then fans out.

- **Inputs:** `ref`, `tag` (defaults to `v$(cat VERSION)`), `dist_name`,
  `create_release`, `publish_pypi`, `pypi_repository_url` (leave empty for real
  PyPI; set it for TestPyPI), `cache_ttl_minutes`.
- **`create_release: true`** creates the GitHub Release if the tag has none, or
  replaces the asset on an existing one. Releases are marked pre-release when
  `VERSION` contains `alpha`, `beta` or `rc`.
- **`publish_pypi: true`** uploads via **trusted publishing (OIDC)** — the
  repository holds no PyPI credentials at all. The publisher must already be
  registered on PyPI for `peerf-eco/sqlite-vec` / `publish.yml` with an **empty
  environment field**.
- **`skip-existing` is on**, so re-running a version that is already on PyPI is a
  no-op rather than a failure. This matters: PyPI filenames are immutable per
  `(project, version)`, so a rebuild of an existing version can never be
  uploaded. To ship changed bytes, bump `VERSION` first.
- Builds are not bit-reproducible across commits — `sqlite-vec.c:10626` embeds a
  `Date:`/`Commit:` provenance string, and MSVC stamps a `TimeDateStamp` into the
  PE header. Same commit differs by 4 bytes; different commits differ in the
  embedded SHA too.

### Test

Upstream's cross-platform matrix, unchanged apart from the trigger.

- **Was:** `push` to `main`. **Now:** manual.
- **Result:** 12 jobs. Linux x64/arm64, macOS x64/arm64, Windows x64,
  Android (4 ABIs), iOS (3 slices), WASM, Pyodide and a cosmopolitan CLI build;
  `make test-loadable` runs where a host executable exists. Extensions are
  uploaded as artifacts.
- This is the broad safety net, but it does **not** cover Windows ARM64 — use
  `sqlite-vec-win-arm64` for that.

### Release

Upstream's full release: amalgamation, sqlite-dist, npm, RubyGems, PyPI and
crates.io.

- **Was:** `release: published`. **Now:** manual.
- **Will fail here.** It needs `PYPI_API_TOKEN`, `GEM_HOST_API_KEY`,
  `CARGO_REGISTRY_TOKEN` and `NCRUCES_BINDINGS_REPO_PAT`, none of which exist in
  this repository, and it targets upstream's own registries. Use
  [`publish`](#publish) for this fork's releases.

### Deploy Site

Builds the VitePress documentation and publishes it to GitHub Pages.

- **Was:** `push` to `main` filtered on `site/**`, `.github/**`, `VERSION`,
  `reference.yaml`. **Now:** manual.
- **Will fail here** until Pages is switched on: repository **Settings → Pages →
  Source → GitHub Actions**. It also targets the `github-pages` environment,
  which does not exist yet and will be created on first run.

### Fuzz

libFuzzer targets for the C code.

- **Was:** `push` to `main` plus a nightly `0 2 * * *` cron. **Now:** manual.
- **Input:** `duration`, seconds per target (default `60`).
- Only `fuzz-linux` is reliable. `fuzz-macos` and `fuzz-windows` are marked
  `continue-on-error` upstream because Homebrew libFuzzer pulls in typed-allocation
  ABI symbols macOS 14's `libc++` lacks, and ASan support on Windows is shaky.
  Crashes are uploaded as artifacts.

### Caching

Only the SQLite amalgamation is cached (~2.7 MB), keyed on `scripts/vendor.sh`.
Because GitHub gives no control over cache expiry — entries linger 7 days after
last access — `scripts/purge-actions-cache.py` deletes any cache entry not
accessed within `cache_ttl_minutes` (default 60) at the end of each successful
run. Expiry is therefore enforced at purge time, not autonomously by GitHub.

## Sponsors

Development of `sqlite-vec` is supported by multiple generous sponsors! Mozilla
is the main sponsor through the new Builders project.
<p align="center">
  <a href="https://hacks.mozilla.org/2024/06/sponsoring-sqlite-vec-to-enable-more-powerful-local-ai-applications/">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./.github/logos/mozilla.dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="./.github/logos/mozilla.svg">
    <img alt="Mozilla Builders logo" width=400>
  </picture>
  </a>
</p>

`sqlite-vec` is also sponsored by the following companies:

<a href="https://fly.io/">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./.github/logos/flyio.dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./.github/logos/flyio.svg">
  <img alt="Fly.io logo" src="./.github/logos/flyio.svg" width="48%">
</picture>
</a>

<a href="https://tur.so/sqlite-vec">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./.github/logos/turso.svg">
  <source media="(prefers-color-scheme: light)" srcset="./.github/logos/turso.svg">
  <img alt="Turso logo" src="./.github/logos/turso.svg" width="48%">
</picture>
</a>

<a href="https://sqlitecloud.io/">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./.github/logos/sqlitecloud.dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./.github/logos/sqlitecloud.svg">
  <img alt="SQLite Cloud logo" src="./.github/logos/flyio.svg" width="48%">
</picture>
</a>

<a href="https://shinkai.com">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./.github/logos/shinkai.dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./.github/logos/shinkai.svg">

  <img alt="Shinkai logo" src="./.github/logos/shinkai.svg" width="48%">
</picture>
</a>

As well as multiple individual supporters on
[Github sponsors](https://github.com/sponsors/asg017/)!

If your company interested in sponsoring `sqlite-vec` development, send me an
email to get more info: https://alexgarcia.xyz

## See Also

- [**`sqlite-ecosystem`**](https://github.com/asg017/sqlite-ecosystem), Maybe
  more 3rd party SQLite extensions I've developed
- [**`sqlite-rembed`**](https://github.com/asg017/sqlite-rembed), Generate text
  embeddings from remote APIs like OpenAI/Nomic/Ollama, meant for testing and
  SQL scripts
- [**`sqlite-lembed`**](https://github.com/asg017/sqlite-lembed), Generate text
  embeddings locally from embedding models in the `.gguf` format
