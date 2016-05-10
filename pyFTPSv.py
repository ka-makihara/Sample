# -*- coding: utf8 -*-
import pyftpdlib.authorizers
import pyftpdlib.handlers
import pyftpdlib.servers

# 認証ユーザーを作る
authorizer = pyftpdlib.authorizers.DummyAuthorizer()
authorizer.add_user('mssys', 'music', 'F:\\FTP_ROOT\\BOOT', perm='elradfmw')

# 個々の接続を管理するハンドラーを作る
handler = pyftpdlib.handlers.FTPHandler
handler.authorizer = authorizer

# FTPサーバーを立ち上げる
server = pyftpdlib.servers.FTPServer(("172.17.120.6", 21), handler)
server.serve_forever()
