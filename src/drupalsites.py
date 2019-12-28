#!/home/mgering/.virtualenvs/sitesui/bin/python
# Author: Mike Gering

import abc
import argparse
import os.path
import shlex
import subprocess
import sys
import textwrap
import re
import datetime

def set_verbose(val):
	global verbose
	verbose = val
	
def get_verbose():
	global verbose
	return verbose

def set_operation_output(obj):
	global op_output
	op_output = obj

op_output = None

def get_operation_output():
	global op_output
	if op_output is None:
		op_output = OperationOutput()
	return op_output

def init_sites():
	# Site init: name, ssh_alias, doc_root, vps_dir = 'www', bam_files = 'sites/default/files/private/backup_migrate', base_domain = ''
	sites = {}
	sites['gattishouse'] = Site('gattishouse', 'gh', '/var/www/dev.gattishouse.com/htdocs', base_domain='gattishouse.com')
	sites['lnba'] = Site('lnba', 'lnba', '/var/www/dev.lnba.net/htdocs', base_domain='lnba.net')
	sites['unrba'] = Site('unrba', 'unrba', '/var/www/dev.unrba.org/htdocs', base_domain='unrba.org')
	#sites['ypdrba'] = Site('ypdrba', 'ypdrba', '/var/www/dev.ypdrba.org/htdocs', base_domain="yadkinpeedee.org")
	sites['ferree-gering'] = Site('ferree-gering', 'fg', '/var/www/dev.ferree-gering.com/htdocs', base_domain='ferree-gering.com')
	return sites

def trace_op(func):
	def func_wrapper(self):
		site_str = ''
		if hasattr(self, 'site'):
			site_str = "{}: ".format(self.site.name)
		get_operation_output().write("-----> {}Starting {}\n".format(site_str, self.name))
		func(self)
		get_operation_output().write("<----- {}Ending {}\n".format(site_str, self.name))
	return func_wrapper

class Operation(object):
	name = None
	desc = None
	
	def __init__(self, site = None):
		self.site = site
		self.cmds = []
		self.cmd_outputs = []

	@abc.abstractmethod
	def do_cmd(self):
		"""Perform a command"""
		return
	
	def run_a_cmd(self, args, check_error = True, print_output = True, shell=False):
		global verbose
		cmd = ' '.join(args)
		self.cmds.append(cmd)
		if verbose:
			get_operation_output().write(cmd+'\n')
		completed_process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=shell)
		cmd_output = str(completed_process.stdout, 'utf-8')
		self.returncode = completed_process.returncode
		self.cmd_outputs.append(cmd_output)
		if print_output:
			if self.returncode != 0 and check_error:
				get_operation_output().write("***ERROR*** for '{0}'\n".format(cmd))
			get_operation_output().write(cmd_output)

	
	def sys_cmd(self, cmd, check_error = True, print_output = True, shell = False):
		os.chdir(self.site.doc_root)
		args = shlex.split(cmd)
		self.run_a_cmd(args, check_error, print_output, shell)

	def ssh_cmd(self, cmd, check_error = True, tty = False, print_output = True):
		if tty:
			args = ['ssh', '-t', self.site.ssh_alias, cmd]
		else:
			args = ['ssh', self.site.ssh_alias, cmd]
		self.run_a_cmd(args, check_error, print_output)

class NoOperation(Operation):
	name = 'no_operation'
	desc = 'Does nothing'

	def __init__(self, site):
		super(NoOperation, self).__init__(site)

	@trace_op
	def do_cmd(self):
		get_operation_output().write("Can't perform")
	
class RemoteCheckCert(Operation):
	name = 'remote_cert'
	desc = 'Remote tls cert check'
	
	def __init__(self, site):
		super(RemoteCheckCert, self).__init__(site)

	@trace_op
	def do_cmd(self):
		cmd = 'curl -v \'https://{}\''.format(self.site.base_domain)
		self.sys_cmd(cmd, print_output=False)
		cmd_output = self.cmd_outputs[-1]
		p = re.compile('Server certificate.*$|server certificate verification.*$', re.MULTILINE)
		m = p.search(cmd_output)
		if m is not None:
			end_pos = m.end()
			str2 = cmd_output[end_pos:]
			p = re.compile('^>', re.MULTILINE)
			m = p.search(str2)
			if m is not None:
				str3 = str2[:m.start()]
				if get_verbose():
					get_operation_output().write("Certificate info:\n"+str3+"\n")
				# Find the start date, expire date, and compute how many days left
				m = re.search(r'start date:\s+(.*)', str3)
				if m is not None:
					start_str = m.group(1)
					date_formats = ["%a, %d %b %Y %H:%M:%S %Z",
										 "%b %d %H:%M:%S %Y %Z",
					]
					start_time = None
					for format in date_formats:
						try:
							start_time = datetime.datetime.strptime(start_str, format)
							break
						except ValueError:
							pass
					if start_time is None:
						raise ValueError("No format matches the start time: %s" % start_str)
					get_operation_output().write("Start date:	{:%m/%d/%Y}\n".format(start_time))
				m = re.search(r'expire date:\s+(.*)', str3)
				if m is not None:
					expire_str = m.group(1)
					expire_time = None
					for format in date_formats:
						try:
							expire_time = datetime.datetime.strptime(expire_str, format)
							break
						except ValueError:
							pass
					if expire_time is None:
							raise ValueError("No format matches the expiration time: %s" % expire_str)
					get_operation_output().write("Expire date: {:%m/%d/%Y}\n".format(expire_time))
					now = datetime.datetime.now()
					to_expire = expire_time - now
					if to_expire.days > 14:
						msg = "Expires in {0} days\n".format(to_expire.days)
					elif to_expire.days <= 0:
						msg = "!!!!!!!!Expired {0} days ago\n".format(-to_expire.days)
					else:
						msg = "********Expires in {0} days\n".format(to_expire.days)
					get_operation_output().write(msg)
				#TODO: FIX
				# datetime.datetime.strptime(s, "%a, %d %b %Y %H:%M:%S %Z")
			else:
				get_operation_output().write("Can't find the end\n")
		else:
			#server certificate verification
			get_operation_output().write("NO MATCH")

