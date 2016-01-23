#!/usr/bin/env python
# Author: Mike Gering

import abc
import argparse
import os.path
import shlex
import subprocess
import sys
import textwrap

def set_verbose(val):
  global verbose
  verbose = val

def init_sites():
  sites = {}
  sites['hillsborough'] = Site('hillsborough', 'hb', '/var/www/dev.ci.hillsborough.nc.us/htdocs', bam_files='sites/default/files/backup_migrate')
  sites['gattishouse'] = Site('gattishouse', 'gh', '/var/www/dev.gattishouse.com/htdocs')
  sites['lnba'] = Site('lnba', 'lnba', '/var/www/dev.lnba.net/htdocs')
  sites['stem'] = Site('stem', 'stem', '/var/www/dev.stemnc.org/htdocs')
  sites['unrba'] = Site('unrba', 'unrba', '/var/www/dev.unrba.org/htdocs')
  sites['hcrt'] = Site('hcrt', 'hcrt', '/var/www/dev.w3.harvardtriangle.org/htdocs', vps_dir='w3.harvardtriangle.org')
  sites['ypdrba'] = Site('ypdrba', 'ypdrba', '/var/www/dev.ypdrba.org/htdocs')
  return sites

def trace_op(func):
  def func_wrapper(self):
    site_str = ''
    if hasattr(self, 'site'):
      site_str = "{}: ".format(self.site.name)
    print "-----> {}Starting {}".format(site_str, self.name)
    func(self)
    print "<----- {}Ending {}".format(site_str, self.name)
  return func_wrapper

class Operation:
  name = None
  
  @abc.abstractmethod
  def do_cmd(self):
    """Perform a command"""
    return
  
  def sys_cmd(self, cmd, check_error = True):
    global verbose
    if verbose:
      print cmd
    os.chdir(self.site.doc_root)
    args = shlex.split(cmd)
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (self.stdoutdata, self.stderrdata) = p.communicate()
    self.returncode = p.returncode
    if self.returncode != 0 and check_error:
      print "***ERROR*** for '{0}'".format(cmd)
      print self.stderrdata,
    else:
      print self.stdoutdata,
    
  def ssh_cmd(self, cmd, check_error = True, tty = False):
    if tty:
      args = ['ssh', '-t', self.site.ssh_alias, cmd]
    else:
      args = ['ssh', self.site.ssh_alias, cmd]
    global verbose
    if verbose:
      cmd = " ".join(args)
      print cmd
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (self.stdoutdata, self.stderrdata) = p.communicate()
    self.returncode = p.returncode
    if self.returncode != 0 and check_error:
      print "***ERROR*** for '{0}'".format(cmd)
      print self.stderrdata,
    else:
      print self.stdoutdata,

class RemoteClearCache(Operation):
  name = 'remote_cc'
  desc = 'Remote clear cache'
  
  def __init__(self, site):
    self.site = site

  @trace_op
  def do_cmd(self):
    cmd = 'cd {} && drush cc all'.format(self.site.vps_dir)
    self.ssh_cmd(cmd, tty=True)

class Remote2LocalRestore(Operation):
  name = 'remote_to_local_restore'
  desc = 'Snapshot remote, sync backupfiles to local, restore snapshot on local'

  def __init__(self, site):
    self.site = site

  @trace_op
  def do_cmd(self):
    RemoteBackup(self.site).do_cmd()
    Remote2LocalBamFiles(self.site).do_cmd()
    LocalRestore(self.site).do_cmd()

class RemoteBackup(Operation):
  name = 'remote_backup'
  desc = 'Snapshot remote (snapshot.mysql.gz in manual directory)'
  
  def __init__(self, site):
    self.site = site

  @trace_op
  def do_cmd(self):
    cmd = 'cd {} && [ -e {}/manual/snapshot.mysql.gz ] && rm {}/manual/snapshot.mysql.gz'.format(self.site.vps_dir, self.site.bam_files, self.site.bam_files)
    self.ssh_cmd(cmd)
    cmd = 'cd {} && drush bam-backup db manual snapshot'.format(self.site.vps_dir)
    self.ssh_cmd(cmd, tty=True)

