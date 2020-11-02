# -*- coding: utf-8 -*-
"""
В этот файл вынесены все секретные настройки, чтобы не светить их в settings.py
Например, при размещении в публичный репоизториях.
"""

# Хосты на которых может работать приложение
MY_HOST_HOME = 'fatal1ty'
MY_HOST_WORK = 'SEremin2'

# Ключ Django
MY_SECRET_KEY = '&c)g5so_o6$q=fw#%&lu__&4$*^=ue@r=&4n-y+b^q8$xz-*vx'

MY_EMAIL = 'erjemin@gmail.com'
MY_EMAIL_HOST_USER = 'info@oknardia.ru'    # login if requared or ''
MY_EMAIL_HOST_PASSWORD = 'IAdra67gonO'     # password

MY_TOUCH_RELOAD_PROD = '/home/eserg/dq.cube2.ru/tmp/restart.txt'
MY_TOUCH_RELOAD_DEV = 'M:/cloud-mail.ru/PRJ/PRJ DicQuo/logs/favicon_prj_reload.log'

MY_MEDIA_ROOT_PROD = '/home/eserg/dq.cube2.ru/public/media'
MY_MEDIA_ROOT_DEV = 'M:/cloud-mail.ru/PRJ/PRJ DicQuo/public/media'

MY_STATIC_ROOT_PROD = '/home/eserg/dq.cube2.ru/public/static/'
MY_STATIC_ROOT_DEV = 'M:/cloud-mail.ru/PRJ/PRJ DicQuo/public/static/'

