#!/home/eserg/dq.cube2.ru/env/bin/python3

import sys, os
INTERP = "/home/eserg/dq.cube2.ru/env/bin/python3"
#INTERP is present twice so that the new python interpreter 
#knows the actual executable path 
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

cwd = os.getcwd()
sys.path.append(cwd)
sys.path.append(cwd + '/dicquo')  #You must add your project here

sys.path.insert(0,cwd+'/env/bin')
sys.path.insert(0,cwd+'/env/lib/python3.8/site-packages')

os.environ['DJANGO_SETTINGS_MODULE'] = "dicquo.settings"
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()


##!/usr/bin/env python
#import sys, os
#cwd = os.getcwd()
#sys.path.append(cwd)
#sys.path.append(cwd + '/dicquo')

##Switch to new python
##if sys.version < "2.7.8": os.execl(cwd+"/env/bin/python", "python2.7", *sys.argv)

#sys.path.insert(0,cwd+'/env/bin')
#sys.path.insert(0,cwd+'/env/lib/python3.8/site-packages/django')
#sys.path.insert(0,cwd+'/env/lib/python3.8/site-packages')

#os.environ['DJANGO_SETTINGS_MODULE'] = "dicquo.settings"
#from django.core.wsgi import get_wsgi_application
#application = get_wsgi_application()
