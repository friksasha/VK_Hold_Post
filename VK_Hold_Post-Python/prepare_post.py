# -*- coding: utf-8 -*-
import re
import datetime
import requests
from time import sleep
sheep = sleep

class post_data:
	attachments = ''
	mtag = ''
	tags = ''
	default_tag = ''
	translate = ''
	post_unixtime_str = ''
	post_text = ''
	
	def __init__(self, attachment, mtag, tags, default_tag = ''):
		self.attachments = attachment
		self.mtag = mtag
		self.tags = tags
		self.default_tag = default_tag
	
# %0A перевод строки
# %23 #
# %40 @

def wait_exit():
	# Функция которая не позволит сразу закрыть консоль если запускать скрипт двойным кликом по файлу
	input("Нажмите Enter для выхода...")
	exit()

def separate_link(link_list, default_tag, ExcepTag):
	# Отделение ссылок от тега по проблелам и вытаскивание из ссыки необходимой информации
	# Поддерживает один хештег после ссылки
	post_list = []
	for link in link_list:		
		need_default_tag = False
		mtag = ''
		tags = ''
		link = link.strip()
		if link.find(" ") > -1 and link[link.find(" ")+1] != ' ':
			print("После ссылки идёт 1 пробел, а ожидалось 2")
			wait_exit()
		split_link = link.split("  ")
		try:
			attachment = re.search("photo-?\d+_\d+|video-?\d+_\d+|album-?\d+_\d+|doc-?\d+_\d+", link)[0]
			split_link.pop(0)
		except TypeError:
			print('Ошибка в ссылке. Поддерживаются только ссылки из ВК с "photo", "video", "album" и "doc".')
			print(split_link[0])
			wait_exit()
		if len(split_link) == 1:
			if len(split_link[0]) > 0:
				split_link[0] = split_link[0].rstrip()
				split_tag = split_link[0].split(" ")
				if len(split_tag[0]) > 0:
					for tag in split_tag: #проверяем что хештеги начинаются с #
						if tag[0] != '#':
							print('Ошибка в хештеге', tag)
							print('Хештег должен начинатся с #')
							wait_exit()
					for tag in split_tag: #если среди хештегов есть исключённый, то делаем пометку, что стандартный тег не нужен
						if tag in ExcepTag:
							need_default_tag = False
							break
						else:
							need_default_tag = True
					mtag = split_tag[0]
					split_tag.pop(0)
					for tag in split_tag:
						tags = tags + tag + '\n'
					if need_default_tag:
						post_list.append(post_data(attachment, mtag + '\n', tags, default_tag + '\n'))
					else:
						post_list.append(post_data(attachment, mtag + '\n', tags))
				else:
					print('после двойного пробела идёт 3й пробел, а ожидался уже хештег')
					wait_exit()

			else:
				post_list.append(post_data(attachment, mtag, tags, default_tag))
		elif len(split_link) > 1:
			print("Обнаружены лишние пробелы межу ссылкой и хештегами или между хештегами.")
			print("Ссылки должны записываться в формате <Ссылка><2 пробела><#tag1><пробел><#tag2><пробел><...>.")
			wait_exit()
		elif len(split_link) == 0:
			post_list.append(post_data(attachment, mtag, tags, default_tag))
			
		
			
	return post_list

def get_postponed_times(groupid, token):
	# Получение списка отложенных постов и взятие их времени
	# Требуется для определения занято ли время при назначении времени посту
	# Обработка исключений не требуется. Ошибка отсутствия прав обрабатывается в init
	offset = 0
	postponed_times = []
	while True: 
		url = 'https://api.vk.com/method/wall.get?owner_id=-' + str(groupid) + '&count=100&offset=' + str(offset) + '&filter=postponed&v=5.103&access_token=' + token
		response = requests.post(url)
		response_json = response.json()['response']
		count = response_json['count']
		items = response_json['items']
		for item in items:
			postponed_times.append(item['date'])
		if len(postponed_times) == count:
			return postponed_times
		else:
			offset += 100
			sheep(0.5)