class Remote2LocalBamFiles(Operation):
  name = 'remote_to_local_bam_files'
  desc = 'Sync remote backup files to local system'
  
  def __init__(self, site):
    self.site = site

  @trace_op
  def do_cmd(self):
    cmd = "rsync -r {}:{}/{}/ {}/{}/".format(self.site.ssh_alias, 
      self.site.vps_dir, self.site.bam_files, self.site.doc_root, self.site.bam_files)
    self.sys_cmd(cmd)

class Remote2LocalDefaultFiles(Operation):
  name = 'remote_to_local_rsync'
  desc = 'Sync remote default/files to local system'
  
  def __init__(self, site):
    self.site = site

  @trace_op
  def do_cmd(self):
    cmd = "rsync -avh --delete --exclude=css/ --exclude=js/ --exclude=ctool/ {}:{}/sites/default/files/ {}/sites/default/files/".format(self.site.ssh_alias, 
      self.site.vps_dir, self.site.doc_root)
    self.sys_cmd(cmd)

class LocalRestore(Operation):
  name = 'local_restore'
  desc = 'Restore db from snapshot in manual backup directory'
  
  def __init__(self, site):
    self.site = site

  @trace_op
  def do_cmd(self):
    cmd = 'drush --root={} --yes bam-restore db manual snapshot.mysql.gz'.format(self.site.doc_root)
    self.sys_cmd(cmd)

class RemotePull(Operation):
  name = 'remote_pull'
  desc = 'Do git pull on remote system'
  
  def __init__(self, site):
    self.site = site

  @trace_op
  def do_cmd(self):
    self.ssh_cmd('cd {} && git pull'.format(self.site.vps_dir))

class RemoteUpdates(Operation):
  name = 'remote_updates'
  desc = 'Backup remote, remote git pull, remote drush updatedb'
  
  def __init__(self, site):
    self.site = site

  @trace_op
  def do_cmd(self):
    RemoteBackup(self.site).do_cmd()
    RemotePull(self.site).do_cmd()
    RemoteUpdateDB(self.site).do_cmd()

class RemoteUpdateDB(Operation):
  name = 'remote_update_db'
  desc = 'Remote drush updatedb'
  
  def __init__(self, site):
    self.site = site

  @trace_op
  def do_cmd(self):
    self.ssh_cmd("cd {} && drush --yes updatedb".format(self.site.vps_dir))

class LocalUpdates(Operation):
  name = 'local_updates'
  desc = 'Pull from master, update modules, commit and push to master'
  
  def __init__(self, site):
    self.site = site

  @trace_op
  def do_cmd(self):
    self.sys_cmd('git pull'.format(self.site.doc_root))
    self.sys_cmd('drush --root={} --yes up'.format(self.site.doc_root), check_error=False)
    self.sys_cmd('git checkout .gitignore'.format(self.site.doc_root))
    self.sys_cmd('git add *'.format(self.site.doc_root))
    self.sys_cmd('git reset -- sites/default/settings.php'.format(self.site.doc_root))
    self.sys_cmd('git commit -a -m "updates"'.format(self.site.doc_root), check_error=False)
    self.sys_cmd('git push'.format(self.site.doc_root))
  
class LocalUpdateStatus(Operation):
  name = 'local_update_status'
  desc = 'Pull from master, check for updates'
  
  def __init__(self, site):
    self.site = site

  @trace_op
  def do_cmd(self):
    self.sys_cmd('git pull'.format(self.site.doc_root))
    self.sys_cmd('drush --root={} --format=list ups'.format(self.site.doc_root), check_error=False)
  
class Site:
  def __init__(self, name, ssh_alias, doc_root, vps_dir='www', bam_files='sites/default/files/private/backup_migrate'):
    self.name = name
    self.ssh_alias = ssh_alias
    self.doc_root = doc_root
    self.vps_dir = vps_dir
    self.bam_files = bam_files
    if not os.path.exists(doc_root):
      raise Exception('Site '+name+' docroot '+doc_root+' does not exist')

