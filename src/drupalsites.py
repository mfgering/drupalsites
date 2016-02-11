#!/usr/bin/env python
# Author: Mike Gering

import abc
import argparse
import os.path
import shlex
import subprocess
import sys
import textwrap
import re

def set_verbose(val):
  global verbose
  verbose = val

def init_sites():
  sites = {}
  sites['hillsborough'] = HillsboroughSite('hillsborough', 'hb', '/var/www/dev.ci.hillsborough.nc.us/htdocs', bam_files='sites/default/files/backup_migrate', base_domain='ci.hillsborough.nc.us')
  sites['gattishouse'] = Site('gattishouse', 'gh', '/var/www/dev.gattishouse.com/htdocs', base_domain='gattishouse.com')
  sites['lnba'] = Site('lnba', 'lnba', '/var/www/dev.lnba.net/htdocs', base_domain='lnba.net')
  sites['stem'] = Site('stem', 'stem', '/var/www/dev.stemnc.org/htdocs', base_domain='stemnc.org')
  sites['unrba'] = Site('unrba', 'unrba', '/var/www/dev.unrba.org/htdocs', base_domain='unrba.org')
  sites['hcrt'] = Site('hcrt', 'hcrt', '/var/www/dev.w3.harvardtriangle.org/htdocs', vps_dir='w3.harvardtriangle.org', base_domain='w3.harvardtriangle.org')
  sites['ypdrba'] = Site('ypdrba', 'ypdrba', '/var/www/dev.ypdrba.org/htdocs', base_domain="yadkinpeedee.org")
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

class Operation(object):
  name = None
  
  @abc.abstractmethod
  def do_cmd(self):
    """Perform a command"""
    return
  
  def sys_cmd(self, cmd, check_error = True, print_output = True, shell = False):
    global verbose
    if verbose:
      print cmd
    os.chdir(self.site.doc_root)
    args = shlex.split(cmd)
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
    (self.stdoutdata, self.stderrdata) = p.communicate()
    self.returncode = p.returncode
    if print_output:
      if self.returncode != 0 and check_error:
        print "***ERROR*** for '{0}'".format(cmd)
        print self.stderrdata,
      else:
        print self.stdoutdata,
    
  def ssh_cmd(self, cmd, check_error = True, tty = False, print_output = True):
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
    if print_output:
      if self.returncode != 0 and check_error:
        print "***ERROR*** for '{0}'".format(cmd)
        print self.stderrdata,
      else:
        print self.stdoutdata,

class NoOperation(Operation):
  name = 'no_operation'
  desc = 'Does nothing'
  
  def __init__(self, site):
    self.site = site

  @trace_op
  def do_cmd(self):
    print "Can't perform"
  
class RemoteCheckCert(Operation):
  name = 'remote_cert'
  desc = 'Remote tls cert check'
  
  def __init__(self, site):
    self.site = site

  @trace_op
  def do_cmd(self):
    cmd = 'curl -v \'https://{}\''.format(self.site.base_domain)
    self.sys_cmd(cmd, print_output=False)
    p = re.compile('Server certificate.*$', re.MULTILINE)
    m = p.search(self.stderrdata)
    if not m is None:
      end_pos = m.end()
      str2 = self.stderrdata[end_pos:]
      p = re.compile('^>', re.MULTILINE)
      m = p.search(str2)
      if not m is None:
        str3 = str2[:m.start()]
        print "Certificate info:\n"+str3+"\n"
      else:
        print "Can't find the end"
    else:
      print "NO MATCH"

class RemoteClearCache(Operation):
  name = 'remote_cc'
  desc = 'Remote clear cache'
  
  def __init__(self, site):
    self.site = site

  @trace_op
  def do_cmd(self):
    cmd = 'cd {} && drush cc all'.format(self.site.vps_dir)
    self.ssh_cmd(cmd, tty=True)

class HillsboroughRemoteClearCache(RemoteClearCache):  
  def __init__(self, site):
    super(HillsboroughRemoteClearCache, self).__init__(site)

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
    self.site.get_operation('remote_backup').do_cmd()
    self.site.get_operation('remote_to_local_bam_files').do_cmd()
    self.site.get_operation('local_restore').do_cmd()

class RemoteBackup(Operation):
  name = 'remote_backup'
  desc = 'Snapshot remote (snapshot.mysql.gz in manual directory)'
  
  def __init__(self, site):
    self.site = site

  @trace_op
  def do_cmd(self):
    cmd = "cd {} && [ -e {}/manual/snapshot.mysql.gz ] && rm {}/manual/snapshot.mysql.gz".format(self.site.vps_dir, self.site.bam_files, self.site.bam_files)
    self.ssh_cmd(cmd, check_error=False)
    cmd = "cd {} && drush bam-backup db manual snapshot".format(self.site.vps_dir)
    self.ssh_cmd(cmd, tty=True)

