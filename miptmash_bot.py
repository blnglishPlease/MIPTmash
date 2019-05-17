from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater
from telegram import ReplyKeyboardMarkup
import os
from requests import get
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np


class MIPTmash_bot(object):
    def __init__(self, token):
        self.updater = Updater(token=token)
        handler = MessageHandler(Filters.text | Filters.command, self.handle_message)
        self.updater.dispatcher.add_handler(handler)
        self.keyboard_hello = ReplyKeyboardMarkup([['Голосовать', 'Топ 5', 'Пока']], one_time_keyboard=True)
        self.keyboard_choice = ReplyKeyboardMarkup([['1', '2']], one_time_keyboard=True)
        if not os.path.exists('./base'):
            self.database = pd.DataFrame(columns=['id', 'name', 'photo_path', 'rating'])
            self.create_base()
        else:
            self.database = pd.read_csv('./base/database.csv')

    def run(self):
        self.updater.start_polling()

    def create_base(self):
        os.makedirs('./base/photo')
        req = get('http://wikimipt.org/wiki/%D0%9A%D0%B0%D1%82%D0%B5%D0%B3%D0%BE%D1%80%D0%B8%D1%8F:%D0%9F%D1%80%D0%B5%D0%BF%D0%BE%D0%B4%D0%B0%D0%B2%D0%B0%D1%82%D0%B5%D0%BB%D0%B8_%D0%BF%D0%BE_%D0%B0%D0%BB%D1%84%D0%B0%D0%B2%D0%B8%D1%82%D1%83')
        soup = BeautifulSoup(req.text)
        id = 0
        self.parse_page(soup, id)
        self.database.to_csv(f'{os.getcwd()}/base/database.csv')


    def parse_page(self, soup, id):
        id = self.find_people(soup, id)
        temp_ref = soup.find_all('div', attrs={'id': 'mw-pages'})
        ref = temp_ref[0].find('a', text='Следующая страница')
        if ref != None:
            if ref['href'].find('http') == -1:
                new_ref = 'http://wikimipt.org' + ref['href']
            else:
                new_ref = ref['href']
            new_req = get(new_ref)
            new_soup = BeautifulSoup(new_req.text)
            self.parse_page(new_soup, id)


    def find_people(self, soup, id):
        for group in soup.find_all('div', attrs={'class': 'mw-category-group'}):
            people_per_group = 0
            for teacher in group.find_all('a'):
                if teacher['href'].find('http') == -1:
                    teacher['href'] = 'http://wikimipt.org' + teacher['href']
                ref_to_teacher = teacher['href']
                req_to_teacher = get(ref_to_teacher)
                name = teacher['title']
                teacher_soup = BeautifulSoup(req_to_teacher.text)
                id = self.add_to_base(teacher_soup, name, id)
                people_per_group += 1

        return id

    def add_to_base(self, soup, name, id):
        photo = soup.find('img')
        if photo['src'] != '/images/5/56/Placeholder.gif':
            if photo['src'].find('http') == -1:
                img_ref = 'http://wikimipt.org' + photo['src']
            else:
                img_ref = photo['src']
            img = get(img_ref)
            out = open(f'{os.getcwd()}/base/photo/{id}.jpg', 'wb')
            out.write(img.content)
            out.close()
            db = pd.DataFrame([{'id' : id, 'name' : name, 'photo_path' : f'{os.getcwd()}/base/photo/{id}.jpg', 'rating' : 400}])
            self.database = pd.concat((self.database, db))
            id += 1
        return id


    def handle_message(self, bot, update):
        chat_id = update.message.chat_id
        if update.message.text == "/start":
            bot.sendMessage(chat_id=chat_id, text="Привет! Готов выбрать самого милого преподавателя? Хочешь голосовать или увидеть топ 5?", reply_markup=self.keyboard_hello)
        if update.message.text.lower() == 'голосовать':

            self.id_1 = np.random.randint(low = 0, high = self.database.id.count())
            self.id_2 = np.random.randint(low = 0, high = self.database.id.count())
            self.vote = True
            while self.id_1 == self.id_2:
                self.id_2 = np.random.randint(low = 0, high = self.database.id.count())
            bot.send_photo(chat_id, open(self.database.iloc[self.id_1, 3], 'rb'))
            bot.send_photo(chat_id, open(self.database.iloc[self.id_2, 3], 'rb'), reply_markup=self.keyboard_choice)

        elif update.message.text == '1':
            if self.vote:

                rating1 = self.database.iloc[self.id_1, 4]
                rating2 = self.database.iloc[self.id_2, 4]
                self.database.iloc[self.id_1, 4] += 1 / (1 + (rating2 - rating1) / 40)
                self.database.iloc[self.id_2, 4] -= 1 / (1 + (rating1 - rating2) / 40)

                del self.database['Unnamed: 0']
                self.database.to_csv(f'{os.getcwd()}/base/database.csv')
                self.database = pd.read_csv('./base/database.csv')

                bot.send_message(chat_id, 'Твой голос учтен! Хочешь голосовать или увидеть топ 5?', reply_markup=self.keyboard_hello)
                self.vote = False

            else:

                bot.send_message(chat_id, 'Хочешь голосовать или увидеть топ 5?', reply_markup=self.keyboard_hello)

        elif update.message.text.lower() == '2':
            if self.vote:

                rating1 = self.database.iloc[self.id_1, 4]
                rating2 = self.database.iloc[self.id_2, 4]
                self.database.iloc[self.id_1, 4] -= 1 / (1 + (rating2 - rating1) / 40)
                self.database.iloc[self.id_2, 4] += 1 / (1 + (rating1 - rating2) / 40)

                del self.database['Unnamed: 0']
                self.database.to_csv(f'{os.getcwd()}/base/database.csv')
                self.database = pd.read_csv('./base/database.csv')

                bot.send_message(chat_id, 'Твой голос учтен! Хочешь голосовать или увидеть топ 5?', reply_markup=self.keyboard_hello)
                self.vote = False

            else:

                bot.send_message(chat_id, 'Хочешь голосовать или увидеть топ 5?', reply_markup=self.keyboard_hello)

        elif update.message.text.lower() == 'пока':

            bot.send_message(chat_id, 'До новых встреч')

        elif update.message.text.lower() == 'топ 5':
            sort_database = self.database.sort_values('rating', ascending = False)
            for top in range(5):
                bot.send_message(chat_id, f'{top + 1} место: {sort_database.iloc[top, 2]}')
                bot.send_photo(chat_id, open(sort_database.iloc[top, 3], 'rb'))
            bot.send_message(chat_id, 'Хочешь голосовать или увидеть топ 5?', reply_markup=self.keyboard_hello)

def main():
    MIPTmash_bot('728600486:AAE4n6gSxTQ7fuMxzcqDImueBdtcGvEY8b0').run()

if __name__ == '__main__':
    main()
