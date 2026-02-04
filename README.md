<h1 align="center">
  Save Restricted Content Bot v3
</h1>

The Save Restricted Content Bot is a stable Telegram bot developed by LastPerson07. It enables users to retrieve restricted messages from Telegram channels and groups, offering features such as custom thumbnail support and the ability to upload files up to 4GB. Additionally, the bot supports downloading videos from platforms like YouTube, Instagram, and Facebook, along with over 100 other sites

[Telegram](https://t.me/save_restricted_content_bots) | [See Recent Updates](https://github.com/LastPerson07/Save-Restricted-Content-Bot-V2/tree/v3#updates)

### Star the repo it motivate us to update new features
Please do start and max fork thanks 

## 📚 About This Branch
- This branch is based on `Pyrogram V2` offering enhanced stability and a forced login feature. User are not forced to login in bot for public channels but for public groups and private channel they have to do login.
- for detailed features scroll down to features section

---

## 🔧 Features
- Extract content from both public and private channels/groups.
- Custom bot functionality added use `/setbot`
- 128 bit encryption for data saving use @v3saverbot on telegram to generate `MASTER_KEY`, `IV_KEY`
- Rename and forward content to other channels or users.
- extract restricted content from other bots how to use format link like `https://botusername(without @)/message_id(get it from plus messenger)`
- `/login` method along with `session` based login
- Custom captions and thumbnails.
- Auto-remove default video thumbnails.
- Delete or replace words in filenames and captions.
- Auto-pin messages if enabled.
- download yt/insta/Twitter/fb ect normal ytdlp supported sites that supports best format
- Login via phone number.
- **Supports 4GB file uploads**: The bot can handle large file uploads, up to 4GB in size.
- file splitter if not premium string
- **Enhanced Timer**: Distinct timers for free and paid users to limit usage and improve service.
- **Improved Looping**: Optimized looping for processing multiple files or links, reduci...(truncated 4453 characters)...dit `config.py` or set environment variables on Render.
3. Go to [render.com](https://render.com), sign up/log in.
4. Create a new web service, select the free plan.
5. Connect your GitHub repo and deploy ✅.

</details>

<details>
<summary><b>Deploy on Koyeb</b></summary>

1. Fork and star the repo.
2. Edit `config.py` or set environment variables on Koyeb.
3. Create a new service, select `Dockerfile` as build type.
4. Connect your GitHub repo and deploy ✅.

</details>

---
### ⚠️ Must Do: Secure Your Sensitive Variables

**Do not expose sensitive variables (e.g., `API_ID`, `API_HASH`, `BOT_TOKEN`) on GitHub. Use environment variables to keep them secure.**

### Configuring Variables Securely:

- **On VPS or Local Machine:**
  - Use a text editor to edit `config.py`:
    ```bash
    nano config.py

Alternatively, export as environment variables:Bashexport API_ID=your_api_id
export API_HASH=your_api_hash
export BOT_TOKEN=your_bot_token
For Cloud Platforms (Heroku, Railway, etc.):
Set environment variables directly in your platform’s dashboard.

Using .env File:
Create a .env file and add your credentials:textAPI_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
Make sure to add .env to .gitignore to prevent it from being pushed to GitHub.


Why This is Important?
Your credentials can be stolen if pushed to a public repository. Always keep them secure by using environment variables or local configuration files.

🛠️ Terms of Use
Visit the Terms of Use page to review and accept the guidelines.
Important Note
Note: Changing the terms and commands doesn't magically make you a developer. Real development involves understanding the code, writing new functionalities, and debugging issues, not just renaming things. If only it were that easy!

  Developed by LastPerson07