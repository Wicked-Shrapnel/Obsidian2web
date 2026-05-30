#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════╗
║         Obsidian -> WordPress Publisher v2.0          ║
║  Publishes, updates, or drafts WordPress posts        ║
║  from Obsidian notes with a single hotkey press.      ║
╚═══════════════════════════════════════════════════════╝

SETUP:
  1. Fill in your credentials in the CONFIG section below.
  2. Save this file somewhere permanent (e.g. C:\Scripts\).
  3. In Obsidian, install the Shell Commands plugin and bind:
       Publish hotkey:
         python "C:\Scripts\publish_to_wp.py" "{{file_path:absolute}}"
       Draft hotkey:
         python "C:\Scripts\publish_to_wp.py" "{{file_path:absolute}}" --draft

NOTE TEMPLATE (frontmatter fields):
  ---
  category: CategoryName
  excerpt: Short summary shown on post listing pages (optional)
  ---

  Your content here...

HOW IT WORKS:
  - Publish hotkey  -> creates a new live post, or updates existing.
  - Draft hotkey    -> creates a new draft, or reverts existing post to draft.
  - wp-id is written to frontmatter after first publish/draft so future
    runs update the correct post instead of creating a duplicate.
  - Categories are created automatically if they don't exist.
  - Date is handled by WordPress, same as writing in Gutenberg.
  - A Windows notification confirms every action.
  - UNC paths (\\server\share) are automatically converted to
    mapped drive letters so the script works from Obsidian hotkeys.
