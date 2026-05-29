# Obsidian2web
# Obsidian -> WordPress Publisher — Setup Guide

## Overview

Full disclosure this tool was written with Claude

This tool lets you write posts in Obsidian and publish them to your WordPress site with a single hotkey press. It converts your Markdown to HTML, assigns the correct category, and sends it to WordPress via the REST API. If you run the hotkey again on the same note it updates the existing post rather than duplicating it.

---

## Components

- Windows PC
- Python 3.10+
- Obsidian with the following plugins:
    - Shell Commands (community plugin)
    - Templater (community plugin — only needed if you want auto-template on new notes)
- WordPress site with HTTPS
- An internet connection at publish time
- Your Obsidian vault stored on a mapped network drive (if using a NAS — see note below)

---

## NAS / Network Drive Note

If your Obsidian vault is stored on a NAS, you must map it as a Windows drive letter before using this tool. Windows CMD does not support UNC paths (\\Server\Share) and Obsidian may pass these to the script.

**To map your NAS:**

1. Open File Explorer -> This PC -> three dots (...) -> Map network drive
2. Choose a drive letter (e.g. Z:)
3. Enter your NAS share path
4. Check Reconnect at sign-in
5. Click Finish

Then open Obsidian and make sure your vault is opened via the mapped drive letter and not the UNC path. If the NAS is offline at boot, the mapping may not connect automatically and the hotkey will fail until the NAS is back online.

==**If your vault is on your local C: drive, ignore this section entirely.**==

---

## Step 1 — Enable Application Passwords in WordPress

Some hosts disable this feature by default. If you don't see Application Passwords in your WordPress profile, add this line to wp-config.php above the "That's all, stop editing" comment:

```php
// Enable Application Passwords for REST API authentication (Obsidian publisher)
define( 'WP_APPLICATION_PASSWORDS_ENABLED', true );
```

On most hosts this file is located at public_html/wp-config.php and can be edited via the host's File Manager.

---

## Step 2 — Generate a WordPress Application Password

1. Log into your WordPress dashboard
2. Go to Users -> Profile
3. Scroll down to Application Passwords
4. Type a name like Obsidian and click Add New Application Password
5. Copy the password shown (looks like: xxxx xxxx xxxx xxxx xxxx xxxx)
   You will not be able to see it again after leaving the page, so copy it immediately.

---

## Step 3 — Configure the script

Open publish_to_wp.py in Notepad and fill in the CONFIG section at the top:

```python
WP_URL          = "https://your-site.com"       # No trailing slash
WP_USERNAME     = "your_wordpress_username"
WP_APP_PASSWORD = "xxxx xxxx xxxx xxxx xxxx xxxx"
```

Save the script somewhere permanent, e.g. C:\Scripts\

---

## Step 4 — Install the Shell Commands plugin

1. Open Obsidian -> Settings -> Community Plugins -> Browse
2. Search for Shell Commands and install it
3. Toggle it on

---

## Step 5 — Add the publish command

1. Go to Settings -> Shell Commands
2. Click + New shell command
3. Enter the following, replacing the path with wherever you saved the script:

   python "C:\path\to\publish_to_wp.py" "{{file_path:absolute}}"

   {{file_path:absolute}} is an Obsidian variable — leave it exactly as written.

4. Click the gear icon next to your new command
5. In the Alias field type a friendly name like: Publish to WordPress
6. Save

---

## Step 6 — Bind a hotkey

1. In Shell Commands settings, click the hotkey icon next to your command
2. Press your desired key combination (e.g. Ctrl+Shift+P)

The alias you set will appear in the Obsidian Command Palette (Ctrl+P) so you
can also trigger it by name if you prefer.

---

## Step 7 — Set the working directory (Skip if using a local drive)

1. In Shell Commands settings, click the Environments tab
2. Set the Working directory to your vault's root folder path

This ensures the script can find your files when triggered via hotkey.

---

## Step 8 — Set up the template (Optional)

