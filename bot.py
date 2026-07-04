import os
import logging
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

import database
import gif_creator
import gif_editor
import utils

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# State management tags
MENU_CHOICE, UPLOADING_IMAGES, EDITING_GIF = range(3)

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("🖼 Create GIF", callback_data="menu_create")],
        [InlineKeyboardButton("🎞 Edit Existing GIF", callback_data="menu_edit")],
        [InlineKeyboardButton("⚙ GIF Settings", callback_data="menu_settings")],
        [InlineKeyboardButton("❓ Help", callback_data="menu_help")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    utils.ensure_temp_directory()
    await database.init_db()
    
    welcome = (
        "👋 Welcome to *GifCraft Bot*!\n"
        "Turn your photos into beautiful animated GIFs in just a few taps.\n\n"
        "🖼 *Upload multiple images*\n"
        "🎞 *Create smooth animated GIFs*\n"
        "⚙ *Customize speed, quality, and looping*\n"
        "🚀 *Fast, simple, and high quality*\n\n"
        "Tap a button below or start uploading images to begin."
    )
    if update.message:
        await update.message.reply_text(welcome, reply_markup=get_main_menu(), parse_mode="Markdown")
    return MENU_CHOICE

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "❓ *GifCraft Manual Guide*\n\n"
        "1. Click *Create GIF* and send between 2 and 50 photos.\n"
        "2. When done uploading, send the command /done to build the animation.\n"
        "3. Adjust frame configuration states under the *Settings* drawer menu anytime."
    )
    if update.message: await update.message.reply_text(msg)
    elif update.callback_query: await update.callback_query.message.reply_text(msg)

async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    
    if query.data == "menu_create":
        context.user_data['upload_queue'] = []
        await query.message.reply_text("🖼 Send your frames one by one (JPG, PNG, WEBP, BMP). When finished, type or click: /done")
        return UPLOADING_IMAGES
        
    elif query.data == "menu_edit":
        await query.message.reply_text("🎞 Upload an existing animated GIF file to reverse or compress:")
        return EDITING_GIF
        
    elif query.data == "menu_settings":
        kb = [
            [InlineKeyboardButton("Speed: Slow", callback_data="set_speed_Slow"),
             InlineKeyboardButton("Speed: Fast", callback_data="set_speed_Fast")],
            [InlineKeyboardButton("Loop: Infinite", callback_data="set_loop_Infinite"),
             InlineKeyboardButton("Loop: Once", callback_data="set_loop_Once")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="go_home")]
        ]
        await query.edit_message_text("⚙ *Configure Default Generation Framework Settings:*", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        
    elif query.data.startswith("set_"):
        _, param, val = query.data.split("_")
        await database.update_setting(uid, param, val)
        await query.message.reply_text(f"✅ Updated operational parameter *{param}* to: `{val}`", parse_mode="Markdown")
        
    elif query.data == "go_home":
        await query.edit_message_text("Choose an option below to begin:", reply_markup=get_main_menu())
        
    elif query.data == "menu_help":
        await help_cmd(update, context)
        
    return MENU_CHOICE

async def handle_frame_uploads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    photo = update.message.photo[-1] if update.message.photo else (update.message.document if update.message.document and update.message.document.mime_type.startswith("image/") else None)
    
    if not photo:
        await update.message.reply_text("❌ Invalid asset format type. Send an image.")
        return UPLOADING_IMAGES
        
    queue = context.user_data.setdefault('upload_queue', [])
    idx = len(queue)
    
    if idx >= 50:
        await update.message.reply_text("❌ Queue threshold limits breached. You cannot exceed 50 frames.")
        return UPLOADING_IMAGES
        
    tg_file = await context.bot.get_file(photo.file_id)
    path = os.path.join(utils.TEMP_DIR, f"user_{uid}_frame_{idx}.png")
    await tg_file.download_to_drive(path)
    queue.append(path)
    
    await update.message.reply_text(f"📝 Frame #{idx + 1} logged. Ready for processing, or send /done to finalize.")
    return UPLOADING_IMAGES

async def compile_gif_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    queue = context.user_data.get('upload_queue', [])
    
    if len(queue) < 2:
        await update.message.reply_text("❌ Minimum frame bounds violated. Send at least 2 images before invoking /done.")
        return UPLOADING_IMAGES
        
    status = await update.message.reply_text("⏳ Processing canvas frames and building your high-quality GIF...")
    settings = await database.get_settings(uid)
    out_path = os.path.join(utils.TEMP_DIR, f"user_{uid}_output.gif")
    
    success = gif_creator.create_animated_gif(queue, out_path, settings)
    
    if success and os.path.exists(out_path):
        with open(out_path, 'rb') as f:
            await update.message.reply_animation(animation=f, caption="✨ Your animated GIF is ready!")
        await database.log_gif(uid, out_path)
    else:
        await update.message.reply_text("❌ Failed to compile your frames into a GIF.")
        
    utils.clear_user_cache(uid)
    await status.delete()
    return MENU_CHOICE

async def handle_gif_editing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    doc = update.message.document if update.message.document and update.message.document.mime_type == "image/gif" else (update.message.animation if update.message.animation else None)
    
    if not doc:
        await update.message.reply_text("❌ Please send an animated GIF file to execute transformation processing.")
        return EDITING_GIF
        
    tg_file = await context.bot.get_file(doc.file_id)
    in_path = os.path.join(utils.TEMP_DIR, f"user_{uid}_edit_src.gif")
    await tg_file.download_to_drive(in_path)
    
    out_path = os.path.join(utils.TEMP_DIR, f"user_{uid}_reversed.gif")
    if gif_editor.reverse_gif(in_path, out_path):
        with open(out_path, 'rb') as f:
            await update.message.reply_animation(animation=f, caption="🔄 Here is your reversed GIF animation!")
    else:
        await update.message.reply_text("❌ Error trying to reverse the animation.")
        
    utils.clear_user_cache(uid)
    return MENU_CHOICE

def main():
    if not TOKEN:
        print("Fatal error: Missing BOT_TOKEN")
        return
        
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(menu_router, pattern="^menu_")
        ],
        states={
            MENU_CHOICE: [CallbackQueryHandler(menu_router, pattern="^(menu_|go_home|set_)")],
            UPLOADING_IMAGES: [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_frame_uploads),
                CommandHandler("done", compile_gif_done)
            ],
            EDITING_GIF: [MessageHandler(filters.ANIMATION | filters.Document.ALL, handle_gif_editing)]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    application.add_handler(conv_handler)
    print("GifCraft Listening Threads Active...")
    application.run_polling()

if __name__ == '__main__':
    main()

