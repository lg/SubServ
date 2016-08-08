# - set default editor - EDITOR, VISUAL, or HOMEBREW_EDITOR to your preferred text editor.
# - pylint

from SubServ.uritools import uricompose

import socket
import sublime, sublime_plugin
from threading import Thread
from http.server import HTTPServer, SimpleHTTPRequestHandler

class SubServ():
  def __init__(self):
    self.httpd = None

    settings = sublime.load_settings('SubServ.sublime-settings')
    self.port = settings.get("port", 8080)
    self.ipv6 = settings.get("ipv6", False)
    self.interface = settings.get("interface", "127.0.0.1")

  def start_command(self):
    if self.httpd is not None:
      return

    # Using serve_forever() is blocking, as such offer it on a new thread
    def threaded_start():
      # Hey, it's the future, get with it
      class HTTPServerWithIPv6(HTTPServer):
        if self.ipv6: address_family = socket.AF_INET6

      self.httpd = HTTPServerWithIPv6((self.interface, self.port), SimpleHTTPRequestHandler)
      print("SubServ HTTP server ready on %s" % (uricompose(scheme="http", host=self.interface, port=self.port)))
      self.httpd.serve_forever()
      print("SubServ HTTP server stopped")

    Thread(target=threaded_start).start()

    self.httpd = None

  def stop_command(self):
    if self.httpd is None:
      return

    # Using shutdown() can sometimes be slow, doing it on a thread is faster
    def threaded_stop():
      self.httpd.shutdown()
      self.httpd.server_close()

    Thread(target=threaded_stop).start()

class StartCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    global subserv
    subserv.start_command()

class StopCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    global subserv
    subserv.stop_command()

def plugin_loaded():
  global subserv
  subserv = SubServ()

def plugin_unloaded():
  global subserv
  subserv.stop_command()
