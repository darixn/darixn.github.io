#!/usr/bin/env python3
"""
publish.py — Ulysses → Blog Publisher
======================================
Converts Markdown drafts (with YAML front matter) into fully styled
blog posts and updates the blog listing pages automatically.

Usage:
    python3 publish.py                  # Publish all drafts in blog/drafts/
    python3 publish.py my-post.md       # Publish a specific draft
    python3 publish.py --list           # List unpublished drafts
    python3 publish.py --undo my-slug   # Remove a published post

Workflow:
    1. Write in Ulysses using standard Markdown
    2. Export as .md to blog/drafts/
    3. Add YAML front matter at the top (see below)
    4. Run: python3 publish.py
    5. git add -A && git commit -m "new post" && git push

Front matter format:
    ---
    title: Your Post Title Here
    date: 2026-02-15
    tags: jamf, automation, compliance
    reading_time: 6 min read
    excerpt: A brief summary of the post for listing cards.
    ---

    Your Markdown content starts here...
"""

import os
import sys
import re
import math
import glob
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
DRAFTS_DIR = SCRIPT_DIR / "blog" / "drafts"
BLOG_DIR = SCRIPT_DIR / "blog"
BLOG_HTML = SCRIPT_DIR / "blog.html"
INDEX_HTML = SCRIPT_DIR / "index.html"
MAX_HOME_POSTS = 3  # Max blog cards shown on the home page


# ── Front Matter Parser ────────────────────────────────────────────
def parse_front_matter(text):
    """Parse YAML front matter from Markdown text. Returns (metadata_dict, body_markdown)."""
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, text, re.DOTALL)
    if not match:
        print("  ⚠  No YAML front matter found. Expected --- block at top of file.")
        print("     Example:")
        print("     ---")
        print("     title: My Post Title")
        print("     date: 2026-02-15")
        print("     tags: tag1, tag2")
        print("     reading_time: 5 min read")
        print("     excerpt: A short summary.")
        print("     ---")
        return None, text

    yaml_block = match.group(1)
    body = match.group(2)

    meta = {}
    for line in yaml_block.strip().split('\n'):
        if ':' in line:
            key, _, value = line.partition(':')
            meta[key.strip()] = value.strip()

    return meta, body


def estimate_reading_time(text):
    """Estimate reading time based on word count (~200 wpm)."""
    words = len(text.split())
    minutes = max(1, math.ceil(words / 200))
    return f"{minutes} min read"


def slugify(title):
    """Convert a title to a URL-safe slug."""
    slug = title.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


# ── HTML Generators ────────────────────────────────────────────────
def generate_post_html(meta, markdown_body):
    """Generate the full blog post HTML file from metadata and Markdown body."""
    title = meta.get('title', 'Untitled Post')
    date = meta.get('date', '2026-01-01')
    reading_time = meta.get('reading_time', estimate_reading_time(markdown_body))
    tags_raw = meta.get('tags', '')
    slug = slugify(title)

    tags_list = [t.strip() for t in tags_raw.split(',') if t.strip()]
    tags_html = '\n                    '.join(
        f'<span class="skill-tag">{tag}</span>' for tag in tags_list
    )

    # Escape </script> in markdown body to prevent premature closing
    safe_body = markdown_body.replace('</script>', '<\\/script>')

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | dariangarcia.com</title>
    <link rel="stylesheet" href="../assets/css/style.css">
</head>
<body>
    <!-- Header -->
    <header class="header">
        <nav class="nav">
            <a href="../index.html" class="logo">dariangarcia.com</a>
            <button class="mobile-menu-toggle" onclick="toggleMobileMenu()">☰</button>
            <ul class="nav-links">
                <li><a href="../index.html">Home</a></li>
                <li><a href="../about.html">About</a></li>
                <li><a href="../blog.html">D.Log</a></li>
            </ul>
        </nav>
    </header>

    <!-- Blog Post -->
    <section class="blog-post-page">
        <div class="blog-post-terminal terminal-window">
            <div class="terminal-header">
                <div class="terminal-controls">
                    <div class="terminal-button close"></div>
                    <div class="terminal-button minimize"></div>
                    <div class="terminal-button maximize"></div>
                </div>
                <div class="terminal-title">{slug}.md</div>
            </div>
            <div class="blog-post-content">
                <a href="../blog.html" class="blog-post-back">Back to D.Log</a>

                <div class="blog-post-meta">
                    <span class="blog-post-date">{date}</span>
                    <span class="blog-post-reading-time">{reading_time}</span>
                </div>

                <h1>{title}</h1>

                <div class="blog-post-tags">
                    {tags_html}
                </div>

                <div id="post-body" class="blog-post-body"></div>
                <script id="post-markdown" type="text/markdown">
{safe_body}
                </script>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <p>© 2026 Darian Garcia — IT Systems Engineer. All rights reserved.</p>
        </div>
    </footer>

    <script src="../assets/js/main.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
        (function() {{
            const md = document.getElementById('post-markdown');
            const body = document.getElementById('post-body');
            if (md && body) {{
                const raw = md.textContent.trim();
                marked.setOptions({{ gfm: true, breaks: false }});
                body.innerHTML = marked.parse(raw);
            }}
        }})();
    </script>
