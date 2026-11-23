# Art Intelligence website

## Editing the copy
All text on the site is in **content.toml**. Open it on GitHub, click the pencil icon, change the text between the quotation marks, and click **Commit changes**. The site rebuilds and goes live in about a minute.

- `**words**` sets those words in the heavier weight.
- Lines beginning with `#` are notes and don't appear on the site.

## Substack posts
These update automatically. Every morning at about 7am UK time, the site checks your Substack feed and adds new posts to the home page (latest four) and the Writing page (latest twelve). To leave a post off the site, add a phrase from its title to the `exclude` list under `[writing]` in content.toml. To update straight away after publishing, go to **Actions › Build and deploy › Run workflow** on GitHub.

## One-time setup
1. Create a free GitHub account and a new repository, for example `artintelligence-site`.
2. Upload every file and folder in this package, including the hidden `.github` folder.
3. In the repository go to **Settings › Pages** and set **Source** to **GitHub Actions**.
4. Under **Settings › Pages › Custom domain**, enter `artintelligence.io`.
5. At your domain registrar, point the domain at GitHub Pages: four `A` records for `@` to 185.199.108.153, 185.199.109.153, 185.199.110.153 and 185.199.111.153, and a `CNAME` record for `www` to `<your-github-username>.github.io`. Then tick **Enforce HTTPS** in Settings › Pages.
6. Cancel the Squarespace website plan only after the new site is live on your domain. If your domain was bought through Squarespace, transfer it or edit its DNS there first.

## What's where
- `content.toml`: all copy
- `assets/site.css`: design (colours, type, layout)
- `assets/`: logo, portrait
- `fonts/`: Valley Sans (licensed: check your licence covers web use)
- `build.py`: builds the pages; you don't need to touch it
- `posts-cache.json`: the last Substack posts fetched, used if Substack can't be reached