class RemoteClearCache(Operation):
	name = 'remote_cc'
	desc = 'Remote clear cache'

	def __init__(self, site):
		super(RemoteClearCache, self).__init__(site)

	@trace_op
	def do_cmd(self):
		cmd = 'cd {} && drush --nocolor cc all'.format(self.site.vps_dir)
		self.ssh_cmd(cmd, tty=True)

class Remote2LocalRestore(Operation):
	name = 'remote_to_local_restore'
	desc = 'Snapshot remote, sync backupfiles to local, restore snapshot on local'

	def __init__(self, site):
		super(Remote2LocalRestore, self).__init__(site)

	@trace_op
	def do_cmd(self):
		self.site.get_operation('remote_backup').do_cmd()
		self.site.get_operation('remote_to_local_bam_files').do_cmd()
		self.site.get_operation('local_restore').do_cmd()

class RemoteBackup(Operation):
	name = 'remote_backup'
	desc = 'Snapshot remote (snapshot.mysql.gz in manual directory)'
	
	def __init__(self, site):
		super(RemoteBackup, self).__init__(site)

	@trace_op
	def do_cmd(self):
		cmd = "cd {} && [ -e {}/manual/snapshot.mysql.gz ] && rm {}/manual/snapshot.mysql.gz".format(self.site.vps_dir, self.site.bam_files, self.site.bam_files)
		self.ssh_cmd(cmd, check_error=False)
		cmd = "cd {} && drush --nocolor bam-backup db manual snapshot".format(self.site.vps_dir)
		self.ssh_cmd(cmd, tty=True)

class Remote2LocalBamFiles(Operation):
	name = 'remote_to_local_bam_files'
	desc = 'Sync remote backup files to local system'
	
	def __init__(self, site):
		super(Remote2LocalBamFiles, self).__init__(site)

	@trace_op
	def do_cmd(self):
		cmd = "rsync -r {}:{}/{}/ {}/{}/".format(self.site.ssh_alias, 
			self.site.vps_dir, self.site.bam_files, self.site.doc_root, self.site.bam_files)
		self.sys_cmd(cmd)

class Remote2LocalDefaultFiles(Operation):
	name = 'remote_to_local_rsync'
	desc = 'Sync remote default/files to local system'
	
	def __init__(self, site):
		super(Remote2LocalDefaultFiles, self).__init__(site)

	@trace_op
	def do_cmd(self):
		cmd = "rsync -avh --delete --exclude=css/ --exclude=js/ --exclude=ctool/ {}:{}/sites/default/files/ {}/sites/default/files/".format(self.site.ssh_alias, 
			self.site.vps_dir, self.site.doc_root)
		self.sys_cmd(cmd)
		self.site.get_operation('local_fix_perms').do_cmd()

class LocalFixPerms(Operation):
	name = 'local_fix_perms'
	desc = 'Fix local files file permissions'
	
	def __init__(self, site):
		super(LocalFixPerms, self).__init__(site)

	@trace_op
	def do_cmd(self):
		cmd = 'sudo chmod -R g+w {}'.format(self.site.doc_root)
		self.sys_cmd(cmd)
		cmd = 'sudo chown -R mgering:www-data {}'.format(self.site.doc_root)
		self.sys_cmd(cmd)

class LocalRestore(Operation):
	name = 'local_restore'
	desc = 'Restore db from snapshot in manual backup directory'
	
	def __init__(self, site):
		super(LocalRestore, self).__init__(site)

	@trace_op
	def do_cmd(self):
		cmd = 'drush --nocolor --root={} --yes bam-restore db manual snapshot.mysql.gz'.format(self.site.doc_root)
		self.sys_cmd(cmd)

