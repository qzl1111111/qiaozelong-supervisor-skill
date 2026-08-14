# Copyright and publication policy

Apply this policy to every tutorial ingestion, knowledge package, expert knowledge base, Git operation, cloud transfer, attachment, and public release.

## Default state: local only

- Treat every tutorial and every intermediate extraction as copyrighted and non-public unless the user provides a clear license or permission.
- Never upload, attach, push, publish, sync, or transmit original tutorials or intermediate extractions without the user's explicit approval for the exact files and destination.
- Do not infer approval from a request to read, summarize, index, classify, convert, or build a knowledge base.
- Keep raw tutorials, OCR/full text, rendered pages, slide images, speaker notes, workbook copies, extracted figures, audio/video, archives, and source code copies outside the public repository.
- Treat generated summaries as local-only until a publication-safety review passes and the user explicitly approves release.

## Private and public layers

Maintain two separate layers:

1. **Private provenance layer**: local source paths, filenames, titles, creators/authors, licenses, hashes, page/slide/cell/line locators, and extraction artifacts. This layer supports verification and is never published automatically.
2. **Public derived layer**: independently written knowledge units, concise summaries, formulas or facts expressed only as needed, source IDs without local paths, and no original binaries or reversible full-text extraction.

Do not remove author or creator information from the private provenance layer. Omit unnecessary personal names from the public derived layer, but do not present omission as eliminating copyright. If attribution is legally, ethically, or scientifically required, block publication until the user decides how to cite or obtain permission.

## Extraction must remain complete

- Perform author/creator metadata minimization only when producing a public derived export.
- Do not redact names, headers, references, or surrounding context before knowledge extraction when they affect interpretation, chronology, provenance, named methods, software versions, or scientific claims.
- Do not alter original files.
- Do not reduce knowledge coverage merely because a source is copyrighted; instead keep the complete analysis local and publish only a safely transformed subset.

## Content allowed in a public-derived candidate

- original synthesis of concepts and procedures;
- short evidence excerpts only when necessary for verification;
- standard facts, formulas, terminology, and methods expressed concisely;
- transformed examples that do not reproduce a substantial original exercise, answer set, table, figure, slide, or tutorial sequence;
- source IDs and internal unit IDs that do not expose local paths.

## Content blocked from public release

- original PDF, PPT/PPTX, DOC/DOCX, XLS/XLSX, notebooks, scripts, images, audio, video, or archives copied from tutorials;
- OCR output, full transcripts, full speaker notes, full workbook data, page images, slide images, or reconstructed documents;
- substantial or repeated excerpts, even when author names are removed;
- detailed summaries that substitute for the original tutorial or preserve its distinctive sequence, exercises, examples, tables, or expressive structure;
- local paths, account names, private metadata, access tokens, or confidential material;
- any candidate not explicitly approved by the user for the named destination.

## Required release gate

Before any upload:

1. Identify the exact candidate files and destination.
2. Run `check_publication_safety.py`.
3. Review flagged names, excerpts, source paths, binaries, extraction artifacts, and potentially substitutive summaries.
4. Confirm that private provenance remains local.
5. Ask the user for explicit approval to upload the exact reviewed files.
6. Upload only those approved files; approval does not extend to later batches.

The checker detects structural risks but cannot determine legal fair use, substantial similarity, licensing terms, or whether a summary substitutes for a source. When uncertain, keep the material local and obtain qualified legal advice.