"""

import sys
import io
import os
import json
import re
import base64
import subprocess
import urllib.request
import urllib.error
import urllib.parse
import traceback

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ── CONFIG ─────────────────────────────────────────────────────────────────────
# Your WordPress site URL — https:// no trailing slash
WP_URL          = ""

# Your WordPress login username
WP_USERNAME     = ""

# Application Password — generate one at:
# WordPress Dashboard -> Users -> Profile -> Application Passwords
WP_APP_PASSWORD = ""
# ───────────────────────────────────────────────────────────────────────────────

def notify(title, message):
    """Show a Windows balloon notification in the taskbar."""
    try:
        script = (
            f'Add-Type -AssemblyName System.Windows.Forms;'
            f'$n = New-Object System.Windows.Forms.NotifyIcon;'
            f'$n.Icon = [System.Drawing.SystemIcons]::Information;'
            f'$n.Visible = $true;'
            f'$n.ShowBalloonTip(4000, "{title}", "{message}", '
            f'[System.Windows.Forms.ToolTipIcon]::None);'
            f'Start-Sleep -Seconds 5; $n.Dispose()'
        )
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-Command", script]
        )
    except Exception:
        pass  # Notifications are best-effort; never crash the script


def resolve_path(note_path):
    """
    Convert UNC paths (\\server\share\...) to mapped drive paths (Z:\...).
    Obsidian sometimes passes UNC paths even when the vault is on a mapped drive.
    """
    if note_path.startswith("\\\\"):
        result = subprocess.run(["net", "use"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            parts = line.split()
            drive = None
            unc_share = None
            for part in parts:
                if len(part) == 2 and part[1] == ':':
                    drive = part
                if part.startswith("\\\\"):
                    unc_share = part.rstrip("\\")
            if drive and unc_share and note_path.lower().startswith(unc_share.lower()):
                converted = drive + note_path[len(unc_share):]
                return converted
    return note_path


def parse_frontmatter(content):
    """
    Extract YAML frontmatter and body from a Markdown note.
    Returns (dict of frontmatter values, body string).
    """
    frontmatter = {}
    body = content

    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            fm_block = content[3:end].strip()
            body = content[end + 3:].strip()
            for line in fm_block.splitlines():
                if ":" in line:
                    key, _, val = line.partition(":")
                    frontmatter[key.strip().lower()] = (
                        val.strip().strip('"').strip("'")
                    )

    return frontmatter, body


def markdown_to_html(md):
    """
    Convert Markdown to HTML.
    Supports: headings, bold, italic, bold+italic, strikethrough,
    inline code, fenced code blocks, links, images, blockquotes,
    unordered lists, ordered lists, and horizontal rules.
    """
    lines = md.split("\n")
    html_lines = []
    in_ul = False
    in_ol = False
    in_code_block = False
    code_buffer = []

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            html_lines.append("</ul>")
            in_ul = False
        if in_ol:
            html_lines.append("</ol>")
            in_ol = False

    def inline(text):
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
        text = re.sub(r'\*\*(.+?)\*\*',     r'<strong>\1</strong>', text)
        text = re.sub(r'__(.+?)__',          r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*',          r'<em>\1</em>', text)
        text = re.sub(r'_(.+?)_',            r'<em>\1</em>', text)
        text = re.sub(r'`(.+?)`',            r'<code>\1</code>', text)
        text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',  r'<a href="\2">\1</a>', text)
        text = re.sub(r'~~(.+?)~~',          r'<del>\1</del>', text)
        return text

    for line in lines:
        if line.startswith("```"):
            if not in_code_block:
                close_lists()
                in_code_block = True
                code_buffer = []
            else:
                in_code_block = False
                code = "\n".join(code_buffer)
                html_lines.append(f'<pre><code>{code}</code></pre>')
            continue

        if in_code_block:
            code_buffer.append(line)
            continue

        if re.match(r'^(\*{3,}|-{3,}|_{3,})$', line.strip()):
            close_lists()
            html_lines.append("<hr>")
            continue

        heading = re.match(r'^(#{1,6})\s+(.*)', line)
        if heading:
            close_lists()
            level = len(heading.group(1))
            html_lines.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            continue

        if line.startswith("> "):
            close_lists()
            html_lines.append(f"<blockquote>{inline(line[2:])}</blockquote>")
            continue

        ul_match = re.match(r'^[-*+] (.*)', line)
        if ul_match:
            if in_ol:
                html_lines.append("</ol>")
                in_ol = False
            if not in_ul:
                html_lines.append("<ul>")
                in_ul = True
            html_lines.append(f"<li>{inline(ul_match.group(1))}</li>")
            continue

        ol_match = re.match(r'^\d+\. (.*)', line)
        if ol_match:
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            if not in_ol:
                html_lines.append("<ol>")
                in_ol = True
            html_lines.append(f"<li>{inline(ol_match.group(1))}</li>")
            continue

        if line.strip() == "":
            close_lists()
            html_lines.append("")
            continue

        close_lists()
        html_lines.append(f"<p>{inline(line)}</p>")

    close_lists()
    return "\n".join(html_lines)


def wp_request(endpoint, data=None, method="GET"):
    """Make an authenticated request to the WordPress REST API."""
    credentials = f"{WP_USERNAME}:{WP_APP_PASSWORD}"
    token = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }
    url = f"{WP_URL}/wp-json/wp/v2/{endpoint}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"HTTP {e.code} error from WordPress: {error_body}")
        raise


def get_category_id(category_name):
    """Look up a category by name; create it if it doesn't exist."""
    cats = wp_request(
        f"categories?search={urllib.parse.quote(category_name)}&per_page=10"
    )
    if isinstance(cats, list):
        for cat in cats:
            if cat["name"].lower() == category_name.lower():
                return cat["id"]
    new_cat = wp_request("categories", {"name": category_name}, method="POST")
    if isinstance(new_cat, list):
        new_cat = new_cat[0]
    return new_cat["id"]


def find_existing_post(title):
    """Search for an existing post by title; return its ID or None."""
    results = wp_request(
        f"posts?search={urllib.parse.quote(title)}&per_page=10&status=any"
    )
    if isinstance(results, list):
        for post in results:
            if post["title"]["rendered"].lower() == title.lower():
                return post["id"]
    return None


