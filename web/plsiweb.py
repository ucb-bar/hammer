# PLSI web interface.
# Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>

# Currently supports only the Chisel core generator.
# More to come.

# vim: tabstop=4 expandtab

from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from peewee import * # pylint: disable=unused-wildcard-import,wildcard-import
from playhouse.sqlite_ext import SqliteExtDatabase
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor as Pool
import os
import shutil
import subprocess
import sys

# Add instance-specific configuration in config.cfg.
class DefaultSettings:
    # Port to run the web interface on.
    PORT = "5050"
    # SQLite3 database to use for storage.
    SQLITE_DB = "configs.db"
    # PLSI folder. You should probably set this up ahead of time and run one
    # pass to build all the tools, etc.
    # Requires an appropriate Makefile.project in the parent folder.
    # TODO: automatically deal with the Makefile.project
    PLSI_DIR = "/home/ubuntu/build_flow/plsi"
    # PLSI web folder.
    # Used to store log files, final build outputs, and cloned source repos.
    PLSI_WEB_DIR = os.getcwd()
    # Secret key. Replace in config.cfg.
    SECRET_KEY = 'Eighek7eesai4ahghue7gaa7shabohy'

app = Flask(__name__)
app.config.from_object(DefaultSettings)
app.config.from_pyfile('config.cfg', silent=True)

db = SqliteExtDatabase(app.config['SQLITE_DB'])

class AppBaseModel(Model):
    class Meta:
        database = db