def preparing_post(post_list, postponed_times ,Time_dict, start_date, start_time, virtual, STag_list, STimeTag_dict, conflict_time_act, absence_spost_act, token, log):
	# Здесь происходит вся магия по подготовке постов к постингу

	def take_translate(post):
		# Получение перевода картинки
		photo = re.search("-\d+_\d+", post.attachments)[0]
		url = 'https://api.vk.com/method/photos.getById?photos=' + photo + '&extended=1&photo_sizes=0&v=5.103&access_token=' + token
		response = requests.post(url)
		# TODO try:
		# Исключение чтобы для видео не бралось описание
		response_translate = response.json()['response']
		translate_json = {}
		for i in response_translate:
			for k, v in i.items():
				translate_json[k] = v
		post.translate = '\n' + '\n' + translate_json['text'] + '\n' + '\n'
		sheep(0.5)
		return post
		
	#def print_tags(default_tag, mtag, tags):
	#	out_text

	out_post_list = []
	fTime_list = []
	fTime_dict = {}
	flag_no_post = False
	
	log.add_text(1, "Подготовка постов")
	fTime_list = list(Time_dict.keys()) + list(STimeTag_dict.keys())
	fTime_list.sort()
	for key in fTime_list:
		try:
			fTime_dict.setdefault(key, Time_dict[key])
		except KeyError:
			fTime_dict.setdefault(key, STimeTag_dict[key])
	for i in range(len(fTime_list)):
		if fTime_list[i] == start_time:
			time_id = i
			break
	
	#Пока в массиве post_list есть значения, то работаем
		#Берём время
			#Собираем датавремя и проверяем есть такое уже в запланированном
				#Если есть и указан параметр nexttime пишем об этом и переходим к следующему
				#Если есть и указан параметр stop пишем об этом и прекращаем работу
			#Если время помечено как обычное, то ставим туда обычный пост
				#Проверяем флаг отсутствия материалов для обычных постов в массиве
				#Берём будущий пост
				#Смотрим тег будущего поста, если он не входит в специальные, то изымаем из массива
				#Назначаем время, пишем об этом, добавляем в новый массив
				#Если поста не оказалось, то поднимаем флаг отсутствия обычных постов и пишем об отсутствии поста
			#Если время не помечено как обычное, то ставим туда пост согласно массиву тегов этого времени
				#Берём первый тег из массива
					#Берём будущий пост
					#Смотрим соответствиет ли тег будущего поста тегу массива
						#Если соответствиет то проверяем является ли это переводом
							#Если перевод - вытаскиваем перевод и добавляем к посту
						#Назначаем время, пишем об этом, добавляем в новый массив
				#Если cпец поста не оказалось и указан параметр usualpost, то ищем обычный пост на это время
					#Проверяем флаг отсутствия материалов для обычных постов в массиве
					#Берём будущий пост
					#Смотрим тег будущего поста, если он не входит в специальные, то изымаем из массива
					#Назначаем время, пишем об этом, добавляем в новый массив
					#Если поста не оказалось, то поднимаем флаг отсутствия обычных постов и пишем об отсутствии поста
				#Если cпец поста не оказалось и указан параметр skip, то пропускаем и пишем об этом
				#Если cпец поста не оказалось и указан параметр stop, то прекращаем работу и пишем об этом
		#Переходим к следующему времени пока не дойдём до конца
		
	while len(post_list) > 0:
		while time_id < len(fTime_list):
			ok = False
			post_datetime = datetime.datetime.combine(start_date, fTime_list[time_id])
			post_unixtime = int(post_datetime.timestamp())
			if post_unixtime not in postponed_times:
				if fTime_dict[fTime_list[time_id]][0] == 'usual': #работа с обычными постами
					if not flag_no_post:
						for i in range(len(post_list)):
							mtag = re.sub('\n', '', post_list[i].mtag)
							if mtag not in STag_list:
								post = post_list.pop(i)
								post.post_unixtime_str = str(post_unixtime)
								out_post_list.append(post)
								log.add_text(0, 'На время ' + post_datetime.strftime('%d.%m.%Y %H:%M') + ' обычный пост подготовлен')
								print('На время',post_datetime.strftime('%d.%m.%Y %H:%M'),'обычный пост подготовлен')
								log.add_text(0, "Теги поста: "+ re.sub('\n', ' ', (post.mtag + post.tags + post.default_tag)))
								print("Теги поста:", re.sub('\n', ' ', (post.mtag + post.tags + post.default_tag)))
								print()
								ok = True
								break
							if ok: break
					if not ok:
						flag_no_post = True
						log.add_text(2, 'На время ' + post_datetime.strftime('%d.%m.%Y %H:%M') + ' нет обычного поста.')
						print('На время',post_datetime.strftime('%d.%m.%Y %H:%M'),'нет обычного поста. Записано в лог.')
						#запись в лог что обычного поста по такому-то времени нет
				else: #работа с спец постами
					for tag in fTime_dict[fTime_list[time_id]]:
						for i in range(len(post_list)):
							mtag = re.sub('\n', '', post_list[i].mtag)
							if mtag == tag:
								post = post_list.pop(i)
								tag_lower = post.mtag.lower()
								if virtual != 1:
									if tag_lower.find('translate') >= 0 or tag_lower.find('перевод') >= 0:
										if post.attachments.find('photo') >= 0:
											post = take_translate(post)
								post.post_unixtime_str = str(post_unixtime)
								out_post_list.append(post)
								log.add_text(0, 'На время ' + post_datetime.strftime('%d.%m.%Y %H:%M') + ' Spost подготовлен')
								print('На время',post_datetime.strftime('%d.%m.%Y %H:%M'),'Spost подготовлен')
								log.add_text(0, "Теги поста: "+ re.sub('\n', ' ', (post.mtag + post.tags + post.default_tag)))
								print("Теги поста:", re.sub('\n', ' ', (post.mtag + post.tags + post.default_tag)))
								print()
								ok = True
								break
						if ok: break #А если не True, то работаем дальше
					if not ok:						
						#Код поиска класса с тегом не в STag_list и запись в лог о замене или отсутствии
						if absence_spost_act == 'usualpost':
							if not flag_no_post:
								for i in range(len(post_list)):
									mtag = re.sub('\n', '', post_list[i].mtag)
									if mtag not in STag_list:
										post = post_list.pop(i)
										post.post_unixtime_str = str(post_unixtime)
										out_post_list.append(post)
										log.add_text(2, 'На время ' + post_datetime.strftime('%d.%m.%Y %H:%M') + ' обычный пост заменил Spost.')
										print('На время',post_datetime.strftime('%d.%m.%Y %H:%M'),'обычный пост заменил Spost. Записано в лог.')
										log.add_text(0, "Теги поста: "+ re.sub('\n', ' ', (post.mtag + post.tags + post.default_tag)))
										print("Теги поста:", re.sub('\n', ' ', (post.mtag + post.tags + post.default_tag)))
										print()
										ok = True
										break
									if ok: 
										break
									else:
										flag_no_post = True
										log.add_text(2, 'На время ' + post_datetime.strftime('%d.%m.%Y %H:%M') + ' нет обычного поста для замены Spost.')
										print('На время', post_datetime.strftime('%d.%m.%Y %H:%M'), 'нет обычного поста для замены Spost. Записано в лог.')
							else:
								log.add_text(2, 'На время ' + post_datetime.strftime('%d.%m.%Y %H:%M') + ' нет обычного поста для замены Spost.')
								print('На время', post_datetime.strftime('%d.%m.%Y %H:%M'), 'нет обычного поста для замены Spost. Записано в лог.')
								log.add_text(0, "Теги поста: "+ re.sub('\n', ' ', (post.mtag + post.tags + post.default_tag)))
								print("Теги поста:", re.sub('\n', ' ', (post.mtag + post.tags + post.default_tag)))
						elif absence_spost_act == 'skip':
							log.add_text(2, 'Нету материалов для Spost на время ' + post_datetime.strftime('%d.%m.%Y %H:%M') + '. Время пропущено.')
							print('Нету материалов для Spost на время', post_datetime.strftime('%d.%m.%Y %H:%M') + '. Время пропущено. Записано в лог.')
						elif absence_spost_act == 'stop':
							print("Нету материалов для Spost на время", post_datetime.strftime('%d.%m.%Y %H:%M'))
							wait_exit()
			else:
				if conflict_time_act == 'nexttime':
					log.add_text(2, "Время " + post_datetime.strftime('%d.%m.%Y %H:%M')+ " уже занято.")
					print("Время",post_datetime.strftime('%d.%m.%Y %H:%M'),"уже занято. Записано в лог.")
					pass
				elif conflict_time_act == 'stop':
					print("Время",post_datetime.strftime('%d.%m.%Y %H:%M'),"уже занято")
					print("Пожалуйста удалите конфликтующий пост, используйте 'nexttime' в конфиге или аргумент --start_date -sd")
					wait_exit()
			time_id += 1
			if len(post_list) == 0: break
		start_date += datetime.timedelta(days = 1)	
		time_id = 0
	if virtual == 1:
		print('Скрипт был запущен со значением virtual 1. Постинг производится не будет.')
		log.write_to_file()
		wait_exit()
	return out_post_list


