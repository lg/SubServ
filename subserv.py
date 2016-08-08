# - set default editor - EDITOR, VISUAL, or HOMEBREW_EDITOR to your preferred text editor.
# - pylint

import socket
import sublime, sublime_plugin
import os
from threading import Thread
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urljoin

class SubServ():
  def __init__(self):
    self.httpd = None
    self.httpd_path = None

    settings = sublime.load_settings('SubServ.sublime-settings')
    self.port = settings.get("port", 8080)
    self.interface = settings.get("interface", "127.0.0.1")
    if len(self.interface) == 0:
      self.interface = "0.0.0.0"

  def _log(self, text):
    print(text)
    sublime.active_window().status_message(text)

  def update_status_bar(self, cur_view=sublime.active_window().active_view()):
    if self.httpd is None or self.httpd_path is None:
      if len(cur_view.get_status("subserv")) > 0:
        cur_view.erase_status("subserv")
      return

    filename = cur_view.file_name()
    if filename is None or filename.startswith(self.httpd_path) == False:
      return

    relative = filename[len(self.httpd_path):]
    server_path = urljoin("http://%s:%d/" % (self.interface, self.port), relative)
    cur_view.set_status("subserv", "SubServ %s" % (server_path))

  def _start_server(self, root_dir):
    # Using serve_forever() is blocking, as such offer it on a new thread
    def threaded_start():
      self.httpd_path = root_dir
      os.chdir(root_dir)

      self.httpd = HTTPServer((self.interface, self.port), SimpleHTTPRequestHandler)
      print("SubServ HTTP server ready on %s:%d with root %s" % (self.interface, self.port, self.httpd_path))
      sublime.active_window().status_message("SubServ HTTP server ready")
      self.update_status_bar()

      self.httpd.serve_forever()
      print("SubServ HTTP server stopped")
      sublime.active_window().status_message("SubServ HTTP server stopped")

    Thread(target=threaded_start).start()

  def start_command(self):
    if self.httpd is not None:
      return

    # Use the project folder by default and if there's no project use the current file's path instead
    folders = sublime.active_window().folders()
    if len(folders) > 0:
      default_path = folders[0]
    else:
      variables = sublime.active_window().extract_variables()
      default_path = variables['file_path'] if 'file_path' in variables else '~'

    sublime.active_window().show_input_panel("Start SubServ HTTP server in path:", default_path, self._start_server, None, None)

  def stop_command(self):
    if self.httpd is None:
      return

    # Using shutdown() can sometimes be slow, doing it on a thread is faster
    def threaded_stop():
      self.httpd.shutdown()
      self.httpd.server_close()
      self.httpd = None
      self.httpd_path = None
      self.update_status_bar()

    Thread(target=threaded_stop).start()

class SubServListener(sublime_plugin.EventListener):
  def on_activated_async(self, view):
    global subserv
    subserv.update_status_bar(view)

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