1. Place Site Post.md in your Obsidian Templates folder
2. Open Settings -> Templater
3. Enable Trigger Templater on new file creation
4. Under Folder Templates, add an entry:
   - Folder: your site posts folder
   - Template: Site Post

New notes created in that folder will now automatically get the template applied.

---

## Writing in Markdown

Your posts are written in Markdown — a lightweight way of formatting text using
simple symbols. Obsidian renders it visually while you write, and the script
converts it to HTML for WordPress automatically.

A quick reference:

| Format          | Markdown syntax               |
|-----------------|-------------------------------|
| Heading         | # H1  ## H2  ### H3           |
| Bold            | **bold text**                 |
| Italic          | *italic text*                 |
| Bold + italic   | ***bold and italic***         |
| Strikethrough   | ~~strikethrough~~             |
| Inline code     | `code`                        |
| Code block      | ``` (three backticks)         |
| Link            | [link text](https://url.com)  |
| Image           | ![alt text](https://url.com)  |
| Bullet list     | - item                        |
| Numbered list   | 1. item                       |
| Blockquote      | > quoted text                 |
| Horizontal rule | ---                           |

Note: images are only supported if they are already hosted at a public URL
(e.g. an image you uploaded manually to WordPress Media Library). Local images
stored in your Obsidian vault will not appear in the published post. To use an
image, upload it via WordPress Dashboard -> Media -> Add New, copy the URL, and
reference it in your note like: ![alt text](https://your-site.com/wp-content/uploads/image.jpg)

For a full reference see: https://www.markdownguide.org/cheat-sheet

---

## Deleting a post

This tool can publish and update posts but cannot delete them. To remove a
post from your site go to WordPress Dashboard -> Posts, find the post, and
move it to trash from there. You can also set it back to draft if you want
to hide it temporarily without deleting it.

---

## How to write a post

1. Create a new note inside your site posts folder
2. The template is applied automatically (if used)
3. Fill in category: and optionally excerpt:
4. The note filename becomes the post title — name it accordingly
5. Write your content in Markdown
6. Use %% comment text %% for any notes you don't want published
7. Press your hotkey to publish

Note: the frontmatter block (the --- section) must start at the very first line
of the note with no blank lines above it, otherwise the script won't detect it
and the category won't be applied.

Note: category names will autocomplete once you have used them before. You can
also use the %% comment feature to write your category list inside the template
as a reference — it won't appear in the published post.

---

## Template fields

| Field    | What it does                                               |
|----------|------------------------------------------------------------|
| category | WordPress category. Auto-created if it doesn't exist yet.  |
| excerpt  | Short summary shown on post listing pages (optional).      |
| wp-id    | Added automatically after first publish. Do not delete.    |

The post title comes from the note filename — no need to set it manually.

---

## How updates work

The first time you publish a note the script writes a wp-id field into your
frontmatter. Next time you press the hotkey on the same note it finds that ID
and updates the existing WordPress post instead of creating a duplicate.

---

## Obsidian comments

Anything wrapped in %% will be stripped before publishing:

  %% This is a private note — it won't appear on the site %%

Works inline or across multiple lines.

---

## Troubleshooting

**"python is not recognized"**
Reinstall Python from python.org and check Add to PATH during install.

**401 Unauthorized**
Double-check your WP_USERNAME and WP_APP_PASSWORD in the script.
Make sure Application Passwords are enabled (see Step 1).

**Post not showing up on site**
Check WordPress Dashboard -> Posts to confirm it was created.
Make sure your homepage is set to Latest Posts (Settings -> Reading).
Verify your WP_URL has no trailing slash.

**Hotkey does nothing / file not found**
Make sure your NAS is mapped and online (if applicable).
Check the vault is opened via the mapped drive letter, not a UNC path.
Confirm the Working directory is set in Shell Commands -> Environments.

**Script fails with a connection error**
Check that you have an active internet connection and that your WordPress
site is reachable in a browser.
