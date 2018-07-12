from google.appengine.ext.webapp import template
from urllib import unquote

register = template.create_template_register()

@register.filter
def unquote_raw(value):
	v = value.replace('=', '%')
	return unquote(v)
	
register.filter('unquote_raw', unquote_raw) 