#!/usr/bin/env python
'''
Created on Jan 22, 2016

@author: mgering
'''
import StringIO
import cgi
import sys
import yaml
from flask import Flask, render_template, redirect, url_for, flash, request, Markup
from drupalsites import init_sites, sites, Operations, set_verbose
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

@app.route("/sites")
def get_sites():
  global sites
  sites_dict = sites
  return render_template('sites.html', sites_dict=sites_dict)

@app.route("/operations")
def get_operations():
  global Operations
  ops_dict = Operations
  return render_template('operations.html', ops_dict=ops_dict)

@app.route("/manage")
def manage():
  global sites, Operations
  return render_template('manage.html', ops_dict=Operations, sites_dict=sites)

@app.route("/perform", methods=["POST"])  
def perform():
  errors = 0
  if request.form.has_key('operation'):
    op_option = request.form['operation']
  else:
    flash("Missing operation")
    errors += 1
  
  if errors == 0:
    verbose = request.form.has_key('verbose')
    set_verbose(verbose)
    sites_to_do = request.form.getlist("site")
    for site_name in sites_to_do:
      site = sites[site_name]
      operation_cls = Operations[op_option]
      operation = operation_cls(site)
      if request.form.has_key('dry-run'):
        flash("Dry run for operation {} on site {}".format(operation.name, site.name))
      else:
        std_str = StringIO.StringIO()
        with stdout_redirector(std_str):
          operation.do_cmd()
          msg = cgi.escape(std_str.getvalue()).replace("\n", "<br>")
          msg = Markup("<code>"+msg+"</code>")
          flash(msg)
          std_str.close()

    flash("Done")
  else:
    flash("No operations performed")
  return redirect(url_for('manage'))

if __name__ == '__main__':
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
  print app
  app.run(host='0.0.0.0')