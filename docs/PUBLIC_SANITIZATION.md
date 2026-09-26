# Public sanitization boundary

This repository includes a narrow, fail-closed check for material proposed for
public release. Its threat model is accidental publication of common personal
identifiers, local paths, credentials, private artifacts, opaque files, and
non-synthetic fixture data. It is a publication guard, not an operational
career-intelligence capability or a production security system.

## What is scanned

From the repository root, the scanner asks Git for tracked files and untracked,
non-ignored files. Consequently, a force-added file is scanned even if an ignore
rule also matches it. `.git` internals and unrelated filesystem locations are
not scanned. The scanner source and tests receive ordinary content inspection;
they have no content exemption. The optional local denylist is loaded separately
but is not itself published or printed.

The conservative maximum file size is 1,048,576 bytes. Symlinks, special files,
escaping paths, unreadable files, invalid UTF-8, NUL-containing input, oversized
files, and explicitly opaque/archive/binary types fail closed. Candidate
enumeration and other internal scanner failures also fail closed.

## Synthetic provenance contract

`config/*.example.json`, `data/*.json`, and
`data/demo_readiness_cases/*.json` are designated synthetic fixtures.
Each must be parseable JSON with a top-level object, an integer
`schema_version`, and `synthetic` set to the JSON boolean `true`. Unknown domain
fields are allowed. HTTP(S) URLs in these fixtures must use `example.com`,
`example.org`, `example.net`, their subdomains, or a host ending in `.invalid`.
Reserved domains constrain fixture URLs; they do not prove surrounding data is
synthetic.

The currently understood `profile_id` and company `id` fields must use an
accepted fictional prefix such as `synthetic_` or `example_`. This is not a
generic rule for every future field ending in `_id`.

## Optional private context

A maintainer may create the ignored file
`config/public-sanitizer.local.json` without committing it. Its minimal format is:

```json
{
  "literals": ["maintainer-specific literal"],
  "regexes": ["maintainer-specific regular expression"]
}
```

Both keys are optional string arrays. Values and expressions are never emitted.
Malformed JSON, schema, or regular expressions fail the scan safely.
Organization-specific detection depends on this optional private maintainer
context.

## Output and invocation

Run from the repository root without installing dependencies:

```sh
PYTHONPATH=src python3 -m ai_job_radar.public_sanitizer
```

Failure records contain only a repository-relative path, category, and `FAIL`.
They never contain matched text, excerpts, absolute paths, exception details,
tracebacks, or secret-derived fingerprints. A clean run emits one minimal
repository-level `PASS` record. Exit status is zero only when every applicable
check passes; findings and scanner failures return nonzero.

## Limitations

Pattern and entropy checks are deliberately conservative. False positives and
false negatives remain possible. This tool does not provide complete secret
detection, guaranteed anonymization, a confidentiality guarantee, or proof of
production security. It inspects the current publication candidate, not Git
history; it does not claim that history is sanitized. Human review and
appropriate repository/history handling remain necessary. Decision Model V2
remains `DRAFT_NOT_ACTIVE`, and no collection, analysis, scoring, evaluation,
agent, or other operational career-intelligence runtime is introduced here.
