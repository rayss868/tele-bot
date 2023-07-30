import logging
import random
import threading
import time
from telegram import Update, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

# Ganti "TOKEN_BOT_ANDA" dengan token bot Telegram Anda
TOKEN = "6063005347:AAEtWgNbKVQfzSVZtJZKUDz46CubzqkMy1A"

# Daftar status verifikasi
WAITING_FOR_VERIFICATION = 1
VERIFIED = 2

def generate_question():
    # Fungsi ini akan menghasilkan soal penjumlahan dan pengurangan acak
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)

    # Pilih secara acak apakah akan melakukan penjumlahan atau pengurangan
    operator = random.choice(['+', '-'])

    if operator == '+':
        answer = num1 + num2
        question = f"Berapa hasil dari {num1} + {num2}?"
    else:
        answer = num1 - num2
        question = f"Berapa hasil dari {num1} - {num2}?"

    return question, answer

def welcome_message(update: Update, context: CallbackContext):
    new_members = update.message.new_chat_members
    chat_id = update.message.chat_id

    for new_member in new_members:
        context.user_data[new_member.id] = {'status': WAITING_FOR_VERIFICATION, 'answer': None}
        question, answer = generate_question()
        context.user_data[new_member.id]['answer'] = answer

        welcome_text = f"Selamat datang {new_member.first_name} di grup Telegram kami! 🎉🌟 Senang Anda bergabung!\n\n"
        welcome_text += f"Sebelum dapat bergabung sepenuhnya, kami perlu melakukan verifikasi singkat.\n\n{question}"

        message = context.bot.send_message(chat_id=chat_id, text=welcome_text, parse_mode=ParseMode.MARKDOWN)
        context.user_data[new_member.id]['question_message_id'] = message.message_id

        # Timer untuk membatasi waktu pengguna menjawab
        threading.Timer(30, timeout_verification, args=[update, context, new_member.id]).start()

def check_answer(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if user_id in context.user_data:
        if context.user_data[user_id]['status'] == WAITING_FOR_VERIFICATION:
            user_answer = update.message.text
            expected_answer = context.user_data[user_id]['answer']

            try:
                user_answer = int(user_answer)
                if user_answer == expected_answer:
                    user = update.message.from_user
                    welcome_text = f"Selamat datang {user.first_name} di grup kami! 🎉🌟 Senang Anda bergabung!\n\n"
                    welcome_text += "Berikut beberapa sumber daya yang berguna:\n\n"
                    welcome_text += "1. Kunjungi forum UiPath untuk mendapatkan jawaban atas pertanyaan Anda: [Link Forum UiPath](https://forum.uipath.com)\n"
                    welcome_text += "2. Tambahkan pengetahuan Anda dengan kursus pelatihan resmi dari UiPath: [Link Training UiPath](https://academy.uipath.com)\n\n"
                    welcome_text += "Jangan ragu untuk bertanya, berbagi ide, atau berdiskusi tentang apapun di grup ini. Kami harap Anda dapat menikmati pengalaman berharga bersama kami! 🤗🎈"

                    update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

                    # Set status pengguna menjadi "VERIFIED"
                    context.user_data[user_id]['status'] = VERIFIED

                else:
                    update.message.reply_text("Maaf, jawaban Anda salah. Anda telah mencoba menjawab dengan salah 1 kali. Chat Anda telah dihapus dari grup.")
                    # Jika jawaban salah, bot akan mengeluarkan pengguna dari grup
                    context.bot.kick_chat_member(chat_id=update.message.chat_id, user_id=user_id)

            except ValueError:
                update.message.reply_text("Mohon jawab dengan angka yang valid.")

            # Hapus pesan verifikasi dari bot
            if 'question_message_id' in context.user_data[user_id]:
                context.bot.delete_message(chat_id=update.message.chat_id, message_id=context.user_data[user_id]['question_message_id'])

            del context.user_data[user_id]

def timeout_verification(update: Update, context: CallbackContext, user_id: int):
    # Jika user tidak menjawab dalam waktu 30 detik, maka hapus chat pribadinya dan keluarkan dari grup
    if user_id in context.user_data and context.user_data[user_id]['status'] == WAITING_FOR_VERIFICATION:
        update.message.reply_text("Maaf, Anda tidak menjawab dalam waktu yang ditentukan. Chat Anda telah dihapus dari grup.")
        context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
        context.bot.kick_chat_member(chat_id=update.message.chat_id, user_id=user_id)

        # Hapus pesan verifikasi dari bot
        if 'question_message_id' in context.user_data[user_id]:
            context.bot.delete_message(chat_id=update.message.chat_id, message_id=context.user_data[user_id]['question_message_id'])

        del context.user_data[user_id]

def main():
    # Konfigurasi log untuk melihat pesan log dari bot
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    # Buat objek Updater dan pindahkan token bot Anda ke sini
    updater = Updater(token=TOKEN, use_context=True)

    # Dapatkan pengelola dispatcher untuk mendaftarkan handler
    dispatcher = updater.dispatcher

    # Daftarkan handler untuk menangani ketika ada anggota baru bergabung
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome_message))

    # Daftarkan handler untuk menangani jawaban dari verifikasi
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, check_answer))

    # Jalankan bot
    updater.start_polling()

    # Jaga agar bot tetap berjalan sampai diberhentikan dengan CTRL-C
    updater.idle()

if __name__ == '__main__':
    main()
