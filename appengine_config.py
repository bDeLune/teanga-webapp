from gaesessions import SessionMiddleware 

def webapp_add_wsgi_middleware(app): 
	app = SessionMiddleware(app, cookie_key='\x9d\x90\x18\x13C\xaaw5\x07\xb0N]/\xcf\x93r\xeb\xb2\xc4[p\x02\xc1\x9f\x8f1\xac\x8e\x9b\xed\x95\t|\xc4\xee\xc4\xc3\xce\xb2\x03\xdd`l\xf2P\xbd\xc1s\xf8H\xb9R\xc9IA_\x00=\xe7\n\x81\x8e\x9d\xaf') 
	return app