class HillsboroughRemoteBackup(RemoteBackup):
  def __init(self, site):
    super(HillsboroughRemoteBackup, self).__init__(site)
    
  @trace_op
  def do_cmd(self):
    print "Doing external (www) site..."
    cmd = "cd {} && [ -e {}/manual/snapshot.mysql.gz ] && rm {}/manual/snapshot.mysql.gz".format(self.site.vps_dir, self.site.bam_files, self.site.bam_files)
    self.ssh_cmd(cmd, check_error=False)
    cmd = "cd {} && drush bam-backup db manual snapshot".format(self.site.vps_dir)
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

class HillsboroughRemote2LocalBamFiles(Remote2LocalBamFiles):
  def __init__(self, site):
    super(HillsboroughRemote2LocalBamFiles, self).__init__(site)
    
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
    self.site.get_operation('local_fix_perms').do_cmd()

class HillsboroughRemote2LocalDefaultFiles(Remote2LocalDefaultFiles):
  def __init__(self, site):
    super(HillsboroughRemote2LocalDefaultFiles, self).__init__(site)

  @trace_op
  def do_cmd(self):
    cmd = "rsync -avh --delete --exclude=css/ --exclude=js/ --exclude=ctool/ {}:{}/sites/default/files/ {}/sites/default/files/".format(self.site.ssh_alias, 
      self.site.vps_dir, self.site.doc_root)
    self.sys_cmd(cmd)
    
class LocalFixPerms(Operation):
  name = 'local_fix_perms'
  desc = 'Fix local files file permissions'
  
  def __init__(self, site):
    self.site = site

  @trace_op
  def do_cmd(self):
    cmd = 'sudo chmod -R g+w {}/sites/default/files'.format(self.site.doc_root)
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

class HillsboroughLocalRestore(LocalRestore):
  def __init__(self, site):
    super(HillsboroughLocalRestore, self).__init__(site)
    
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
    self.site.get_operation('remote_backup').do_cmd()
    self.site.get_operation('remote_pull').do_cmd()    
    self.site.get_operation('remote_update_db').do_cmd()    

class RemoteUpdateDB(Operation):
  name = 'remote_update_db'
  desc = 'Remote drush updatedb'
  
  def __init__(self, site):
    self.site = site

  @trace_op
  def do_cmd(self):
    self.ssh_cmd("cd {} && drush --yes updatedb".format(self.site.vps_dir))

class HillsboroughRemoteUpdateDB(RemoteUpdateDB):
  def __init__(self, site):
    super(HillsboroughRemoteUpdateDB, self).__init__(site)

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
    self.sys_cmd('git commit -a -m "updates"'.format(self.site.doc_root), check_error=False)
    self.sys_cmd('git push'.format(self.site.doc_root))

class HillsboroughLocalUpdates(LocalUpdates):
  def __init__(self, site):
    super(HillsboroughLocalUpdates, self).__init__(site)

  @trace_op
  def do_cmd(self):
    # Hillsborough is different because the local settings files are different from the remote ones,
    # and there is internal site, too
    self.sys_cmd('git pull'.format(self.site.doc_root))
    self.sys_cmd('drush --root={} --yes up'.format(self.site.doc_root), check_error=False)
    # The following will revert the gitignore and settings files to HEAD
    self.sys_cmd('git checkout .gitignore sites/default/settings.php'.format(self.site.doc_root))
    self.sys_cmd('git add *'.format(self.site.doc_root))
    self.sys_cmd('git commit -a -m "updates"'.format(self.site.doc_root), check_error=False)
    self.sys_cmd('git push'.format(self.site.doc_root))
    self.sys_cmd('cp sites/default/settings-dev.php sites/default/settings.php') # restore dev settings
  
class LocalUpdateStatus(Operation):
  name = 'local_update_status'
  desc = 'Pull from master, check for updates'
  
  def __init__(self, site):
    self.site = site

  @trace_op
  def do_cmd(self):
    self.sys_cmd('git pull'.format(self.site.doc_root), print_output=False)
    if self.stdoutdata.find("Already up-to-date.") < 0:
      print "git pulled:\n"+self.stdoutdata
    self.sys_cmd('drush --root={} --format=list ups'.format(self.site.doc_root), check_error=False, print_output=False)
    modules_to_update = self.stdoutdata.split("\n")
    if len(modules_to_update) > 1: # Note that the last module has a newline
      modules_to_update.pop()
      print "****** {} modules need updating: {}".format(len(modules_to_update), ", ".join(modules_to_update))
    else:
      print "modules are up-to-date"