class CompileConfig(AppBaseModel):
    config_id = PrimaryKeyField()

    # Name of the configuration (must be unique)
    name = CharField(unique=True, default="")

    # PLSI chisel generator parameters
    CORE_TOP = CharField(default="")
    CORE_SIM_TOP = CharField(default="")
    CORE_CONFIG_TOP_PACKAGE = CharField(default="")

    # Git repo URL for this configuration
    # e.g. https://github.com/edwardcwang/microdemo.git
    git_repo = CharField(default="")
    # Git branch to use
    git_branch = CharField(default="master")

    def update(self, d):
        """
        Update this config with the given dictionary of values, e.g. "CORE_TOP".
        """
        for key, value in d.items():
            try:
                setattr(self, key, value)
            except AttributeError:
                pass

    def checkout(self, target):
        """
        Check out the given target, assuming the repo is valid.
        The target can either be a revision or a branch.
        Return:
            Bool, String
            True on success, and string with log
        """
        if not self.is_valid():
            return False, "Invalid repo"

        args = ['git', 'checkout', target]
        try:
            subprocess.check_call(args, cwd=self.repodir(), stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            # If the folder doesn't exist, it's not valid.
            return False, "failed to checkout " + target
        except subprocess.CalledProcessError:
            return False, "No such checkout target " + target 

        return True, "success"

    def recreate(self):
        """
        Delete this repo and re-create it.
        Return:
            Bool, String
            True on success, and string with log
        """
        # Remove the existing folder.
        try:
            shutil.rmtree(self.repodir())
        except FileNotFoundError:
            # It's okay if it doesn't exist yet.
            pass
        # Re-create the folder.
        os.makedirs(self.repodir(), exist_ok=True)
        # Clone into the given folder
        args = ['git', 'clone', self.git_repo, self.repodir()]
        try:
            subprocess.check_call(args, stderr=subprocess.STDOUT)
        except FileNotFoundError:
            # If the folder doesn't exist, it's not valid.
            return False, "failed to clone"

        success, msg = self.checkout(self.git_branch)
        if not success:
            return success, msg

        return True, "success"

    def refresh(self):
        """
        Refresh this repo by pulling the latest changes and changing branches as
        needed.
        Return:
            Bool, String
            True on success, and string with log
        """
        args = ['git', 'reset', '--hard', 'HEAD']
        try:
            subprocess.check_call(args, cwd=self.repodir(), stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            # If the folder doesn't exist, it's not valid.
            return False, "failed to clear working directory"

        args = ['git', 'fetch']
        try:
            subprocess.check_call(args, cwd=self.repodir(), stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            # If the folder doesn't exist, it's not valid.
            return False, "failed to fetch changes"

        success, msg = self.checkout(self.git_branch)
        if not success:
            return success, msg

        args = ['git', 'pull']
        try:
            subprocess.check_call(args, cwd=self.repodir(), stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            # If the folder doesn't exist, it's not valid.
            return False, "failed to pull changes into branch"

        return True, "success"

    def validate(self):
        """
        Validate this config.
        Returns:
            Bool, List(String) - True if valid, List of strings describing the error if invalid
        """
        valid = True
        msgs = []

        if self.name == "":
            valid = False
            msgs.append("Name not set")
        if self.CORE_TOP == "":
            valid = False
            msgs.append("Synthesis top module name not set")
        if self.CORE_SIM_TOP == "":
            valid = False
            msgs.append("Simulation top module name not set")
        if self.CORE_CONFIG_TOP_PACKAGE == "":
            valid = False
            msgs.append("Top module package not set")
        if self.git_repo == "":
            valid = False
            msgs.append("Git repo not set")
        if self.git_branch == "":
            valid = False
            msgs.append("Git branch not set")

        return valid, msgs

    def repodir(self):
        """
        Get the repository directory for this config.
        """
        return app.config['PLSI_WEB_DIR'] + '/' + self.name

    def is_valid(self):
        """
        Return true if the repository is valid (i.e. cloned properly).
        """
        args = ['git', 'rev-parse', '--is-inside-work-tree'] # returns status 0 if valid git repo
        try:
            return subprocess.call(args, cwd=self.repodir(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
        except FileNotFoundError:
            # If the folder doesn't exist, it's not valid.
            return False

    def git_revision(self):
        """
        Get the git revision of the repo or None if the repo is invalid.
        """
        if not self.is_valid():
            return None

        args = ['git', 'rev-parse', '--short', 'HEAD']
        try:
            return subprocess.check_output(args, cwd=self.repodir(), stderr=subprocess.DEVNULL).decode("utf-8").strip()
        except FileNotFoundError:
            # If the folder doesn't exist, it's not valid.
            return None

    def git_branch_actual(self):
        """
        Get the actual on-disk git branch of the repo or None if the repo is
        invalid or not in a branch.
        """
        if not self.is_valid():
            return None

        args = ['git', 'symbolic-ref', '--short', 'HEAD']
        try:
            return subprocess.check_output(args, cwd=self.repodir(), stderr=subprocess.DEVNULL).decode("utf-8").strip()
        except FileNotFoundError:
            # If the folder doesn't exist, it's not valid.
            return None
        except subprocess.CalledProcessError:
            # If the folder doesn't exist, it's not valid.
            return None

class Runs(AppBaseModel):
    time = DateTimeField()
    # Uniquely generated identifier for this run, used in filenames & folder names
    identifier = CharField(unique=True)
    # Configuration associated to this run
    config = ForeignKeyField(CompileConfig, to_field="config_id")
    # Command-line used for this run
    commandline = CharField()

    def logfilename(self):
        """
        Get the path to the log file for this run.
        """
        return app.config['PLSI_WEB_DIR'] + '/' + self.identifier + ".log"

    def system_bit(self):
        """
        Get the path to the system.bit file or None if it does not exist.
        """
        bit_path = app.config['PLSI_WEB_DIR'] + '/' + self.identifier + ".bit"
        if os.path.isfile(bit_path):
            return bit_path
        else:
            return None

    def system_mcs(self):
        """
        Get the path to the system.mcs file or None if it does not exist.
        """
        mcs_path = app.config['PLSI_WEB_DIR'] + '/' + self.identifier + ".mcs"
        if os.path.isfile(mcs_path):
            return mcs_path
        else:
            return None

# Create the tables in the database.
def create_tables():
    db.connect()
    db.create_tables([CompileConfig, Runs])

def extract_entries_with_prefix(dictionary, prefix):
    """
    Extract all the entries in the given dictionary with the prefix into a new
    dictionary, without the prefix.

    Examples:
        >>> extract_entries_with_prefix({'ax_a': 0, 'ax_b': 1, 'foo': 2, 'ax_c': 3}, 'ax_')
        {'a': 0, 'c': 3, 'b': 1}
    """
    config_dict = {}
    for k in dictionary.keys():
        if k.startswith(prefix):
            config_dict[k[len(prefix):]] = dictionary[k]
    return config_dict

class RuntimeState:
    # Dictionary of identifier -> Popen objects
    run_objects = {}

@app.context_processor
def inject_render_menu():
    def render_menu(request):
        menu = [
            ('/configs', 'Configurations'),
            ('/runs', 'Runs')
        ]
        menu_items_arr = []
        for entry in menu:
            class_str = 'class="active"' if request.path == entry[0] else ""
            menu_items_arr.append('<li {0}><a href="{1}">{2}</a></li>'.format(class_str, entry[0], entry[1]))
        menu_items = "\n".join(menu_items_arr)
        menu_template = r"""
    <nav class="navbar navbar-default navbar-fixed-top">
      <div class="container">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar" aria-expanded="false" aria-controls="navbar">
            <span class="sr-only">Toggle navigation</span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="#">PLSI Web Interface</a>
        </div>
        <div id="navbar" class="navbar-collapse collapse">
          <ul class="nav navbar-nav">
            {items}
          </ul>
        </div><!--/.nav-collapse -->
      </div>
    </nav>
"""
        return menu_template.format(items=menu_items)
    return dict(render_menu=render_menu)

@app.route("/")
@app.route("/configs")
def configs():
    selected_configs = CompileConfig.select()
    return render_template('configs.html', configs=selected_configs)

@app.route("/configs/checkout/<config_id>/<rev>")
def configs_checkout(config_id, rev):
    selected_config = CompileConfig.get(CompileConfig.config_id == config_id)
    success, msg = selected_config.checkout(rev)
    return msg, 200 if success else 400

@app.route("/configs/new", methods=['GET', 'POST'])
def configs_new():
    selected_config = CompileConfig()
    if request.method == 'POST':
        config_dict = extract_entries_with_prefix(request.form, "config_")
        selected_config.update(config_dict)
        valid, errs = selected_config.validate()
        if not valid:
            flash("Please correct the errors in the form and resubmit.<br />\n" + "<br />\n".join(errs), 'error_safe')
        else:
            try:
                selected_config.save(force_insert=True)
                flash("Successfully saved!")
                return redirect(url_for('configs_edit', config_id=selected_config.config_id))
            except IntegrityError as e:
                flash("Error occurred while creating the config: " + str(e), 'error')

    return render_template('configs_edit.html', config=selected_config, is_new=True)

@app.route("/configs/recreate/<config_id>")
def configs_recreate(config_id):
    selected_config = CompileConfig.get(CompileConfig.config_id == config_id)
    success, msg = selected_config.recreate()
    return msg, 200 if success else 400

@app.route("/configs/refresh/<config_id>")
def configs_refresh(config_id):
    selected_config = CompileConfig.get(CompileConfig.config_id == config_id)
    if not selected_config.is_valid():
        # Try recreating it if there is no valid dir (e.g. new configuration).
        success, msg = selected_config.recreate()
        if not success:
            return msg, 400
    success, msg = selected_config.refresh()
    return msg, 200 if success else 400

@app.route("/configs/edit/<config_id>", methods=['GET', 'POST'])
def configs_edit(config_id):
    selected_config = CompileConfig.get(CompileConfig.config_id == config_id)
    if request.method == 'POST':
        config_dict = extract_entries_with_prefix(request.form, "config_")
        print(config_dict)
        selected_config.update(config_dict)
        valid, errs = selected_config.validate()
        if not valid:
            flash("Please correct the errors in the form and resubmit.<br />\n" + "<br />\n".join(errs), 'error_safe')
        else:
            selected_config.save()
            flash("Successfully saved!")
            return redirect(request.path)
    if (not selected_config.is_valid()) or (selected_config.git_branch_actual() != selected_config.git_branch):
        flash("Your repo need to be refreshed after creation or branch change! Please use the \"Refresh git repo\" link on the right-side panel.", 'error')
    return render_template('configs_edit.html', config=selected_config, is_new=False)

@app.route("/runs/start", methods=['POST'])
def runs_start():
    # Create the new run
    config_id = int(request.form['config_id'])
    run = Runs(config=config_id)
    run.time = datetime.now()
    # Generate a hopefully unique identifier
    identifier = run.config.name + "_" + run.time.strftime("%Y%m%d_%H%M%S")
    run.identifier = identifier

    # Define the arguments for build.
    config_name = run.config.name
    args = ['make', 'syn-verilog',
        "SHELL=/bin/bash", # TODO: remove this once plsi is rebuilt from scratch
        "CORE_CONFIG=" + config_name,
        "CORE_TOP=" + run.config.CORE_TOP,
        "CORE_SIM_TOP=" + run.config.CORE_SIM_TOP,
        "CORE_CONFIG_TOP_PACKAGE=" + run.config.CORE_CONFIG_TOP_PACKAGE,
        "CORE_CONFIG_PROJ_DIR=" + run.config.repodir()
    ] # TODO: add multicore options, other build steps, etc.
    run.commandline = ' '.join(args)

    run.save()

    # Create the log file and start the build process
    f = open(run.logfilename(), 'wb')
    f.write(("# This is the automatically generated log of the run " + identifier + ".\n").encode())
    f.write(("# Command line executed: " + ' '.join(args) + "\n").encode())
    def create_and_wait_for_process():
        # Remove the existing folder to rebuild the .v file.
        try:
            shutil.rmtree(app.config['PLSI_DIR'] + "/" + "obj/core-chisel-" + config_name)
        except FileNotFoundError:
            # It's okay if it doesn't exist yet.
            pass

        process = subprocess.Popen(args, cwd=app.config['PLSI_DIR'], stdin=subprocess.PIPE, stdout=f, stderr=f)
        RuntimeState.run_objects[identifier] = process
        process.wait()
        bit = app.config['PLSI_DIR'] + "/" + "obj/syn-chisel-" + config_name + "-default-vivado-default-default/generated/vivado_par/obj/system.bit"
        if os.path.isfile(bit):
            shutil.copyfile(bit, app.config['PLSI_WEB_DIR'] + '/' + run.identifier + ".bit") # TODO: refactor redundancy
        mcs = app.config['PLSI_DIR'] + "/" + "obj/syn-chisel-" + config_name + "-default-vivado-default-default/generated/vivado_par/obj/system.mcs"
        if os.path.isfile(mcs):
            shutil.copyfile(mcs, app.config['PLSI_WEB_DIR'] + '/' + run.identifier + ".mcs") # TODO: refactor redundancy
            
    def callback(future):
        del RuntimeState.run_objects[identifier]
    pool = Pool(max_workers=1)
    f = pool.submit(create_and_wait_for_process)
    f.add_done_callback(callback)
    flash("New run added to queue!")
    return redirect(url_for('runs_list'))

@app.route("/runs/bit/<identifier>")
def runs_bit(identifier):
    run = Runs(identifier=identifier)
    bitfile = run.system_bit()
    if bitfile is None:
        return "No bit file", 404
    return send_file(bitfile, as_attachment=True, attachment_filename="system.bit", mimetype='application/octet-stream')

@app.route("/runs/mcs/<identifier>")
def runs_mcs(identifier):
    run = Runs(identifier=identifier)
    mcsfile = run.system_mcs()
    if mcsfile is None:
        return "No mcs file", 404
    return send_file(mcsfile, as_attachment=True, attachment_filename="system.mcs", mimetype='application/octet-stream')

@app.route("/runs/logs/<identifier>")
def runs_logs(identifier):
    run = Runs(identifier=identifier)
    return send_file(run.logfilename(), mimetype='text/plain')

@app.route("/runs/status/<identifier>")
def runs_status(identifier):
    run = Runs(identifier=identifier)
    return send_file(run.logfilename(), mimetype='text/plain')

@app.route("/runs_test")
def runs_test():
    tails = subprocess.check_output(['tail'])
    return tails

@app.route("/runs")
def runs_list():
    runobjs = Runs.select()
    runs = []
    for r in runobjs:
        d = {'time': r.time.strftime('%Y-%m-%d %H:%M:%S'), 'config': r.config.name, 'identifier': r.identifier, 'finished': (r.identifier not in RuntimeState.run_objects), 'system_bit': r.system_bit, 'system_mcs': r.system_mcs}
        runs.append(d)
    runs = sorted(runs, key=lambda k: k['time'])

    config_names = CompileConfig.select()

    return render_template('runs.html', runs=runs, config_names=config_names)

if __name__ == "__main__":
    # Create database if this is called with create_db.
    if len(sys.argv) > 1 and sys.argv[1] == "create_db":
        create_tables()
    else:
        app.run(host="0.0.0.0", port=app.config['PORT'])

