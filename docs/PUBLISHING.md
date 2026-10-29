# Publish the repository and demo

## Published project

- Public repository: https://github.com/gytung/ProseLedger
- Interactive round scores: https://gytung.github.io/ProseLedger/#rounds

The link opens the full round-score dashboard: round 0 plus rounds 1–3, batch means, all six case curves, and candidate-versus-retained decisions. All saved results load together. New model generation runs through the local application, not GitHub Pages.

## Repository

1. Extract the source archive locally.
2. Create a public GitHub repository, for example `proseledger`.
3. Upload or commit the **contents** of the extracted project folder. The README, `app.py`, `proseledger/` and `docs/` should be at the repository root; do not upload only the ZIP.
4. Ensure hidden configuration files such as `.gitignore` and `.github/workflows/ci.yml` are included when using Git.
5. Open the public repository link in a signed-out browser to check access.

Do not upload local run folders, account files, source uploads, environments or the old desktop runtime bundle. The release keeps the license and attribution notices required for the reused code and source materials.

## Demo link with GitHub Pages

The `docs` folder contains a self-contained static demonstration of the six recorded cases. It requires no API key or server.

In the repository, open **Settings → Pages**. Under **Build and deployment**, choose **Deploy from a branch**, select the branch containing the uploaded project, select **/docs**, and save. Use the published URL shown by GitHub after deployment completes. These steps follow [GitHub's publishing-source documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

This site displays saved outputs, not live proposal generation. The Python application remains a separate local program; do not describe GitHub Pages as a hosted inference service.

## Submission links

After publishing, place the actual repository URL and the actual Pages URL on the first slide. Also include the group number and the member/student-ID information requested by the course. The archive does not contain invented public URLs or unprovided student IDs.

Open both links without relying on your signed-in session. Check that the six-case table loads, Case 02's memory trace opens, and a manuscript or summary can be downloaded. The source ZIP by itself is not a public GitHub or demo link.
