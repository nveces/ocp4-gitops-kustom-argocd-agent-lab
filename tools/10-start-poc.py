"""
 2025 PoC Wizard: Using the Argo CD Agent with OpenShift GitOps

Usage:
    python ./10-start-poc.py

    Based on the https://developers.redhat.com/blog/2025/10/06/using-argo-cd-agent-openshift-gitops  (Created by Gerald Nunn https://developers.redhat.com/author/gerald-nunn)

    Created by Nveces, 2025

"""

import sys
import os
import time
import json
import logging
import subprocess
import time, datetime
import pathlib
import rich
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
import inquirer

# ============================ #
# ====== Initialization ====== #
# ============================ #

# Variable global para almacenar los textos cargados
I18N = {}
BIN_DIR = ''
# en | es | ca
DEFAULT_LANG = "en"
DEFAULT_LANG_PATH = "i18n"
#os.path.basename
STEPS = []
STEP_EXECUTION_STATUS = {}

# Rich Console Initialization
console = Console()
status_message = "Initializing..."
current_step = 0

# Session File Global Variable
GLOBAL_SESSION_FILE = None #
STEP_EXECUTION_STATUS = {} #
ENABLE_SESSION_PERSISTENCE = False

# Date Formats
DATE_FMT_01='%Y-%m-%d %H:%M:%S'
DATE_FMT_02='%Y-%m-%d,%H:%M:%S'
DATE_FMT_03="%F %A %T"
DATE_FMT_04='%Y/%m/%d %H:%M:%S'
DATE_FMT_05='%Y-%m-%d %H-%M-%S'
DATE_FMT_06='%Y-%m-%dT%H:%M:%S.%f'
# Logs Path
PATH_LOGS='/tmp/'
FILELOG_EXT  =".log"
FILE_ENCODING = 'utf-8'
FILELOG_PATH=''  # To be initialized in _init_logger() as PATH_LOGS + os.path.basename( __file__)[:-3] +
#
STL_DEFAULT = "bold white"               # Default Step
STL_CURRENT_STEP = "bold green reverse"  # Current Step
STL_DRYRUN_EXECUTED_STEP = "italic cyan" # Dry run Completed Step
STL_COMPLETED_STEP = "dim cyan"          # Completed Step
#
# Rich attributes
# bold       [bold]Texto[/]
# italic     [italic]Texto[/]
# underline  [underline]Texto[/]
# dim        [dim]Texto[/]
# reverse    [reverse]Texto[/]
# strike     [strike]Texto[/]
# blink      [blink]Texto[/]
# none       [none]Texto[/]
#
# Colors: rgb(r,g,b) #RRGGBB color(208)
# Basic colors:
# red, green, blue, yellow, magenta, cyan, white, black
# bright_red, bright_green, bright_blue, bright_yellow, bright_magenta, bright_cyan, bright_white, bright_black
#
# ==================================== #
# ====== Unicode Characters ========== #
# ==================================== #
#   Code Point  Python Unicode  Archivo JSON
# 🚀 U+1F680   \U0001f680       \uD83d\uDE80
# ✅	U+2705	  \u2705           \u2705
# ❌	U+274C	  \u274c           \u274c
# ⚠️ U+26A0    \u26a0
# ℹ️ U+2139    \u2139
# ➡️ U+27A1    \u27a1
# ⬅️ U+2B05    \u2b05
# 🚨           \ud83d\udea8     \U0001f6a8
# 🎉           \ud83c\udf89     \U0001F389
# ==================================== #
# ====== Functions & Procedures ====== #
# ==================================== #
def usage():
    #print("usage")
    print(__doc__)

def _init_logger():
    global FILELOG_PATH
    fileMode='a+' # The 'a' enables you to append to a file and the '+' will create the file if it doesn't already exist.
    #fileMode='w'
    FILELOG_PATH = PATH_LOGS + os.path.basename( __file__)[:-3] + FILELOG_EXT
    logging.basicConfig(handlers=[logging.FileHandler(filename=FILELOG_PATH, encoding=FILE_ENCODING, mode=fileMode)],
                                  #,logging.StreamHandler(sys.stdout)], # You can add multiple handlers, sys.stdout for console
                    format="[%(asctime)s] [%(levelname)s] -- %(name)s -- %(module)s-- %(message)s",
                    datefmt=DATE_FMT_01,
                    level=logging.DEBUG)
    msg("End init_logger")

