#!/usr/bin/env python

import abc
import os
import os.path
import subprocess
import shlex
import argparse
import sys

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

class Operation:
  name = None
  
  @abc.abstractmethod
  def do_cmd(self):
    """Perform a command"""
    return
  
  def sys_cmd(self, cmd, check_error = True):
    os.chdir(self.site.doc_root)
    args = shlex.split(cmd)
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (self.stdoutdata, self.stderrdata) = p.communicate()
    self.returncode = p.returncode
    if self.returncode != 0 and check_error:
      print "***ERROR*** for '{0}'".format(cmd)
      print self.stderrdata
    else:
      print self.stdoutdata
    
  def ssh_cmd(self, cmd, check_error = True, tty = False):
    if tty:
      args = ['ssh', '-t', self.site.ssh_alias, cmd]
    else:
      args = ['ssh', self.site.ssh_alias, cmd]
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (self.stdoutdata, self.stderrdata) = p.communicate()
    self.returncode = p.returncode
    if self.returncode != 0 and check_error:
      print "***ERROR*** for '{0}'".format(cmd)
      print self.stderrdata
    else:
      print self.stdoutdata

class Remote2LocalRestore(Operation):
  name = 'remote_to_local_restore'
  desc = 'Snapshot remote, sync backupfiles to local, restore snapshot on local'

  def __init__(self, site):
    self.site = site

  def do_cmd(self):
    RemoteBackup(self.site).do_cmd()
    Remote2LocalBamFiles(self.site).do_cmd()
    LocalRestore(self.site).do_cmd()

class RemoteBackup(Operation):
  name = 'remote_backup'
  desc = 'Snapshot remote (snapshot.mysql.gz in manual directory)'
  
  def __init__(self, site):
    self.site = site

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

  def do_cmd(self):
    cmd = "rsync -r {}:{}/{}/ {}/{}/".format(self.site.ssh_alias, 
      self.site.vps_dir, self.site.bam_files, self.site.doc_root, self.site.bam_files)
    self.sys_cmd(cmd)

class LocalRestore(Operation):
  name = 'local_restore'
  desc = 'Restore db from snapshot in manual backup directory'
  
  def __init__(self, site):
    self.site = site

  def do_cmd(self):
    cmd = 'drush --root={} --yes bam-restore db manual snapshot.mysql.gz'.format(self.doc_root)
    self.sys_cmd(cmd)

class RemotePull(Operation):
  name = 'remote_pull'
  desc = 'Do git pull on remote system'
  
  def __init__(self, site):
    self.site = site

  def do_cmd(self):
    self.ssh_cmd('cd {} && git pull'.format(self.site.vps_dir))

class RemoteUpdates(Operation):
  name = 'remote_updates'
  desc = 'Backup remote, remote git pull, remote drush updatedb'
  
  def __init__(self, site):
    self.site = site

  def do_cmd(self):
    RemoteBackup(self.site).do_cmd()
    RemotePull(self.site).do_cmd()
    RemoteUpdateDB(self.site).do_cmd()

class RemoteUpdateDB(Operation):
  name = 'remote_update_db'
  desc = 'Remote drush updatedb'
  
  def __init__(self, site):
    self.site = site

  def do_cmd(self):
    self.ssh_cmd("drush --root={} --yes updatedb".format(self.site.vps_dir))

class LocalUpdates(Operation):
  name = 'local_updates'
  desc = 'Pull from master, update modules, commit and push to master'
  
  def __init__(self, site):
    self.site = site

  def do_cmd(self):
    self.sys_cmd('git pull'.format(self.site.doc_root))
    self.sys_cmd('drush --root={} --yes up'.format(self.site.doc_root), check_error=False)
    self.sys_cmd('git checkout .gitignore'.format(self.site.doc_root))
    self.sys_cmd('git add *'.format(self.site.doc_root))
    self.sys_cmd('git reset -- sites/default/settings.php'.format(self.site.doc_root))
    self.sys_cmd('git commit -a -m "updates"'.format(self.site.doc_root), check_error=False)
    self.sys_cmd('git push'.format(self.site.doc_root))
  
class Site:
  def __init__(self, name, ssh_alias, doc_root, vps_dir='www', bam_files='sites/default/files/private/backup_migrate'):
    self.name = name
    self.ssh_alias = ssh_alias
    self.doc_root = doc_root
    self.vps_dir = vps_dir
    self.bam_files = bam_files
    if not os.path.exists(doc_root):
      raise Exception('Site '+name+' docroot '+doc_root+' does not exist')

OperationClasses = [Remote2LocalRestore,
  RemoteBackup,
  Remote2LocalBamFiles,
  LocalRestore,
  RemotePull,
  RemoteUpdates,
  RemoteUpdateDB,
  LocalUpdates
]

Operations = {}

def operation_help():
  help = "Operations:\n"
  for operation_name in Operations:
    operation = Operations[operation_name]
    help += "  {}\t\t{}\n".format(operation.name, operation.desc)
  return help

def init_operations():
  for operation in OperationClasses:
    Operations[operation.name] = operation

init_operations()

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Manage drupal sites',
    epilog=operation_help(),
    formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('-v','--verbose', action='store_true')
  parser.add_argument('--sites', nargs='*')
  parser.add_argument('--op')
  errors = 0
  try:
    if len(sys.argv) == 1:
      parser.print_help()
      sys.exit(1)
    args = parser.parse_args()
    if not Operations.has_key(args.op):
      print "Operation {0} is not recognized.".format(args.op)
      errors += 1
    sites = init_sites()
    sites_to_do = set()
    for site_name in args.sites:
      if site_name == 'all':
        sites_to_do = sets.Set(sites.values())
      else:
        if sites.has_key(site_name):
          sites_to_do.add(sites[site_name])
        else:
          print "No site named '{0}'".format(site_name)
          errors += 1
    if errors == 0:
      for site in sites_to_do:
        operation_cls = Operations[args.op]
        operation = operation_cls(site)
        operation.do_cmd()
  finally:
    if errors == 0:
      print("Done")
    else:
      print("Done with {0} errors".format(errors))
