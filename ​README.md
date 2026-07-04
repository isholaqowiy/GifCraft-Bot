# GifCraft Bot 🖼🎞

A high-performance Python Telegram bot optimized for Render.com that merges sequential photos into high-quality animated GIFs with customizable settings.

## 🚀 Step-by-Step Render Deployment Workflows

### Step 1: Commit and Push Code base directly to your GitHub Root Directory
Ensure all required configuration files (`bot.py`, `database.py`, `gif_creator.py`, `gif_editor.py`, `utils.py`, `requirements.txt`, etc.) are placed immediately in the repository root. Do not wrap them inside any subfolders:
```bash
git init
git add .
git commit -m "GifCraft system baseline release build package"
git branch -M main
git remote add origin [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
git push -u origin main