class RemotePull(Operation):
	name = 'remote_pull'
	desc = 'Do git pull on remote system'
	
	def __init__(self, site):
		super(RemotePull, self).__init__(site)

	@trace_op
	def do_cmd(self):
		self.ssh_cmd('cd {} && git pull'.format(self.site.vps_dir))

class RemoteUpdates(Operation):
	name = 'remote_updates'
	desc = 'Backup remote, remote git pull, remote drush updatedb'
	
	def __init__(self, site):
		super(RemoteUpdates, self).__init__(site)

	@trace_op
	def do_cmd(self):
		self.site.get_operation('remote_backup').do_cmd()
		self.site.get_operation('remote_pull').do_cmd()		
		self.site.get_operation('remote_update_db').do_cmd()		

class RemoteUpdateDB(Operation):
	name = 'remote_update_db'
	desc = 'Remote drush updatedb'
	
	def __init__(self, site):
		super(RemoteUpdateDB, self).__init__(site)

	@trace_op
	def do_cmd(self):
		self.ssh_cmd("cd {} && drush --nocolor --yes updatedb".format(self.site.vps_dir))

class LocalUpdates(Operation):
	name = 'local_updates'
	desc = 'Pull from master, update modules & db, commit and push to master'
	
	def __init__(self, site):
		super(LocalUpdates, self).__init__(site)

	@trace_op
	def do_cmd(self):
		self.sys_cmd('git pull'.format(self.site.doc_root))
		self.sys_cmd('drush --nocolor --root={} --yes up'.format(self.site.doc_root), check_error=False)
		self.site.get_operation('local_update_db').do_cmd()		
		self.sys_cmd('git checkout .gitignore .htaccess'.format(self.site.doc_root))
		self.sys_cmd('git add *'.format(self.site.doc_root))
		self.sys_cmd('git commit -a -m "updates"'.format(self.site.doc_root), check_error=False)
		self.sys_cmd('git push'.format(self.site.doc_root))

class LocalUpdateDB(Operation):
	name = 'local_update_db'
	desc = 'Local drush updatedb'
	
	def __init__(self, site):
		super(LocalUpdateDB, self).__init__(site)

	@trace_op
	def do_cmd(self):
		self.sys_cmd('drush --nocolor --root={} --yes updatedb'.format(self.site.doc_root), check_error=False)

class LocalUpdateStatus(Operation):
	name = 'local_update_status'
	desc = 'Pull from master, check for updates'
	
	def __init__(self, site):
		super(LocalUpdateStatus, self).__init__(site)

	@trace_op
	def do_cmd(self):
		self.sys_cmd('git pull'.format(self.site.doc_root), print_output=False)
		if self.cmd_outputs[-1].find("Already up-to-date.") < 0:
			get_operation_output().write("git pulled:\n"+self.cmd_outputs[-1])
		self.sys_cmd('drush --nocolor --root={} --format=list ups'.format(self.site.doc_root), check_error=False, print_output=False)
		modules_to_update = self.cmd_outputs[-1].split("\n")
		if len(modules_to_update) > 1: # Note that the last module has a newline
			modules_to_update.pop()
			get_operation_output().write("****** {} modules need updating: {}\n".format(len(modules_to_update), ", ".join(modules_to_update)))
		else:
			get_operation_output().write("modules are up-to-date\n")

class OperationOutput(object):
	
	def write(self, msg):
		sys.stdout.write(msg)
	
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
	LocalUpdateDB,
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
	
def operation_help():
	help_txt = ''
	help_txt += "Sites:\n"
	for site_name in sorted(sites.keys()):
		help_txt += "	{}\n".format(sites[site_name].name)
	help_txt += "\nOperations (OP):\n"
	max_op_len = max(map(len, Site.operations.keys()))
	t_wrapper = textwrap.TextWrapper()
	t_wrapper.width = 80
	t_wrapper.initial_indent = ' ' * 2
	t_wrapper.subsequent_indent = ' ' * (6 + max_op_len)
	for operation_name in sorted(Site.operations.keys()):
		operation = Site.operations[operation_name]
		op_help = "{}{}		{}\n".format(operation.name, 
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
		print("Sites:")
		x = 0
		for site_name in site_options:
			print("	{} {}".format(x, site_name))
			x += 1
		site_inp = input("Site [0]? ")
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
			print("	{} {}".format(x, op_name))
			x += 1
		op_inp = input("Operation? ")
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
		if not op_option in Site.operations:
			print("Operation {0} is not recognized.".format(op_option))
			errors += 1
		sites_to_do = set()
		for site_name in site_option:
			if site_name == 'all':
				sites_to_do = set(sites.values())
			else:
				if site_name in sites:
					sites_to_do.add(sites[site_name])
				else:
					print("No site named '{0}'".format(site_name))
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
			get_operation_output().write("Done\n")
		else:
			get_operation_output().write("Done with {0} errors\n".format(errors))