</body>
</html>
'''


def generate_blog_card(meta, for_index=False):
    """Generate a blog card HTML snippet for listing pages."""
    title = meta.get('title', 'Untitled Post')
    date = meta.get('date', '2026-01-01')
    reading_time = meta.get('reading_time', '5 min read')
    excerpt = meta.get('excerpt', '')
    tags_raw = meta.get('tags', '')
    slug = slugify(title)

    tags_list = [t.strip() for t in tags_raw.split(',') if t.strip()]
    tags_html = '\n                            '.join(
        f'<span class="skill-tag">{tag}</span>' for tag in tags_list
    )

    # Adjust href based on whether this is for index.html or blog.html
    href = f"blog/{slug}.html" if for_index else f"blog/{slug}.html"
    if not for_index:
        href = f"blog/{slug}.html"

    return f'''                <div class="blog-card animate-on-scroll">
                    <div class="blog-card-header">
                        <div class="blog-card-meta">
                            <span class="blog-card-date">{date}</span>
                            <span class="blog-card-reading-time">{reading_time}</span>
                        </div>
                        <h3><a href="{href}">{title}</a></h3>
                    </div>
                    <div class="blog-card-body">
                        <p class="blog-card-excerpt">{excerpt}</p>
                    </div>
                    <div class="blog-card-footer">
                        <div class="blog-card-tags">
                            {tags_html}
                        </div>
                        <a href="{href}" class="blog-card-link">Read More →</a>
                    </div>
                </div>'''


# ── Page Updaters ──────────────────────────────────────────────────

def find_card_bounds(html, start_pos):
    """Find the end position of a blog-card div starting at start_pos.
    Counts nested <div> tags to find the matching closing </div>."""
    depth = 0
    i = start_pos
    while i < len(html):
        if html[i:i+4] == '<div':
            depth += 1
            i += 4
        elif html[i:i+6] == '</div>':
            depth -= 1
            if depth == 0:
                return i + 6  # position after the closing </div>
            i += 6
        else:
            i += 1
    return -1


def remove_card_block(html, card_start_pos):
    """Remove a full blog-card block including surrounding whitespace."""
    card_end = find_card_bounds(html, card_start_pos)
    if card_end == -1:
        return html

    # Extend to consume leading whitespace/newline
    block_start = card_start_pos
    while block_start > 0 and html[block_start - 1] in ' \t':
        block_start -= 1
    if block_start > 0 and html[block_start - 1] == '\n':
        block_start -= 1

    # Extend to consume trailing newline
    block_end = card_end
    if block_end < len(html) and html[block_end] == '\n':
        block_end += 1

    return html[:block_start] + html[block_end:]


def remove_coming_soon(html):
    """Remove the Coming Soon placeholder card from HTML."""
    marker = '<!-- Coming Soon'
    idx = html.find(marker)
    if idx == -1:
        return html

    # The comment sits BEFORE the <div class="blog-card"> on the next line
    # Find the next blog-card div after the comment
    card_start_search = html[idx:]
    div_offset = card_start_search.find('<div class="blog-card')
    if div_offset == -1:
        return html

    card_start = idx + div_offset
    card_end = find_card_bounds(html, card_start)
    if card_end == -1:
        return html

    # Block includes the comment line + the card div + surrounding whitespace
    block_start = idx
    while block_start > 0 and html[block_start - 1] in ' \t':
        block_start -= 1
    if block_start > 0 and html[block_start - 1] == '\n':
        block_start -= 1

    block_end = card_end
    if block_end < len(html) and html[block_end] == '\n':
        block_end += 1

    return html[:block_start] + html[block_end:]


def insert_card_into_blog_html(card_html):
    """Insert a blog card into blog.html after the template comment."""
    content = BLOG_HTML.read_text()

    # Remove coming soon card if present
    if 'Coming Soon' in content:
        content = remove_coming_soon(content)

    # Find insertion point: after the closing --> of the template comment
    marker = '                -->\n'
    idx = content.find(marker)
    if idx == -1:
        print("  ⚠  Could not find insertion marker in blog.html")
        return False

    insert_at = idx + len(marker)
    content = content[:insert_at] + '\n' + card_html + '\n' + content[insert_at:]

    BLOG_HTML.write_text(content)
    return True


def insert_card_into_index_html(card_html):
    """Insert a blog card into index.html, keeping max MAX_HOME_POSTS cards."""
    content = INDEX_HTML.read_text()

    # Remove coming soon card if present
    if 'Coming Soon' in content:
        content = remove_coming_soon(content)

    # Find insertion point: after the closing --> of the template comment
    marker = '                -->\n'
    idx = content.find(marker)
    if idx == -1:
        print("  ⚠  Could not find insertion marker in index.html")
        return False

    insert_at = idx + len(marker)
    content = content[:insert_at] + '\n' + card_html + '\n' + content[insert_at:]

    # Enforce max cards on home page
    card_positions = [m.start() for m in re.finditer(r'<div class="blog-card animate-on-scroll">', content)]
    while len(card_positions) > MAX_HOME_POSTS:
        # Remove the last (oldest) card
        content = remove_card_block(content, card_positions[-1])
        card_positions = [m.start() for m in re.finditer(r'<div class="blog-card animate-on-scroll">', content)]

    INDEX_HTML.write_text(content)
    return True


COMING_SOON_CARD = '''
                <!-- Coming Soon — remove this card once you publish your first post -->
                <div class="blog-card animate-on-scroll" style="grid-column: 1 / -1; max-width: 600px; margin: 0 auto;">
                    <div class="blog-card-header" style="text-align: center;">
                        <h3 style="color: var(--terminal-accent); margin-top: 0.5rem;">Coming Soon</h3>
                    </div>
                    <div class="blog-card-body" style="text-align: center;">
                        <p class="blog-card-excerpt">First post is on the way — check back shortly.</p>
                    </div>
                </div>'''


def restore_coming_soon_if_empty(html):
    """If no blog-card elements remain, re-insert the Coming Soon placeholder."""
    if 'Coming Soon' in html:
        return html  # already has it
    card_positions = [m.start() for m in re.finditer(r'<div class="blog-card animate-on-scroll">', html)]
    if len(card_positions) == 0:
        # Insert after the template comment -->
        marker = '                -->\n'
        idx = html.find(marker)
        if idx != -1:
            insert_at = idx + len(marker)
            html = html[:insert_at] + COMING_SOON_CARD + '\n' + html[insert_at:]
    return html


# ── Undo (remove a published post) ────────────────────────────────
def undo_post(slug):
    """Remove a published post by slug."""
    post_file = BLOG_DIR / f"{slug}.html"

    if post_file.exists():
        post_file.unlink()
        print(f"  ✓  Deleted blog/{slug}.html")
    else:
        print(f"  ⚠  blog/{slug}.html not found")

    # Remove card from blog.html and index.html
    for html_path in [BLOG_HTML, INDEX_HTML]:
        content = html_path.read_text()
        # Find the blog-card that contains a link to this slug
        slug_ref = f"{slug}.html"
        card_positions = [m.start() for m in re.finditer(r'<div class="blog-card animate-on-scroll">', content)]

        removed = False
        for pos in card_positions:
            card_end = find_card_bounds(content, pos)
            if card_end == -1:
                continue
            card_text = content[pos:card_end]
            if slug_ref in card_text:
                content = remove_card_block(content, pos)
                removed = True
                break

        if removed:
            content = restore_coming_soon_if_empty(content)
            html_path.write_text(content)
            print(f"  ✓  Removed card from {html_path.name}")
        else:
            print(f"  ⚠  No card found for {slug} in {html_path.name}")


# ── Main ───────────────────────────────────────────────────────────
def publish_draft(draft_path):
    """Publish a single Markdown draft."""
    draft = Path(draft_path)
    if not draft.exists():
        print(f"  ✗  File not found: {draft}")
        return False

    print(f"\n  📄 Processing: {draft.name}")

    text = draft.read_text()
    meta, body = parse_front_matter(text)

    if meta is None:
        return False

    # Validate required fields
    required = ['title', 'date']
    missing = [f for f in required if f not in meta]
    if missing:
        print(f"  ✗  Missing required front matter: {', '.join(missing)}")
        return False

    # Auto-fill optional fields
    if 'reading_time' not in meta:
        meta['reading_time'] = estimate_reading_time(body)
        print(f"  ℹ  Auto-calculated reading time: {meta['reading_time']}")

    if 'excerpt' not in meta:
        # Use first paragraph as excerpt
        first_para = body.strip().split('\n\n')[0]
        # Strip markdown formatting
        first_para = re.sub(r'[#*_`\[\]()]', '', first_para)
        meta['excerpt'] = first_para[:200].strip()
        if len(first_para) > 200:
            meta['excerpt'] += '...'
        print(f"  ℹ  Auto-generated excerpt from first paragraph")

    slug = slugify(meta['title'])
    post_file = BLOG_DIR / f"{slug}.html"

    # Check if post already exists
    if post_file.exists():
        print(f"  ⚠  Post already exists: blog/{slug}.html")
        response = input("     Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("  ⏭  Skipped")
            return False

    # Generate and write the post HTML
    post_html = generate_post_html(meta, body)
    post_file.write_text(post_html)
    print(f"  ✓  Created blog/{slug}.html")

    # Generate blog card and insert into listing pages
    blog_card = generate_blog_card(meta, for_index=False)
    index_card = generate_blog_card(meta, for_index=True)

    if insert_card_into_blog_html(blog_card):
        print(f"  ✓  Added card to blog.html")

    if insert_card_into_index_html(index_card):
        print(f"  ✓  Added card to index.html")

    # Move draft to a "published" subfolder
    published_dir = DRAFTS_DIR / "published"
    published_dir.mkdir(exist_ok=True)
    draft.rename(published_dir / draft.name)
    print(f"  ✓  Moved draft to blog/drafts/published/{draft.name}")

    print(f"\n  🚀 Published! Run 'git add -A && git commit -m \"publish: {meta['title']}\" && git push' to go live.")
    return True


def list_drafts():
    """List all unpublished drafts."""
    drafts = sorted(DRAFTS_DIR.glob('*.md'))
    if not drafts:
        print("\n  📭 No drafts found in blog/drafts/")
        print("     Export a .md file from Ulysses to blog/drafts/ to get started.")
        return

    print(f"\n  📝 Unpublished drafts ({len(drafts)}):\n")
    for draft in drafts:
        text = draft.read_text()
        meta, _ = parse_front_matter(text)
        title = meta.get('title', '(no title)') if meta else '(no front matter)'
        date = meta.get('date', '') if meta else ''
        print(f"     • {draft.name}")
        print(f"       Title: {title}  Date: {date}")
        print()


def main():
    print("  ╔══════════════════════════════════════╗")
    print("  ║ dariangarcia.com — Blog Publisher  ║")
    print("  ╚══════════════════════════════════════╝")

    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == '--list':
            list_drafts()
            return

        if arg == '--undo':
            if len(sys.argv) < 3:
                print("\n  Usage: python3 publish.py --undo <slug>")
                print("  Example: python3 publish.py --undo automating-patch-compliance")
                return
            undo_post(sys.argv[2])
            return

        # Specific file
        draft_path = Path(arg)
        if not draft_path.is_absolute():
            draft_path = DRAFTS_DIR / arg
        publish_draft(draft_path)
        return

    # No args — publish all drafts
    drafts = sorted(DRAFTS_DIR.glob('*.md'))
    if not drafts:
        print("\n  📭 No drafts found in blog/drafts/")
        print("     Export a .md file from Ulysses to blog/drafts/ to get started.\n")
        print("  Front matter template:\n")
        print("     ---")
        print("     title: Your Post Title")
        print("     date: 2026-02-15")
        print("     tags: tag1, tag2, tag3")
        print("     reading_time: 5 min read")
        print("     excerpt: A brief summary for listing cards.")
        print("     ---")
        print()
        return

    print(f"\n  Found {len(drafts)} draft(s):\n")
    for d in drafts:
        print(f"     • {d.name}")

    print()
    confirm = input("  Publish all? (Y/n): ").strip().lower()
    if confirm == 'n':
        print("  Cancelled.")
        return

    published = 0
    for draft in drafts:
        if publish_draft(draft):
            published += 1

    print(f"\n  ✅ Published {published}/{len(drafts)} post(s).\n")


if __name__ == '__main__':
    main()
