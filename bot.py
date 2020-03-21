# -*- coding: utf-8 -*-
import config
import random
import telebot
from telebot import types
from words import word_list

bot = telebot.TeleBot(config.TOKEN) # start bot

# easy btn generator function
def create_btn(text_btn, call_btn):
  return types.InlineKeyboardButton( text_btn, callback_data = call_btn )

# new game btn
def play_markup():
  play = types.InlineKeyboardMarkup()
  play.add( create_btn( 'Начать игру 🎮', 'play' ) )
  return play

# stop game btn
def give_up_markup(word):
  give_up = types.InlineKeyboardMarkup()
  give_up.add( create_btn( 'Сдаться ❌', 'give_up_{}'.format(word) ) )
  return give_up

# hello menu
@bot.message_handler(commands = [ 'start', 'help' ])
def start(m):
  msg = '*Повесь Бота* 🤖\n\nПравила просты: пишешь буквы пока не угадаешь слово которое я загадал! Ошибаешься - по-тихоньку вешаю Бота! Сильно умный? Пиши слово сразу 🙊'
    
  bot.send_message( m.chat.id, msg, parse_mode = 'Markdown' )
  bot.send_message( m.chat.id, 'Поиграем? 😜', reply_markup = play_markup() )

# start new game
def play(m, word, placeholder, guessed, tries, letters, guess):
  try:
    if not guessed and tries > 0:
      if guess == '': # is start
        msg = 'Угадай-ка букву!\n{}\n{}\nПопыток: {}'.format(' '.join(placeholder), config.stages[tries], tries)
      else:
        if len(guess) == 1 and guess.isalpha(): # is letter
          if guess in letters:
            msg = 'Уже пробовал! Будь внимательнее!\n{}\n{}\nПопыток: {}\nБуквы: {}'.format(' '.join(placeholder), config.stages[tries], tries,' '.join(letters))

          elif guess not in word:
            tries -= 1
            letters.append(guess)
            msg = 'Буквы {} увы нет\n{}\n{}\nПопыток: {}\nБуквы: {}'.format(guess, ' '.join(placeholder), config.stages[tries], tries, ' '.join(letters))

          else:
            letters.append(guess)

            indices = [i for i, letter in enumerate(word) if letter == guess]
            for index in indices:
              placeholder[index] = guess

            if "_" not in placeholder:
              guessed = True

            msg = 'Откройте букву {}!\n{}\n{}\nПопыток: {}\nБуквы: {}'.format(guess, ' '.join(placeholder), config.stages[tries], tries, ' '.join(letters))

        elif len(guess) > 1 and guess.isalpha(): # is word
          if guess == word:
            guessed = True
            placeholder = list(word)
            msg = 'Победа 🎉\n{}\n{}\nПопыток: {}\nБуквы: {}'.format(' '.join(placeholder), config.stages[tries], tries, ' '.join(letters))
          else:
            tries -= 1
            msg = 'Увы это не слово {}!\n{}\n{}\nПопыток: {}\nБуквы: {}'.format(guess, ' '.join(placeholder), config.stages[tries], tries, ' '.join(letters))

        else:
          msg = 'Повторите, я Вас не понимаю\n{}\n{}\nПопыток: {}\nБуквы: {}'.format(' '.join(placeholder), config.stages[tries], tries, ' '.join(letters))
          
      bot.register_next_step_handler( bot.edit_message_text( chat_id = m.chat.id, message_id = m.message_id, text = msg, reply_markup = give_up_markup(word) ), next_guess, last_m = m, word = word, placeholder = placeholder, guessed = guessed, tries = tries, letters = letters ) # input() with current state

    if guessed: # win
      msg = 'Победа 🎉\n{}\n{}\nПопыток: {}\nБуквы: {}'.format(' '.join(placeholder), config.stages[tries], tries, ' '.join(letters))
      bot.edit_message_text( chat_id = m.chat.id, message_id = m.message_id, text = msg )

      bot.send_message(m.chat.id, 'Ещё раз? 😜', reply_markup = play_markup())
    elif tries == 0: # lose
      msg = 'Бот повешен 😞\nСлово: {}\n{}\n{}\nПопыток: {}\nБуквы: {}'.format(word, ' '.join(placeholder), config.stages[tries], tries, ' '.join(letters))
      bot.edit_message_text( chat_id = m.chat.id, message_id = m.message_id, text = msg )

      bot.send_message(m.chat.id, 'Ещё раз? 😜', reply_markup = play_markup())
  
  except Exception as e:
    print(repr(e))

# input()
def next_guess(m, last_m, word, placeholder, guessed, tries, letters):
  try:
    if m.text:
      guess = m.text.upper()
    else:
      guess = '0'

    bot.delete_message(m.chat.id, m.message_id) # delete the guess

    play(m = last_m, word = word, placeholder = placeholder, guessed = guessed, tries = tries, letters = letters, guess = guess) # current state with the guess

  except Exception as e:
    print(repr(e))

# callback from btns
@bot.callback_query_handler(func = lambda call: True)
def callback_query(call):
  try:
    if call.message:
      if call.data == 'play':
        bot.clear_step_handler_by_chat_id( call.message.chat.id )

        # get random word
        word = random.choice(word_list).upper()
        string = '_' * len(word)
        placeholder = list(string) # make an array 

        play( m = call.message, word = word, placeholder = placeholder, guessed = False, tries = 6, letters = [], guess = '' ) # start new game

        bot.answer_callback_query( call.id, '' )
      
      elif call.data.startswith('give_up_'):
        bot.clear_step_handler_by_chat_id( call.message.chat.id )

        msg = 'Бот повешен 😞\nСлово: {}\n{}'.format(call.data.split('_')[-1], config.stages[0])
        bot.edit_message_text( chat_id = call.message.chat.id, message_id = call.message.message_id, text = msg ) # lose msg

        bot.send_message(call.message.chat.id, 'Ещё раз? 😜', reply_markup = play_markup())

        bot.answer_callback_query( call.id, '' )

  except Exception as e:
    print(repr(e))

bot.polling(none_stop = True)