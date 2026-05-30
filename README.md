# Obsidian -> WordPress Publisher — Setup Guide

## Overview
Full disclosure this was made with the assistance of claude.

This tool lets you write notes in Obsidian and publish them to your WordPress site with a single hotkey press. It converts your Markdown to HTML, assigns the category, and sends it to WordPress via the REST API. A second hotkey lets you save a post as a draft or revert a live post back to draft. If you run the publish hotkey again on the same note it updates the existing post rather than duplicating it.
I was inspired by this video from Network Chuck. This is a simplified version of his idea but the principle is still the same.
https://www.youtube.com/watch?v=dnE7c0ELEH8

I wanted a way to publish and draft website post from obsidian. I was sick of using the Gutenberg editor since for whatever reason it made it impossible to just get my ideas down on paper.  My speech to text software was also constantly messing up when I used it in the web browser and for whatever reason works perfectly inside obsidian so there's that lol.

There are 2 versions of the script. The test version has some basic logs functionality. It maintains the core functionality of the project but may have some small differences from the main project. If you use it make sure to remove the_test from the file name. I abandoned it because as useful as logs are there are only a handful problems you can run into with this project and I think I figured them all out. I may add them in the future but trying to implement them to have the features that I wanted broke the project.

## Potential issues
- Wrong filename
- Improperly configured shell command
- The note not being in the correct folder
- Invalid or missing credentials
- Wrong site URL
- Site being down/no network connection
- Removing or changing the wp-id


---
## Future features

- Add an error status. As of right now even if the script fails the status will change can be a little confusing. I want out of feature that ensures that if an error occurs the status set to Error and not draft or published.
- Proper logs with the log file stored in the vault itself.
- Linux version but not until I get improper text-to-speech software working on my laptop.
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

Note: NAS/network drives have the exact same set up so I will be using them Interchangeably.

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

(Make a backup before doing this just to be safe)

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
**Repeat this same steps to install Templater.** 

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

1. In Shell Commands settings, click the hotkey icon next to Publish to WordPress
2. Press your desired combo (e.g. Ctrl+Shift+P)
3. Click the hotkey icon next to Save as Draft
4. Press a different combo (e.g. Ctrl+Shift+D)

You can set these keys anything you would like also, you can trigger them by name if you prefer.

---

## Step 7 — Set the working directory (Skip if using a local drive)

1. In Shell Commands settings, click the Environments tab
2. Set the working directory to your vault's root folder path

This ensures the script can find your files when triggered via hotkey.

---

## Step 8 — Set up the template (Optional)

1. 
2. Place Site Post.md in your Obsidian Templates folder
3. Open Settings -> Templater
4. Enable Trigger Templater on new file creation
5. Under Folder Templates, add an entry:
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

| Field      | What it does                                              |
| ---------- | --------------------------------------------------------- |
| `category` | WordPress category. Auto-created if it doesn't exist yet. |
| `excerpt`  | Short summary shown on post listing pages (optional).     |
| `status`   | Updated automatically to publish or draft after each run. |
| `wp-id`    | Added automatically after first publish. Do not delete.   |
Note: If the category section as bank it will be marked as uncategorized

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
## Formatting
To embed videos obsidian requires the following syntax but if the link is just![](Link) If the link is pasted plainly in the note and is pushed to the site it will be embedded in the with post but the note not show the video as embedded. This was a choice I made for consistency sake so that the note looks as close to the site post this possible. The script can handle both options.

Images are taken from the vault and uploaded as well. The program will upload duplicates in the future I plan to fix this issue.

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
