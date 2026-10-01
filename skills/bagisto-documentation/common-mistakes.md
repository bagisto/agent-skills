# Common mistakes

Work through this list during the independent audit that finishes every change.

- **Mixing the two audiences on one page** — the failure this skill exists to
  prevent. Click paths in developer docs, class names in the user guide.
- **Documenting the intended design instead of the shipped behaviour.** When a
  page and the code disagree, the code is right.
- **A stub page left behind after a move.** A page whose whole body is "this
  moved" stays in the sidebar and ranks in search. Redirect it, then delete it.
- **A rename shipped without a redirect.** Fixing a typo in a filename feels
  like tidying rather than a URL change, which is why it is the one that gets
  missed.
- **Aligned `=>` columns and inline comments in PHP samples.** They look tidy in
  the editor and are exactly what Pint rejects; the project's own code never
  has them.
- **A procedure written as prose.** "Go to Configure, open General, enable X
  and save" reads fine to the author and is unusable to someone doing it with
  the admin open beside them.
- **Marketing language on a technical page, and a technical page's caution on
  a marketing one.** The AI overview may say "generative AI"; the page that
  documents `magic_ai()->generateContent()` says what the method returns.
- **A docs skill that describes yesterday's admin.** When a menu path, label or
  group changes in the code, the guide's paths change with it; grep the guide
  for the old label before calling the code change done.