OperationClasses = [RemoteClearCache,
  Remote2LocalRestore,
  RemoteBackup,
  Remote2LocalBamFiles,
  Remote2LocalDefaultFiles,
  LocalRestore,
  RemotePull,
  RemoteUpdates,
  RemoteUpdateDB,
  LocalUpdates,
  LocalUpdateStatus
]

Operations = {}

def operation_help():
  help_txt = ''
  help_txt += "Sites:\n"
  for site_name in sorted(sites.keys()):
    help_txt += "  {}\n".format(sites[site_name].name)
  help_txt += "\nOperations (OP):\n"
  max_op_len = max(map(len, Operations.keys()))
  t_wrapper = textwrap.TextWrapper()
  t_wrapper.width = 80
  t_wrapper.initial_indent = ' ' * 2
  t_wrapper.subsequent_indent = ' ' * (6 + max_op_len)
  for operation_name in sorted(Operations.keys()):
    operation = Operations[operation_name]
    op_help = "{}{}    {}\n".format(operation.name, 
                                        ' ' * (max_op_len - len(operation.name)), 
                                        operation.desc)
    help_txt += t_wrapper.fill(op_help)+"\n"
  return help_txt

def init_operations():
  global Operations
  for operation in OperationClasses:
    Operations[operation.name] = operation

init_operations()
sites = init_sites()

def interactive():
  site_option = None
  op_option = None
  site_options = ['all']
  for site_name in sorted(sites.keys()):
    site_options.append(site_name)
  while site_option is None:
    print "Sites:"
    x = 0
    for site_name in site_options:
      print "  {} {}".format(x, site_name)
      x += 1
    site_inp = raw_input("Site [0]? ")
    if site_inp == '':
      site_inp = '0'
    try:
      site_num = int(site_inp)
      if site_num < 0 or site_num >= len(site_options):
        print("Invalid choice")
      else:
        site_option = site_options[site_num]
    except ValueError:
      print("Invalid number")
  while op_option is None:
    print("\nOperations:")
    x = 0
    op_keys = sorted(Operations.keys())
    for op_name in op_keys:
      print "  {} {}".format(x, op_name)
      x += 1
    op_inp = raw_input("Operation? ")
    try:
      op_num = int(op_inp)
      if op_num < 0 or op_num >= len(Operations):
        print("Invalid choice")
      else:
        op_option = op_keys[op_num]
    except ValueError:
      print("Invalid number")
  return ([site_option], op_option)

set_verbose(False)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Manage drupal sites',
    epilog=operation_help(),
    formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('-i','--interactive', action='store_true')
  parser.add_argument('-d','--dry-run', action='store_true')
  parser.add_argument('-v','--verbose', action='store_true')
  parser.add_argument('--sites', nargs='*')
  parser.add_argument('--op')
  errors = 0
  try:
    if len(sys.argv) == 1:
      parser.print_help()
      sys.exit(1)
    args = parser.parse_args()
    set_verbose(args.verbose)
    if args.interactive:
      (site_option, op_option) = interactive()
    else:
      op_option = args.op
      site_option = args.sites
    if not Operations.has_key(op_option):
      print "Operation {0} is not recognized.".format(op_option)
      errors += 1
    sites_to_do = set()
    for site_name in site_option:
      if site_name == 'all':
        sites_to_do = set(sites.values())
      else:
        if sites.has_key(site_name):
          sites_to_do.add(sites[site_name])
        else:
          print "No site named '{0}'".format(site_name)
          errors += 1
    if errors == 0:
      for site in sites_to_do:
        operation_cls = Operations[op_option]
        operation = operation_cls(site)
        if args.dry_run:
          print("Dry run for operation {} on site {}".format(operation.name, site.name))
        else:
          operation.do_cmd()
  finally:
    if errors == 0:
      print("Done")
    else:
      print("Done with {0} errors".format(errors))
