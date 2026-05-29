# Obsidian -> WordPress Publisher — Setup Guide

## Overview

This tool lets you write notes in Obsidian and publish them to your WordPress site with a single hotkey press. It converts your Markdown to HTML, assigns the category, and sends it to WordPress via the REST API. A second hotkey lets you save a post as a draft or revert a live post back to draft. If you run the publish hotkey again on the same note it updates the existing post rather than duplicating it.

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

If your Obsidian vault is stored on a NAS or SMB shere, you must map it as a Windows drive letter before using this tool. Windows CMD does not support UNC paths (\Server\Share) and Obsidian may pass these to the script.

Note: NAS/network drives have the exact same set up so be using them no changeable

**To map your Network share:**

1. Open File Explorer -> This PC -> three dots (...) -> Map network drive
2. Choose a drive letter (e.g. Z:)
3. Enter your network drive path
4. Check Reconnect at sign-in
5. Click Finish

Then open Obsidian and make sure your vault is opened via the mapped drive letter and not the UNC path. If the NAS is offline at boot, the mapping may not connect automatically and the hotkey will fail until the NAS is back online.

==**If your vault is on your local C: drive, ignore this section entirely.**==

---

## Step 1 — Enable Application Passwords in WordPress

Some hosts disable this feature by default. If you don't see Application Passwords in your WordPress profile, add this line to wp-config.php. Note there might be some slight variation between the naming of this folder based on your web host.

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
5. Copy the password shown (looks like: xxxx xxxx xxxx xxxx xxxx xxxx) You will not be able to see it again after leaving the page, so copy it immediately.

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

## Step 5 — Add the publish and draft commands

Add two shell commands — one to publish, one to draft.

**Publish command:**

1. Go to Settings -> Shell Commands
    
2. Click + New shell command
    
3. Enter the following, replacing the path with wherever you saved the script:
    
    python "C:\path\to\publish_to_wp.py" "{{file_path:absolute}}"
    
    {{file_path:absolute}} is an Obsidian variable — leave it exactly as written.
    
4. Click the gear icon next to your new command
    
5. In the Alias field type: Publish to WordPress
    
6. Save
    

**Draft command:**

1. Click + New shell command again
    
2. Enter the following (same path, just add --draft at the end):
    
    python "C:\path\to\publish_to_wp.py" "{{file_path:absolute}}" --draft
    
3. Click the gear icon
    
4. In the Alias field type: Save as Draft
    
5. Save
    

---

## Step 6 — Bind hotkeys

Bind a hotkey to each command:

1. In Shell Commands settings, click the hotkey icon next to Publish to WordPress
2. Press your desired combo (e.g. Ctrl+Shift+P)
3. Click the hotkey icon next to Save as Draft
4. Press a different combo (e.g. Ctrl+Shift+D)

You can set these key anything you would like also, you can trigger them by name if you prefer.

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
## Deleting a post

This tool can publish and update posts but cannot delete them. To remove a post from your site go to WordPress Dashboard -> Posts, find the post, and move it to trash from there. You can also set it back to draft if you want to hide it temporarily without deleting it.

---
## How to write a post

1. Create a new note inside your site posts folder
2. The template is applied automatically (if used)
3. Fill in `category:` and optionally `excerpt:`
4. The note filename becomes the post title — name it accordingly
5. Write your content in Markdown
6. Press your publish or draft hotkey when ready

> The frontmatter block (the `---` section) must start on the very first line of the note with no blank lines above it, otherwise the script won't detect it and the category won't be applied.

> Category names autocomplete once you have used them before.

---

## Commenting out text

Wrapping any text in double percent signs (`%%`) tells the script to strip it before publishing. The text is still visible to you in Obsidian but will never appear on your site.

Single line:

```
%% This note won't be published %%
```

Multiple lines:

```
%%
This whole block is private.
Great for keeping your category list handy in the template.
%%
```

Use it freely for reminders, drafting notes, or anything you want to keep out of the published post.

---

## Template fields

|Field|What it does|
|---|---|
|`category`|WordPress category. Auto-created if it doesn't exist yet.|
|`excerpt`|Short summary shown on post listing pages (optional).|
|`status`|Updated automatically to publish or draft after each run.|
|`wp-id`|Added automatically after first publish. Do not delete.|

The post title comes from the note filename — no need to set it manually.

---

## How updates work

The first time you publish or draft a note the script writes a `wp-id` field into your frontmatter. Next time you press either hotkey on the same note it finds that ID and updates the correct WordPress post instead of creating a duplicate.

---

## Draft mode

The draft hotkey has two behaviours depending on the state of the note:

- No `wp-id` → creates a new draft on WordPress, not visible on your site
- Has `wp-id` → updates the post and sets it to draft, taking it down if live

The publish hotkey works the same way in reverse — pressing it on a draft note makes it live. The `status:` field in your frontmatter always reflects the current state so you can see at a glance whether a note is live or in draft.

---

## Troubleshooting

**"python is not recognized"** Reinstall Python from python.org and check Add to PATH during install.

**401 Unauthorized** Double-check your `WP_USERNAME` and `WP_APP_PASSWORD` in the script. Make sure Application Passwords are enabled (see Step 1).

**Post not showing up on site** Check WordPress Dashboard -> Posts to confirm it was created. Make sure your homepage is set to Latest Posts (Settings -> Reading). Verify your `WP_URL` has no trailing slash.

**Hotkey does nothing / file not found** Make sure your NAS is mapped and online (if applicable). Check the vault is opened via the mapped drive letter, not a UNC path. Confirm the Working directory is set in Shell Commands -> Environments.

**Post publishes but has no category** Check for typos in the category field. The script is case-insensitive but will create a new category if the spelling doesn't match an existing one.

**Draft hotkey opens the Python script instead of running it** Make sure `--draft` is outside the quotes in the shell command:

```
python "C:\path\to\publish_to_wp.py" "{{file_path:absolute}}" --draft
```

**Script fails with a connection error** Check that you have an active internet connection and that your WordPress site is reachable in a browser.
