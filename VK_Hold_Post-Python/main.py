# -*- coding: utf-8 -*-

# Script made in the Abyss
# Этот скрипт создан при поддержке Бездны
# Написан на 6м уровне бездны и поднят наверх
# В результате поднятия код полностью утратил читаемый облик и способность рефакторинга, 
# хотя сохранила способность выполняться и модификации.
# В нём смешалось всё
# Класс с функциями, класс без функций, неиспользуемый код, рекурсия в одном месте, баги, Exceptions 
# и куча закомментированного кода, отсутствие комментариев
# Код фактически превратился в Мити / Mitty
# https://desu.shikimori.one/system/characters/original/153888.jpg?1578566523

import init
import prepare_post

def wait_exit():
	input("Нажмите Enter для выхода...")
	exit()

def main():	
	Config = init.VKConfig()
	Config.loadconfig()
	Config.checkconfig()
	Config.initscript()
	log = init.log_kit(Config.log_level)
	#Config.PrintConfig()
	#print(Config.default_tag)
	#print(Config.link_list)
	#print(Config.Time_dict)
	#print(Config.STag_list)
	#print(Config.STagTime_list)
	prepare_post.init(Config, log)
	wait_exit()
	#print(post_list)
	
if __name__ == '__main__':
	main()