def posting(post_data, GroupID, autor_marker, mute_notifications, token, log):
	# Постинг переданного поста
	post_text = post_data.translate + post_data.default_tag + post_data.mtag + post_data.tags
	url = "https://api.vk.com/method/wall.post?owner_id=-" + str(GroupID) + "&from_group=1" + "&attachments=" + post_data.attachments + "&signed=" + str(autor_marker) + "&mute_notifications="+ str(mute_notifications) + "&publish_date=" + post_data.post_unixtime_str + "&v=5.103&access_token=" + token
	response = requests.post(url, data={'message': post_text})
	try:	#Обработка Json_Error 
		error = response.json()["error"]
		if error["error_code"] == 214: # Legacy код который никогда не исполнится т.к. это обрабатывается ранее
			print("method: wall.post")
			print("Время",datetime.datetime.fromtimestamp(int(post_data.post_unixtime_str)),"уже занято")
			print("Пожалуйста удалите конфликтующий пост, используйте 'nexttime' в конфиге или аргумент --start_date -sd")
			print("Access to adding post denied: a post is already scheduled for this time")
			wait_exit()
		elif error["error_code"] == 15: # Тоже не должно. Права проверяются раньше
			print("method: wall.post")
			print("Access denied: user should be group editor")
			wait_exit()
		else: #Другие ошибки которые не учёл. Надо расширить
			# TODO какой пост был последним и записать его в лог
			print()
			print("Oops. Незарегестрированная ошибка")
			print("method: wall.post")
			print(error["error_code"])
			print(error["error_msg"])
			print("More information on https://vk.com/dev/errors")
			log.write_to_file()
			wait_exit()
	except KeyError:
		log.add_text(0, "Пост на время " + datetime.datetime.fromtimestamp(int(post_data.post_unixtime_str)).strftime('%d.%m.%Y %H:%M') + " успешно создан")
		post_id = response.json()["response"]
		print("Отложенный пост создан")
		print("ID поста:", post_id["post_id"])
		print(datetime.datetime.fromtimestamp(int(post_data.post_unixtime_str)).strftime('%d.%m.%Y %H:%M'),'\n')

	
def init(cfg, log):	
	post_list = separate_link(cfg.link_list, cfg.default_tag, cfg.ExcepTag)
	postponed_times = get_postponed_times(cfg.GroupID, cfg.token)
	post_list = preparing_post(post_list, postponed_times, cfg.Time_dict, cfg.start_date, cfg.start_time, cfg.virtual, cfg.STag_list, cfg.STimeTag_dict, cfg.conflict_time_act, cfg.absence_spost_act, cfg.token, log)
	log.add_text(0, "Постинг")
	input("Проверьте корректность планируемого постинга и нажмите Ввод для продолжения")
	for i in range(len(post_list)):
		posting(post_list[i], cfg.GroupID, cfg.autor_marker, cfg.mute_notifications, cfg.token, log)
		sheep(1)
	log.write_to_file()
	#print_list(post_list)

###########################################################

def print_list(post_list):
	# Отладочная функция
	for i in range(len(post_list)):
		print("--------------")
		print(post_list[i].attachments)
		print(post_list[i].tag)
		print(post_list[i].post_unixtime_str)
		print(datetime.datetime.fromtimestamp(int(post_list[i].post_unixtime_str)).strftime('%d.%m.%Y %H:%M'))
