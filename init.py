# -*- coding: utf-8 -*-

import argparse
import configparser
import os
import datetime
import re
import requests
import sys

class VKConfig:

	#default value
	path = None
	start_date = None
	start_time = None
	virtual = None

	Source_type = ''	
	Source_input = ''
	permission_score = ''
	appid = 0
	GroupID = 0
	save_token = 1
	token = ''
	
	Default_tag = ''
	autor_marker = 0
	mute_notifications = 0
	
	conflict_time_act = ''
	absence_spost_act = ''
	time_type = ''
	
	Time_dict = {}
	link_list = []
	ExcepTag = []
	STag_list = []
	STimeTag_dict = {}
	
	ConfigLoad = False
	ConfigCheck = False
	
	def __init__(self, path = 'Config.ini'):
		self.path = path

	def loadconfig(self):
	
		def wait_exit():
			# Функция которая не позволит сразу закрыть консоль если запускать скрипт двойным кликом по файлу
			input("Нажмите Enter для выхода...")
			exit()

		
		def arg_parser():
			# Обработка аргументов
			parser = argparse.ArgumentParser()
			parser.add_argument ('-sd', '--start_date', type=str, help="Дата начала постинга. Формат 01.01.2020 или today если с \"сегодня\".")\
			# TODO
			parser.add_argument ('-st', '--start_time', type=str, help="Время начала постинга. Формат 10-00.")
			parser.add_argument ('-vr', '--virtual', type=str, help="Подготовить посты и выйти без постинга. Для проверки наличия материалов на все задействованые даты время и ошибок. Значения 0 или 1.")
			args = parser.parse_args()
			self.start_date = args.start_date
			self.start_time = args.start_time
			self.virtual = args.virtual

		def config_parcer(path):
			# Обработка конфига
			# Загружаем конфиг
			STagTime_dict = {}
			config = configparser.ConfigParser()
			if not os.path.exists(path):
				print('Не найден файл конфига. Пожалуйста восстановите его из копии.')
				wait_exit()	
			config.read(path)
			try:
			# Читаем конфиг
				self.Source_type  = config.get("Main", "Source_type")
				self.Source_input = config.get("Main", "Source_input")
				self.permission_score  = config.get("Main", "permission_score")
				self.appid = config.get("Main", "appid")
				self.GroupID = config.get("Main", "GroupID")
				self.save_token = config.get("Main", "save_token")
				self.conflict_time_act = config.get("Main", "conflict_time_act")
				self.absence_spost_act = config.get("Main", "absence_spost_act")
				self.time_type = config.get("Main", "time_type")
				self.log_level = config.get("Main", "log_level")
				self.default_tag = '#' + config.get("Post", "default_tag")
				self.autor_marker = config.get("Post", "autor_marker")
				self.mute_notifications = config.get("Post", "mute_notifications")
				
			except configparser.NoOptionError:
				print(sys.exc_info()[1])
				print("Пожалуйста исправьте эту опцию или восстановите конфиг из копии")
				#, rename or delete config.")
				wait_exit()

			n = 1
			while True:
				try:
					self.Time_dict.setdefault(datetime.datetime.strptime(config.get("Time", "Time"+str(n)), "%H-%M").time(), ['usual'])
					n += 1
				except configparser.NoOptionError:
					break
				except ValueError:
					print("В Config.ini в секии [Time] значение = Time"+str(n)+" имеет неверный формат. Пример формата 10-00.")
					wait_exit()
			
			n = 1
			while True:
				try:
					self.ExcepTag.append("#" + config.get("ExcepTag", "etag"+str(n)))
					n += 1
				except configparser.NoOptionError:
					break
			
			n = 1
			while True:
				try:
					self.STag_list.append(config.get("STag", "stag"+str(n)))
					n += 1
				except configparser.NoOptionError:
					break
					
			for i in range(len(self.STag_list)):
				try:
					STagTime_dict.setdefault(self.STag_list[i], datetime.datetime.strptime(config.get("STagTime", self.STag_list[i]), "%H-%M").time())
					n += 1
				except configparser.NoOptionError:
					print ('Специальный тег', self.STag_list[i], 'не найден в секции [STagTime]. Пожалуйста проверьте конфиг и исправьте это.')
					wait_exit()
				except ValueError:
					print("В Config.ini в секии [Time] значение = Time"+str(n)+" имеет неверный формат. Пример формата 10-00.")
					wait_exit()
				self.STimeTag_dict.setdefault(STagTime_dict[self.STag_list[i]],[])
				self.STimeTag_dict[STagTime_dict[self.STag_list[i]]].append('#'+self.STag_list[i])
				self.STag_list[i] = '#' + self.STag_list[i]
			
			#print (self.ExcepTag) # debug
			#print (self.STag_list) #debug
			#print (self.Time_dict) #debug
			#print (self.STimeTag_dict) #debug
			
		# Здесь всё вызывается
		config_parcer(self.path)
		#Парсер аргументов лучше после парсера конфигурации
		#Это даёт возможность добавить переменные из конфига в аргументы и они будут в приоритете
		arg_parser()
		self.ConfigLoad = True
		



	def checkconfig(self):
		# Проверка конфига
		def wait_exit():
			# Функция которая не позволит сразу закрыть консоль если запускать скрипт двойным кликом по файлу
			input("Нажмите Enter для выхода...")
			exit()

		
		def checkparametrs():
						
			if self.start_date != None and self.start_time != None:
				try:
					self.start_date = datetime.datetime.strptime(self.start_date, "%d.%m.%Y").date()
					self.start_time = datetime.datetime.strptime(self.start_time, "%H-%M").time()
					try: self.Time_dict[self.start_time]
					except KeyError:
						try: self.STimeTag_dict[self.start_time]
						except KeyError:
							print("Указанного времени начала нет в конфиге. Укажите другое время или добавте его в конфиг.")
							wait_exit()
					if datetime.datetime.combine(self.start_date, self.start_time) < datetime.datetime.now():
						print("Введённые дата и время являются прошедшими")
						wait_exit()
				except ValueError:
					print(sys.exc_info()[1])
					wait_exit()
			elif self.start_date != None and self.start_time == None:
				try:
					if self.start_date == 'today':
						self.start_date = datetime.datetime.now().date()
					else:
						self.start_date = datetime.datetime.strptime(self.start_date, "%d.%m.%Y").date()
					if self.start_date < datetime.date.today():
						print("Вы указали прошедшую дату")
						wait_exit()
					elif self.start_date == datetime.date.today():
						tmp_list = list(self.Time_dict.keys()) + list(self.STimeTag_dict.keys())
						tmp_list.sort()
						for time in tmp_list:
							if time > (datetime.datetime.now() + datetime.timedelta(minutes = 5)).time() :
								self.start_time = time
								print("Постинг начнётся с сегодня", time)
								break
						if self.start_time == None:
							self.start_time = tmp_list[0]
							self.start_date += datetime.timedelta(days = 1)
							print("Сегодня всё время для постинга уже прошедшее или до последнего времени менее 5 минут.")
							print("Постинг начнётся с завтра", self.start_time)
					else:
						tmp_list = list(self.Time_dict.keys()) + list(self.STimeTag_dict.keys())
						tmp_list.sort()
						self.start_time = tmp_list[0]
				except ValueError:
					print(sys.exc_info()[1])
					wait_exit()
			elif self.start_date == None and self.start_time != None:
				try:
					self.start_time = datetime.datetime.strptime(self.start_time, "%H-%M").time()
					try: self.Time_dict[self.start_time]
					except KeyError:
						try: self.STimeTag_dict[self.start_time]
						except KeyError:
							print("Указанного времени начала нет в конфиге. Укажите другое время или добавте его в конфиг.")
							wait_exit()
					self.start_date = datetime.datetime.now().date()
					if datetime.datetime.combine(self.start_date, self.start_time) < datetime.datetime.now():
						self.start_date = self.start_date + datetime.timedelta(days = 1)
						print("Указанное время сегодня уже прошло")
						print("Начало постинга будет с", datetime.datetime.combine(self.start_date, self.start_time))
				except ValueError:
					print(sys.exc_info()[1])
					wait_exit()	
			else:
				self.start_date = datetime.datetime.now().date() + datetime.timedelta(days = 1)
				tmp_list = list(self.Time_dict.keys()) + list(self.STimeTag_dict.keys())
				tmp_list.sort()
				self.start_time = tmp_list[0]
				
				
			if self.virtual != None:
				try:
					self.virtual = int(self.virtual)
					if self.virtual != 0 and self.virtual != 1:
						print('Аргумент virtual может быть 0 или 1.')
						wait_exit()
				except ValueError:
					print('Ошибка в аргументе virtual. virtual не число. virtual может быть "0" или "1".')
					wait_exit()
			
			if self.Source_type != 'link':
				print('Ошибка в Source_type. Source_type может быть только "link". Откройте Config.ini и исправьте это.')
				wait_exit()

			if self.Source_input != 'paste':
				print('Ошибка в Source_input. Source_input может быть только "paste". Откройте Config.ini и исправьте это.')
				wait_exit()
				
			score_split = self.permission_score.split('+')
			self.permission_score = 0
			try:
				for n in score_split:
					self.permission_score += int(n)
			except ValueError:
				print("Ошибка в permission_score. Ошибка в scope", n+". Откройте Config.ini и исправьте.")

			try:
				self.appid = int(self.appid)
				if self.appid < 0:
					print('Ошибка в appid. appid не может быть отрицательным числом. Откройте Config.ini и исправьте это.')
					wait_exit()
			except ValueError:
				print('Ошибка в appid. appid не число. Откройте Config.ini и исправьте это.')
				wait_exit()

			try:
				self.GroupID = abs(int(self.GroupID))
			except ValueError:
				print('Ошибка в GroupID. GroupID не число. Откройте Config.ini и исправьте это.')
				wait_exit()

			try:
				self.save_token = int(self.save_token)
				if self.save_token != 0 and self.save_token != 1:
					print('Ошибка в save_token. save_token может быть "0" или "1". Откройте Config.ini и исправьте это.')
					wait_exit()
			except ValueError:
				print('Ошибка в save_token. save_token не число. save_token может быть "0" или "1". Откройте Config.ini и исправьте это.')
				wait_exit()
			
			if self.conflict_time_act != 'nexttime' and self.conflict_time_act != 'stop':
				print('Ошибка в conflict_time_act. conflict_time_act может быть "nexttime" или "stop". Откройте Config.ini и исправьте это.')
				wait_exit()
				
			if self.absence_spost_act != 'usualpost' and self.absence_spost_act != 'stop' and self.absence_spost_act != 'skip':
				print('Ошибка в absence_spost_act. absence_spost_act может быть "usualpost" или "stop". Откройте Config.ini и исправьте это.')
				wait_exit()
				
			if self.time_type != 'fixed':
				print('Ошибка в time_type. time_type сожет быть только "fixed". Откройте Config.ini и исправьте это.')
				wait_exit()
				
			try:
				self.log_level = int(self.log_level)
				if self.log_level != 0 and self.log_level != 1 and self.log_level != 2:
					print('Ошибка в log_level. log_level может быть "0", "1" или "2". Откройте Config.ini и исправьте это.')
					wait_exit()
			except ValueError:
				print('Ошибка в log_level. log_level не число. log_level может быть "0", "1" или "2". Откройте Config.ini и исправьте это.')
				wait_exit()
			
			try:
				self.autor_marker = int(self.autor_marker)
				if self.autor_marker != 0 and self.autor_marker != 1:
					print('Ошибка в autor_marker. autor_marker может быть "0" или "1". Откройте Config.ini и исправьте это.')
					wait_exit()
			except ValueError:
				print('Ошибка в autor_marker. autor_marker не число. autor_marker может быть "0" или "1". Откройте Config.ini и исправьте это.')
				wait_exit()	
				
			try:
				self.mute_notifications = int(self.mute_notifications)
				if self.mute_notifications != 0 and self.mute_notifications != 1:
					print('Ошибка в mute_notifications. mute_notifications может быть "0" или "1". Откройте Config.ini и исправьте это.')
					wait_exit()
			except ValueError:
				print('Ошибка в в mute_notifications. mute_notifications не число. mute_notifications может быть "0" или "1". Откройте Config.ini и исправьте это.')
				wait_exit()
		
		if self.ConfigLoad == True:
			checkparametrs()
			self.ConfigCheck = True
		else:
			print("Ошибка последовательности инициализации. Config не загружен. Как это могло произойти?")
			wait_exit()

	def initscript(self):
		# Работа с токеном и получение материалов для постинга
		
		path = 'Token.ini'
	
		def wait_exit():
			# Функция которая не позволит сразу закрыть консоль если запускать скрипт двойным кликом по файлу
			input("Нажмите Enter для выхода...")
			exit()

		
		#Проверка токена и достпа к группе путём получения отложенных постов
		#Если токен неверный вернётся 5
		#Если нет доступа к отложенным записям, а значит не редактор и нельзя создать отложенные записи вернётся 15
		def check_token(token, GroupID): 
		# Проверяем токен
			error = False
			if token != '' :
				url = 'https://api.vk.com/method/wall.get?owner_id=-' + str(GroupID) + '&count=1&offset=&offset=0&extended=0&filter=postponed&v=5.103&access_token=' + token				
				response = requests.post(url)
				try:	#Обработка Json_Error
					error = response.json()["error"]
					if error["error_code"] == 5:
						print("Авторизация неудачна: access_token не верен")	
						error = True
						return error
					elif error["error_code"] == 15:
						print("Нет доступа к отложенным записям группы")
						print("Скорее всего Вы в ней не редактор")
						print("Проверье наличие прав в группе или GroupID в Config.ini")
						wait_exit()
					else:
						print()
						print("Oops. Незарегестрированная ошибка")
						print("Функция vk_auth: проверка токена с помощью wall.get")
						print("Проверка получением поста из отложенных записей группы.")
						print(error["error_code"])
						print(error["error_msg"])
						print("Больше информации по ошибке на https://vk.com/dev/errors")
						wait_exit()
				except KeyError:
					return error
			else:
				error = True
				return error

		def vk_auth(appid, GroupID, permission_score):
		# Получаем токен и проверяем его
			while True:
				url = "https://oauth.vk.com/authorize?client_id="+str(appid)+"&scope="+str(permission_score)+"&response_type=token"
				print()
				print("Откройте эту ссылку:\n\n\t{}\n".format(url))
				raw_url = input("Предоставьте доступ и вставьте ссыку из адресной строки сюда: ")
				res = re.search("access_token=([0-9A-Fa-f]+)", raw_url, re.I)
				if res is not None:
					url = 'https://api.vk.com/method/wall.get?owner_id=-' + str(GroupID) + '&count=1&offset=&offset=0&extended=0&filter=postponed&v=5.103&access_token=' + res.groups()[0]
					response = requests.post(url)
					try:	#Обработка Json_Error
						error = response.json()["error"]
						if error["error_code"] == 5:
							print("Авторизация неудачна: access_token не верен")
						elif error["error_code"] == 15:
							print("Нет доступа к отложенным записям группы")
							print("Скорее всего Вы в ней не редактор")
							print("Проверье наличие прав в группе или GroupID в Config.ini")
							wait_exit()
						else:
							print()
							print("Oops. Незарегестрированная ошибка")
							print("Функция vk_auth: проверка токена с помощью wall.get")
							print("Проверка получением поста из отложенных записей группы.")
							print(error["error_code"])
							print(error["error_msg"])
							print("Больше информации по ошибке на https://vk.com/dev/errors")
							wait_exit()
					except KeyError:
						return res.groups()[0]
				else:
					print("access_token не найден")
					
		
		def erase_token(config, path):
			token = ''
			config.set("Main", "token", token)
			with open(path, "w") as config_file:
				config.write(config_file)
			print("Существующий сохранённый токен был удалён.")
					
		def write_token(token, config, path):
			config.set("Main", "token", token)
			with open(path, "w") as config_file:
				config.write(config_file)

		def read_link(Source_input):
		# Получаем ссылки
			if Source_input == "paste":
				input_links = []
				a = ''
				print('Ввод ссылок из ВК на материалы для постов.')
				print('Напишите "end" для окончания ввода.')
				while a != 'end':
					a = input()
					if len(a) > 0:
						input_links.append(a) 
				input_links.remove("end")
				return input_links
		
		if self.ConfigCheck == True:
			config = configparser.ConfigParser()
			if not os.path.exists(path):
				print('Не найден файл Token.ini. Пожалуйста восстановите его из копии.')
				print('Пожалуйста создайте его в папке со скриптом и напишите в нём:')
				print('[Main]')
				print('token = ')
				wait_exit()	
				return Error, config
			config.read(path)
			self.token = config.get("Main", "token")

			if self.save_token == 0:
				if self.token != '':
					erase_token(config, path)
				self.token = vk_auth(self.appid, self.GroupID, self.permission_score)
			else:
				error_token = check_token(self.token, self.GroupID)
				if error_token == True:
					erase_token(config, path)
					self.token = vk_auth(self.appid, self.GroupID, self.permission_score)
					write_token(self.token, config, path)
			self.link_list = read_link(self.Source_input)
		else:
			print("Ошибка последовательности инициализации. Config не проверен. Как могло это произойти?")
			wait_exit()
			
		
	def PrintConfig(self):
		# Отладочная функция
		print("---Start config print---")
		print(self.Source_type, type(self.Source_type))
		print(self.Source_input, type(self.Source_input))
		print(self.appid, type(self.appid))
		print(self.GroupID, type(self.GroupID))
		print(self.save_token, type(self.save_token))
		print(self.default_tag, type(self.default_tag))
		print(self.autor_marker, type(self.autor_marker))
		print(self.mute_notifications, type(self.mute_notifications))
		print(self.conflict_time_act, type(self.conflict_time_act))
		print(self.absence_spost_act, type(self.absence_spost_act))
		print(self.time_type, type(self.time_type))
		print(self.Time_dict, type(self.Time_dict))
		print(self.ExcepTag, type(self.ExcepTag))
		print(self.STag_list, type(self.mute_notifications))
		print(self.token, type(self.token))
		print("---End config print---")
		
class log_kit:
	# Набор для логов
	def __init__(self, log_level, path='log.txt'):
		self.log = ['Старт записи лога\n']
		self.log_level = log_level
		self.path = path
		self.type_msg = ['[info]', '[info]', '[warning]']
	
	def add_text(self, type_id, text):
		if type_id >= self.log_level:
			self.log.append(datetime.datetime.now().strftime('%d.%m.%Y %H:%M') + self.type_msg[type_id] + ': ' + text + '\n')
	
	def write_to_file(self):
		if os.path.exists(self.path):
			file = open(self.path, 'a')
			file.write('\n')
			for i in self.log:
				file.write(i)
			file.close()
			print('Лог записан')
		else:
			file = open(self.path, 'w')
			for i in self.log:
				file.write(i)
			file.close()
			print('Лог записан')