#!/usr/bin/env python
'''
Created on Jan 22, 2016

@author: mgering
'''
import StringIO
import cgi
import sys
import yaml
from flask import Flask, render_template, redirect, url_for, flash, request, Markup, jsonify
from drupalsites import Site, sites, set_verbose
from contextlib import contextmanager

app = Flask(__name__)
app.secret_key = "It's my secret"


@contextmanager
def stdout_redirector(stream):
    old_stdout = sys.stdout
    sys.stdout = stream
    try:
        yield
    finally:
        sys.stdout = old_stdout

@app.route("/site-op")
def site_op():
  site_name = request.args.get('site')
  op_name = request.args.get('op')
  verbose_opt = request.args.get('verbose') == 'true'
  dry_run_opt = request.args.get('dry_run') == 'true'
  op_result = perform_site_op(site_name, op_name, verbose_opt, dry_run_opt)
  return jsonify(op_result)

@app.route("/manage")
def manage():
  global sites
  return render_template('manage.html', ops_dict=Site.operations, sites_dict=sites)

def perform_site_op(site_name, op_name, verbose_opt, dry_run_opt):
  msgs = []
  site = sites[site_name]
  operation = site.get_operation(op_name)
  set_verbose(verbose_opt)
  if dry_run_opt:
    msgs.append("Dry run for operation {} on site {}".format(operation.name, site.name))
  else:
    std_str = StringIO.StringIO()
    with stdout_redirector(std_str):
      operation.do_cmd()
      msg = cgi.escape(std_str.getvalue()).replace("\n", "<br>")
      msg = Markup("<code>"+msg+"</code>")
      msgs.append(msg)
      std_str.close()
  return {'msgs': msgs}

if __name__ == '__main__':
  try:
    config_file = file('config.yaml', 'r')
    config = yaml.load(config_file)
    if config['FLASK']['DEBUG']:
      app.debug = True
      use_debugger = True
      try:
        use_debugger = not(config['FLASK']['DEBUG_WITH_ECLIPSE'])
        app.use_debugger = use_debugger
        app.use_reloader = use_debugger
      except:
        pass
  except:
    print("Problem openning config.yaml")
  print(app)
  app.run(host='0.0.0.0')