def getDateTime(formatdatetime='[%Y-%m-%d %H:%M:%S]'):
    return datetime.datetime.fromtimestamp(time.time()).strftime(formatdatetime)

def msg(msg):
    print ("\033[1;32m" + getDateTime() + " [INFO] " + msg + "\033[0m")


# --- I18N localization function ---
def i18n(key: str) -> str:
    """
    Find by key in I18N dictionary.
    If the key does not exist, returns a distinctive error string.
    """
    global I18N
    # We use .get(key, default) to handle missing keys
    # The default value is the requested error string
    return I18N.get(key, f"!{key}!")


def get_script_content(file_path: str, line_range: str) -> str:
    """Execute sed to get the content of a file within a line range."""

    if not line_range or not file_path:
        return i18n('no_display_content')

    try:
        # Build the sed command
        sed_command = f"sed -n '{line_range}p' {file_path}"

        # Execute the command and capture the output
        result = subprocess.run(
            [sed_command],
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )

        return result.stdout.strip()

    except subprocess.CalledProcessError as e:
        # If sed fails, return an error message
        return f"[bold red]\U0001f6a8 ERROR reading the script: '{file_path}'. Detected error:[/]\n{e.stderr.strip()}"
    except FileNotFoundError:
        return f"[bold red]\U0001f6a8 ERROR: File not found: '{file_path}'.[/]"


def load_localization(lang=DEFAULT_LANG):
    """Load localization literals from the specified language JSON file."""
    global I18N, DEFAULT_LANG_PATH
    i18n_resources = pathlib.Path(__file__).resolve().parent / DEFAULT_LANG_PATH / lang
    try:
        filename = f"{i18n_resources}.json"
        with open(filename, 'r', encoding=FILE_ENCODING) as f:
            I18N = json.load(f)
    except FileNotFoundError:
        # Handling error if the file is not found
        print(f"\n\U0001f6a8 ERROR: The file for language '{lang}' was not found. Review '{filename}'.")
        sys.exit(1)

def load_steps_data(steps_file_path: pathlib.Path) -> list:
    """Load steps data from a JSON file."""
    try:
        with open(steps_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"\n\U0001f6a8 ERROR: File not found: '{steps_file_path}'.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\n\U0001f6a8 ERROR: The '{steps_file_path}' file contains invalid JSON." + e.msg)
        sys.exit(1)

def save_session(session_file_path: pathlib.Path, current_step_index: int, execution_status: dict):
    """Save the current session state to a JSON file."""
    if not ENABLE_SESSION_PERSISTENCE or GLOBAL_SESSION_FILE is None:
        return # Skip saving if persistence is disabled

    # 1. Prepare data to save
    steps_status_list = []
    # Loop through the steps to get execution status
    for i, _ in enumerate(STEPS):
        status = execution_status.get(i, "pending")
        steps_status_list.append({"index": i, "status": status})

    # 2. Building the JSON object
    session_data = {
        "current_step": current_step_index,
        "steps_status": steps_status_list
    }

    # 3. Save to JSON file
    try:
        with open(session_file_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=4)
    except Exception as e:
        console.print(f"\n[bold red]\U0001f6a8 ERROR: Unable to save session to '{GLOBAL_SESSION_FILE}':[/] {e}")