def write_wp_id(note_path, post_id):
    """Write the WordPress post ID back into the note's frontmatter."""
    with open(note_path, "r", encoding="utf-8") as f:
        raw = f.read()
    if raw.startswith("---"):
        raw = raw[:3] + f"\nwp-id: {post_id}" + raw[3:]
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(raw)


def update_status_in_frontmatter(note_path, status):
    """Update or insert the status field in the note's frontmatter."""
    with open(note_path, "r", encoding="utf-8") as f:
        raw = f.read()

    if raw.startswith("---"):
        end = raw.find("---", 3)
        if end != -1:
            fm_block = raw[3:end]
            if "status:" in fm_block:
                # Replace existing status line
                fm_block = re.sub(r'status:.*', f'status: {status}', fm_block)
            else:
                # Insert status before closing ---
                fm_block = fm_block.rstrip() + f'\nstatus: {status}\n'
            raw = "---" + fm_block + raw[end:]

    with open(note_path, "w", encoding="utf-8") as f:
        f.write(raw)


def build_post_data(note_path, status):
    """Parse note and build the WordPress post data payload."""
    with open(note_path, "r", encoding="utf-8") as f:
        content = f.read()

    frontmatter, body = parse_frontmatter(content)

    title         = frontmatter.get("title") or os.path.splitext(os.path.basename(note_path))[0]
    category_name = frontmatter.get("category", "").strip()
    excerpt       = frontmatter.get("excerpt", "").strip()

    # Strip Obsidian comments (%% ... %%) — both inline and multi-line
    body = re.sub(r'%%.*?%%', '', body, flags=re.DOTALL).strip()

    html_content = markdown_to_html(body)

    post_data = {
        "title":   title,
        "content": html_content,
        "status":  status,
    }

    if excerpt:
        post_data["excerpt"] = excerpt

    if category_name:
        cat_id = get_category_id(category_name)
        post_data["categories"] = [cat_id]

    return post_data, frontmatter, title


def run(note_path, draft_mode=False):
    note_path = resolve_path(note_path)
    note_path = os.path.abspath(note_path)

    if not os.path.exists(note_path):
        print(f"ERROR: File not found: {note_path}")
        sys.exit(1)

    status = "draft" if draft_mode else "publish"
    post_data, frontmatter, title = build_post_data(note_path, status)

    wp_id = frontmatter.get("wp-id", "").strip()

    if wp_id:
        # Post already exists — update it with new status
        result = wp_request(f"posts/{wp_id}", post_data, method="POST")
        if isinstance(result, list):
            result = result[0]
        if draft_mode:
            notify("WordPress Publisher", f"Reverted to draft: {title}")
        else:
            notify("WordPress Publisher", f"Updated: {title}")
    else:
        # New post — check by title as fallback, then create
        existing_id = find_existing_post(title)
        if existing_id:
            result = wp_request(f"posts/{existing_id}", post_data, method="POST")
            if isinstance(result, list):
                result = result[0]
            if draft_mode:
                notify("WordPress Publisher", f"Reverted to draft: {title}")
            else:
                notify("WordPress Publisher", f"Updated: {title}")
        else:
            result = wp_request("posts", post_data, method="POST")
            if isinstance(result, list):
                result = result[0]
            if draft_mode:
                notify("WordPress Publisher", f"Saved as draft: {title}")
            else:
                notify("WordPress Publisher", f"Published: {title}")

        # Write wp-id back to frontmatter for future runs
        write_wp_id(note_path, result["id"])

    # Always update status field in frontmatter
    update_status_in_frontmatter(note_path, status)


if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            print("Usage:")
            print("  Publish : python publish_to_wp.py <note.md>")
            print("  Draft   : python publish_to_wp.py <note.md> --draft")
            sys.exit(1)

        path       = sys.argv[1]
        draft_mode = "--draft" in sys.argv

        run(path, draft_mode=draft_mode)

    except Exception as e:
        print(f"\nERROR: {e}")
        traceback.print_exc()
