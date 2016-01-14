#!/usr/bin/env python

#TODO: Command line checking for no commands should print help info

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

class Site:
  def __init__(self, name, ssh_alias, doc_root, vps_dir='www', bam_files='sites/default/files/private/backup_migrate'):
    self.name = name
    self.ssh_alias = ssh_alias
    self.doc_root = doc_root
    self.vps_dir = vps_dir
    self.bam_files = bam_files
    if not os.path.exists(doc_root):
      raise Exception('Site '+name+' docroot '+doc_root+' does not exist')

  def remote_to_local_restore(self):
    self.remote_backup()
    self.remote_to_local_bam_files()
    self.local_restore()

  def remote_to_local_bam_files(self):
    cmd = "rsync -r {}:{}/{}/ {}/{}/".format(self.ssh_alias, 
      self.vps_dir, self.bam_files, self.doc_root, self.bam_files)
    self.sys_cmd(cmd)
    
  def do_local_updates(self):
    print "Starting local updates for '{0}'".format(self.name)
    self.sys_cmd('git pull')
    self.sys_cmd('drush --yes up', check_error=False)
    self.sys_cmd('git checkout .gitignore')
    self.sys_cmd('git add *')
    self.sys_cmd('git reset -- sites/default/settings.php')
    self.sys_cmd('git commit -a -m "updates"', check_error=False)
    self.sys_cmd('git push')
    print "Finished local updates for '{0}'".format(self.name)

  def remote_updates(self):
    self.remote_backup()
    self.remote_pull()
    self.remote_update_db()
    
  def remote_backup(self):
    print "Doing remote_backup for site {0}".format(self.name)
    cmd = 'cd {} && rm {}/manual/snapshot*'.format(self.vps_dir, self.bam_files)
    self.ssh_cmd(cmd)
    cmd = 'cd {} && drush bam-backup db manual snapshot'.format(self.vps_dir)
    self.ssh_cmd(cmd)
    
  def local_restore(self):
    print "Doing local_restore for site {0}".format(self.name)
    cmd = 'drush --root={} --yes bam-restore db manual snapshot.mysql.gz'.format(self.doc_root)
    self.sys_cmd(cmd)
    
  def remote_pull(self):
    print "Doing remote_pull for site {0}".format(self.name)
    self.ssh_cmd('cd '+self.vps_dir+' && git pull')

  def remote_update_db(self):
    print "Doing remote_update_db for site {0}".format(self.name)
    self.ssh_cmd('cd '+self.vps_dir+' && drush --yes updatedb')
    
  def sys_cmd(self, cmd, check_error = True):
    os.chdir(self.doc_root)
    args = shlex.split(cmd)
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (self.stdoutdata, self.stderrdata) = p.communicate()
    self.returncode = p.returncode
    if self.returncode != 0 and check_error:
      print "***ERROR*** for '{0}'".format(cmd)
      print self.stderrdata
    else:
      print self.stdoutdata
    
  def ssh_cmd(self, cmd, check_error = True):
    args = ['ssh', self.ssh_alias, cmd]
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (self.stdoutdata, self.stderrdata) = p.communicate()
    self.returncode = p.returncode
    if self.returncode != 0 and check_error:
      print "***ERROR*** for '{0}'".format(cmd)
      print self.stderrdata
    else:
      print self.stdoutdata

def foo():
  args = ['ssh', 'gh', 'cd www && ls']
  
  p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  (stdoutdata, stderrdata) = p.communicate()
  if p.returncode != 0:
    print "***ERROR***"
    print stderrdata
  else:
    print stdoutdata

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Manage drupal sites')
  parser.add_argument('--foo', action='store_true')
  parser.add_argument('-v','--verbose', action='store_true')
  parser.add_argument('--sites', nargs='*')
  parser.add_argument('--op')
  errors = 0
  try:
    args = parser.parse_args()
    import inspect
    if not inspect.ismethod(getattr(Site, args.op, None)):
      print "Operation {0} is not recognized.".format(args.op)
      errors += 1
    if args.foo:
      foo()
    else:
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
          op_fn = getattr(site, args.op, None)
          if op_fn is not None:
            op_fn()
          else:
            print "Can't perform '{0}' on site '{1}'".format(args.op, site.name)
            errors += 1
  finally:
    if errors == 0:
      print("Done")
    else:
      print("Done with {0} errors".format(errors))