class HillsboroughLocalUpdateStatus(LocalUpdateStatus):
  def __init__(self, site):
    super(HillsboroughLocalUpdateStatus, self).__init__(site)

  @trace_op
  def do_cmd(self):
    self.sys_cmd('git pull'.format(self.site.doc_root), print_output=False)
    if self.stdoutdata.find("Already up-to-date.") < 0:
      print "git pulled:\n"+self.stdoutdata
    self.sys_cmd('drush --root={} --format=list ups'.format(self.site.doc_root), check_error=False, print_output=False)
    modules_to_update = self.stdoutdata.split("\n")
    if len(modules_to_update) > 1: # Note that the last module has a newline
      modules_to_update.pop()
      print "****** main site: {} modules need updating: {}".format(len(modules_to_update), ", ".join(modules_to_update))
    else:
      print "main site modules are up-to-date"

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
  LocalUpdateStatus,
  LocalFixPerms,
  RemoteCheckCert
]

def base_operations():
  result = {}
  for operation in OperationClasses:
    result[operation.name] = operation
  return result

class Site(object):
  
  operations = base_operations()
  
  def __init__(self, name, ssh_alias, doc_root, vps_dir='www', bam_files='sites/default/files/private/backup_migrate', base_domain=''):
    self.name = name
    self.ssh_alias = ssh_alias
    self.doc_root = doc_root
    self.vps_dir = vps_dir
    self.bam_files = bam_files
    self.base_domain = base_domain
    if not os.path.exists(doc_root):
      raise Exception('Site '+name+' docroot '+doc_root+' does not exist')
  
  def get_operation(self, op_name):
    op_cls = Site.operations[op_name] 
    return op_cls(self)

class HillsboroughSite(Site):
  def __init__(self, name, ssh_alias, doc_root, vps_dir='www', bam_files='sites/default/files/private/backup_migrate', base_domain=''):
    super(HillsboroughSite, self).__init__(name, ssh_alias, doc_root, vps_dir, bam_files, base_domain)

  def get_operation(self, op_name):
    op = super(HillsboroughSite, self).get_operation(op_name)
    if op_name == 'local_updates':
      op = HillsboroughLocalUpdates(self)
    elif op_name == 'remote_update_db':
      op = HillsboroughRemoteUpdateDB(self)
    elif op_name == 'local_update_status':
      op = HillsboroughLocalUpdateStatus(self)
    elif op_name == 'remote_cc':
      op = HillsboroughRemoteClearCache(self)
    elif op_name == 'remote_backup':
      op = HillsboroughRemoteBackup(self)
    elif op_name == 'remote_to_local_rsync':
      op = HillsboroughRemote2LocalDefaultFiles(self)
    elif op_name == 'local_restore':
      op = HillsboroughLocalRestore(self)
    elif op_name == 'remote_to_local_bam_files':
      op = HillsboroughRemote2LocalBamFiles(self)
    else:
      op = NoOperation(self)
    return op
  
def operation_help():
  help_txt = ''
  help_txt += "Sites:\n"
  for site_name in sorted(sites.keys()):
    help_txt += "  {}\n".format(sites[site_name].name)
  help_txt += "\nOperations (OP):\n"
  max_op_len = max(map(len, Site.operations.keys()))
  t_wrapper = textwrap.TextWrapper()
  t_wrapper.width = 80
  t_wrapper.initial_indent = ' ' * 2
  t_wrapper.subsequent_indent = ' ' * (6 + max_op_len)
  for operation_name in sorted(Site.operations.keys()):
    operation = Site.operations[operation_name]
    op_help = "{}{}    {}\n".format(operation.name, 
                                        ' ' * (max_op_len - len(operation.name)), 
                                        operation.desc)
    help_txt += t_wrapper.fill(op_help)+"\n"
  return help_txt

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
    op_keys = sorted(Site.operations.keys())
    for op_name in op_keys:
      print "  {} {}".format(x, op_name)
      x += 1
    op_inp = raw_input("Operation? ")
    try:
      op_num = int(op_inp)
      if op_num < 0 or op_num >= len(Site.operations):
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
    if not Site.operations.has_key(op_option):
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
        operation = site.get_operation(op_option)
        if args.dry_run:
          print("Dry run for operation {} on site {}".format(operation.name, site.name))
        else:
          operation.do_cmd()
  finally:
    if errors == 0:
      print("Done")
    else:
      print("Done with {0} errors".format(errors))