def init_global_variables(steps_file_name="steps.json",session_file_name="session.json"):
    """Initializes global variables: STEPS and status_message."""
    global STEPS, BIN_DIR, GLOBAL_SESSION_FILE,STEP_EXECUTION_STATUS, current_step, status_message
    current_step = 0 # default start step 0

    # 1. Load Steps Definition from JSON file
    steps_file_path = pathlib.Path(__file__).resolve().parent / 'steps.json'
    raw_steps = load_steps_data(steps_file_path)

    # 2. Populate name and description using i18n()
    # Also, prepare display_content if needed
    processed_steps = []
    for step_data in raw_steps:
        description_key = step_data.pop("description")
        step_data["description"] = i18n(description_key)
        name_key = step_data.pop("name")
        step_data["name"] = i18n(name_key)
        #
        display_file = step_data.get("script")
        display_lines = step_data.get("display_lines")
        if display_file and display_lines:
            display_file = BIN_DIR / display_file
            content = get_script_content(display_file, display_lines)
            step_data["display_content"] = content

        processed_steps.append(step_data)

    # 3. Initialize STEPS
    STEPS = processed_steps
    if ENABLE_SESSION_PERSISTENCE:
        script_dir = pathlib.Path(__file__).resolve().parent
        session_file_path = script_dir / session_file_name
        GLOBAL_SESSION_FILE = session_file_path #
        # ---1. Load Session if exists---
        if session_file_path.exists():
            try:
                with open(session_file_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)

                # 2.1. Sincronizar current_step
                # ensure current_step from session does not exceed STEPS length
                saved_step = session_data.get("current_step", 0)
                current_step = min(saved_step, len(STEPS) - 1)
                logger.debug("Loaded saved_step from session: %d - '%d'", saved_step, current_step)

                # 2.2. Synchronize STEP_EXECUTION_STATUS for the Breadcrumb
                saved_status = session_data.get("steps_status", [])
                for item in saved_status:
                    if item["index"] < len(STEPS):
                        STEP_EXECUTION_STATUS[item["index"]] = item["status"]

                status_message = i18n("session_loaded_message").format(step=current_step + 1)

            except (json.JSONDecodeError, KeyError):
                status_message = i18n("session_corrupted_message")
                # You can rename or delete the corrupt session file here if needed

        else:
            # If no session file exists, start fresh and save initial state
            status_message = i18n("welcome_message")
            save_session(GLOBAL_SESSION_FILE, 0, STEP_EXECUTION_STATUS)

    # 4. Initialization of status_message
    status_message = i18n("welcome_msg")

# 2. Render Header Banner Function (Using Rich)
def render_header(step_index):
    """Draw the banner of the PoC status (the 'Ariadne's thread')."""

    # 2.1. Creating the Breadcrumb Steps
    breadcrumb = []
    for i, step in enumerate(STEPS):
        style = STL_DEFAULT
        if i == step_index:
            style = STL_CURRENT_STEP
        elif i < step_index:
            if STEP_EXECUTION_STATUS.get(i) == "dry":
                # Current Step after a dry run execution
                style = STL_DRYRUN_EXECUTED_STEP
            else:
                style = STL_COMPLETED_STEP

        breadcrumb.append(f"[{style}]{step['name']}[/]")

    # 2.2. Building the Current Breadcrumb Panel Content
    step_info = STEPS[step_index]
    script_content = step_info.get("display_content", step_info.get("command", i18n('no_display_content')))
    #
    panel_content = f"[bold white]{i18n("breadcrumb_base")}[/]\n{' -> '.join(breadcrumb)}\n\n"
    panel_content += f"[bold blue]" + i18n('step_by_step').format(step_num=(step_index + 1),total_steps=len(STEPS)) + ":[/]\n"
    panel_content += f"[yellow]{step_info['description']}[/]\n\n"
    panel_content += f"[bold red]{i18n("command_label")}[/]\n[italic]{script_content}[/]\n"

    # 2.3. Printing the Panel Header
    console.clear() # Clean the screen to redraw dynamically
    console.print(Panel(panel_content,
                        title=i18n("welcome_title"),
                        title_align="center",
                        subtitle=i18n("status_label") + f" {step_info["name"]}",
                        subtitle_align="center",
                        border_style="rgb(0,255,128)",
                        box=rich.box.DOUBLE,
                        height=20,
                        expand=True))

    # Show status message (updated after execution)
    console.print(f"\n[bold]{status_message}[/]")


def get_command_or_script_from_step(step: dict) -> str:
    """Get the command or script to execute from the step definition."""
    global BIN_DIR, FILELOG_PATH
    step_command = step.get("command")
    if not step_command:
        script_name = step.get("script")
        script_params = step.get("params", "")
        script_full_path = BIN_DIR / script_name
        #step_command = f"{script_full_path} {script_params} | tee -a {FILELOG_PATH}"
        step_command = f"{script_full_path} {script_params}"
    #
    return step_command


