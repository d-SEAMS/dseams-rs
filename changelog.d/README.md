# Changelog fragments

One file per user-visible change, named `<number>.<type>.md` for a GitHub
issue or pull request, or `+<slug>.<type>.md` when there is none. `<type>`
is one of `added`, `changed`, `deprecated`, `removed`, `fixed`, `security`.
Write one or two sentences in the present tense about what a user of the
crates sees. `towncrier build --version X.Y.Z` folds them into
`CHANGELOG.md` at release.
