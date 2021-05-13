# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
import random
import telebot
from telebot import types

from data import stages
from words import word_list

#data
load_dotenv()

bot = telebot.TeleBot(os.getenv('TOKEN')) # start bot

# easy btn generator function
def create_btn(text_btn, call_btn):
  return types.InlineKeyboardButton(text_btn, callback_data = call_btn)

# new game btn
def play_markup():
  play = types.InlineKeyboardMarkup()
  play.add(create_btn('Почати гру 🎮', 'play'))

  return play

# stop game btn
def give_up_markup(word):
  give_up = types.InlineKeyboardMarkup()
  give_up.add(create_btn('Здатися ❌', 'give_up_{}'.format(word)))

  return give_up

# hello menu
@bot.message_handler(commands = ['start', 'help'])
def start(m):
  msg = '*Гра в слова* \n\nПравила прості: пишеш літери поки не вгадаєш слово яке я загадав! Помиляєшся - по-тихоньку вішаю Бота! Сильно розумний? Пиши слово відразу 🙊'

  bot.send_message(m.chat.id, msg, parse_mode = 'Markdown')
  bot.send_message(m.chat.id, 'Зіграємо? 😜', reply_markup = play_markup())

# start new game
def play(m, word, placeholder, guessed, tries, letters, guess):
  try:
    if not guessed and tries > 0:
      # is start
      if guess == '':
        msg = 'Вгадай-ка літеру!\n{}\n{}\nСпроб: {}'.format(
          ' '.join(placeholder), 
          stages[tries], 
          tries
        )

      else:
        # is letter
        if len(guess) == 1 and guess.isalpha():
          if guess in letters:
            msg = 'Вже пробував! Будь уважніше!\n{}\n{}\nСпроб: {}\nЛітери: {}'.format(
              ' '.join(placeholder), 
              stages[tries], 
              tries, 
              ' '.join(letters)
            )

          elif guess not in word:
            tries -= 1
            letters.append(guess)
            msg = 'Літери {} нема\n{}\n{}\nСпроб: {}\nЛітери: {}'.format(
              guess, ' '.join(placeholder), stages[tries], tries, ' '.join(letters)
            )

          else:
            letters.append(guess)

            indices = [i for i, letter in enumerate(
              word) if letter == guess]
            for index in indices:
              placeholder[index] = guess

            if "_" not in placeholder:
              guessed = True

            msg = 'Відкрийте літеру {}!\n{}\n{}\nСпроб: {}\nЛітери: {}'.format(
              guess, ' '.join(placeholder), stages[tries], tries, ' '.join(letters)
            )

        # is word
        elif len(guess) > 1 and guess.isalpha():
          if guess == word:
            guessed = True
            placeholder = list(word)
            msg = 'Перемога 🎉\n{}\n{}\nСпроб: {}\nЛітери: {}'.format(
              ' '.join(placeholder), stages[tries], tries, ' '.join(letters)
            )
          else:
            tries -= 1
            msg = 'На жаль це не слово {}!\n{}\n{}\nСпроб: {}\nЛітери: {}'.format(
              guess, ' '.join(placeholder), stages[tries], tries, ' '.join(letters)
            )

        else:
          msg = 'Повторіть, я Вас не розумію\n{}\n{}\nСпроб: {}\nЛітери: {}'.format(
            ' '.join(placeholder), stages[tries], tries, ' '.join(letters)
          )

      bot.register_next_step_handler(
        bot.edit_message_text(chat_id = m.chat.id, message_id = m.message_id, text = msg, reply_markup = give_up_markup(word)), 
        next_guess, 
        last_m = m, 
        word = word, 
        placeholder = placeholder, 
        guessed = guessed, 
        tries = tries, 
        letters = letters
      ) 

    # win
    if guessed: 
      msg = 'Перемога 🎉\n{}\n{}\nБалів: {}\nЛітери: {}'.format(
        ' '.join(placeholder), stages[tries], tries, ' '.join(letters)
      )

      bot.edit_message_text(chat_id = m.chat.id, message_id = m.message_id, text = msg)

      bot.send_message(m.chat.id, 'Ще раз? 😜', reply_markup = play_markup())

    # lose
    elif tries == 0:
      msg = 'Бот повішений 😞\nСлово: {}\n{}\n{}\nСпроб: {}\nЛітери: {}'.format(
        word, ' '.join(placeholder), stages[tries], tries, ' '.join(letters)
      )

      bot.edit_message_text(chat_id = m.chat.id, message_id = m.message_id, text = msg)

      bot.send_message(m.chat.id, 'Ще раз? 😜', reply_markup = play_markup())

  except Exception as e:
    print(repr(e))

# input()
def next_guess(m, last_m, word, placeholder, guessed, tries, letters):
  try:
    if m.text:
      guess = m.text.upper()
    else:
      guess = '0'

    bot.delete_message(m.chat.id, m.message_id)  # delete the guess

    # current state with the guess
    play(m = last_m, word = word, placeholder = placeholder, guessed = guessed, tries = tries, letters = letters, guess = guess)  

  except Exception as e:
    print(repr(e))

# callback from btns
@bot.callback_query_handler(func = lambda call: True)
def callback_query(call):
  try:
    if call.message:
      if call.data == 'play':
        bot.clear_step_handler_by_chat_id(call.message.chat.id)

        # get random word
        word = random.choice(word_list).upper()
        string = '_' * len(word)
        placeholder = list(string)  # make an array

        # start new game
        play(m = call.message, word = word, placeholder = placeholder, guessed = False, tries = 15, letters = [], guess = '')

        bot.answer_callback_query(call.id, '')

      elif call.data.startswith('give_up_'):
        bot.clear_step_handler_by_chat_id(call.message.chat.id)

        msg = 'Бот повішений 😞\nСлово: {}\n{}'.format(
          call.data.split('_')[-1], stages[0]
        )

        # lose msg
        bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id, text = msg)

        bot.send_message(call.message.chat.id, 'Ще раз? 😜', reply_markup = play_markup())

        bot.answer_callback_query(call.id, '')

  except Exception as e:
    print(repr(e))

bot.polling(none_stop = True)

# Склав: Котов П.В. КВ-03