# 3. Interactive Menu Function using Inquirer
def ask_options(step_index):
    """Show the Next/Previous/Cancel interactive menu."""

    global current_step, status_message
    logger.debug("ask_options called for step_index: '%d' - '%d'", step_index,current_step)
    step_info = STEPS[step_index]
    last_step_index = len(STEPS) - 1
    raw_options = []
    # Building the options dynamically
    if step_index < last_step_index:
        raw_options.append((i18n("next_option"), "next"))
        if step_info.get("can_dryrun", False):
            raw_options.append((i18n("dryrun_option"), "dryrun"))

        if step_info.get("can_go_back",False) and step_index > 0:
            raw_options.append((i18n("previous_option"), "previous"))

    elif step_index == last_step_index:
        raw_options.append((i18n('finish_action'), "finish"))

    raw_options.append((i18n("cancel_option"), "cancel"))

    final_options = []
    for i, (text_action, action_value) in enumerate(raw_options, start=1):
        # Creating the dynamic prefix: "1) " or "2) , ..."
        prefixed_text = f"{i}) {text_action}"
        # Add the action tuple to the final options list
        final_options.append((prefixed_text, action_value))

    # Inquirer Menu Configuration
    questions = [
        inquirer.List(
            'action',
            message=i18n("action_prompt"),
            choices=final_options,
        )
    ]

    try:
        answers = inquirer.prompt(questions)
        action = answers['action']
    except TypeError:
        # User pressed Ctrl+C on the menu
        action = "cancel"

    if action == "next":
        step_command = get_command_or_script_from_step(STEPS[step_index])
        logger.debug("Executing command next --: %s", step_command)
        console.print(f"\n[bold green]{i18n("executing_message")}: {step_command}[/]")
        # Execute the command/script of the current step
        result = subprocess.run(
                [step_command],
                shell=True,
                check=False,
                capture_output=True,
                text=True
                #,executable="/bin/bash"
        )
        logger.debug("Executing command next --: `%s' - %d", result.stdout, result.returncode)
        console.print(f"\nOutput:\n{result.stdout}")
        #time.sleep(5)
        status_message = f"[green]\u2705 " + i18n('step_complete_message').format(
                step_num=step_index + 1,
                step_name=STEPS[step_index]['name']
            ) + "[/]"

        STEP_EXECUTION_STATUS[step_index] = "real"
        current_step += 1

    elif action == "dryrun":
        step_command = get_command_or_script_from_step(STEPS[step_index])
        logger.debug("Executing command dryrun --: %s", step_command)
        # Simulare execute the command of the current step
        console.print(f"\n[bold green]{i18n("label_executing_dryrun")}: {step_command}[/]")
        #
        #time.sleep(2.5)  # Simulate some delay for dry run execution
        status_message = f"[green]\u2705 " + i18n('step_complete_message').format(
                step_num=step_index + 1,
                step_name=STEPS[step_index]['name']
            ) + "[/]"
        STEP_EXECUTION_STATUS[step_index] = "dry"
        current_step += 1
    elif action == "previous":
        status_message = f"[yellow]\u2b05 {i18n("back_step").format(step_index=step_index)}[/]"
        current_step -= 1
    elif action == "finish":
        status_message = f"[yellow]\U0001F389 {i18n("completed_wizard_msg")}[/]"
        current_step += 1
    elif action == "cancel":
        save_session(GLOBAL_SESSION_FILE, step_index, STEP_EXECUTION_STATUS)
        console.print(f"\n[bold red]\u274c {i18n("wizard_cancel_by_user")}[/]")
        sys.exit(0)

    if action in ["next", "dryrun", "previous"]:
        save_session(GLOBAL_SESSION_FILE, current_step, STEP_EXECUTION_STATUS)

# ================== #
# ==== __main__ ==== #
# ================== #
_init_logger()
logger = logging.getLogger(__name__)
BIN_DIR = pathlib.Path(os.getcwd())
logger.info("Init Script: %s", BIN_DIR)

# 4. Main Wizard Loop
if __name__ == '__main__' or __name__ == 'main':
    load_localization(DEFAULT_LANG)
    init_global_variables()
    try:
        while current_step < len(STEPS):
            logger.debug("Main Loop at current_step: '%d'", current_step)
            render_header(current_step)
            ask_options(current_step)

        render_header(len(STEPS) - 1) # Render last step

        console.print(f"\n[bold magenta] \U0001F389 {i18n("completed_wizard_msg")}[/]")

    except KeyboardInterrupt:
        console.print(f"\n[bold red]\u274c {i18n("break_wizard_msg")}[/]")
        sys.exit(0)

    logger.info("End Script: %s",os.getcwd())


# EOF