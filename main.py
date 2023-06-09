#!/usr/bin/env python3

from math import floor, log
from subprocess import check_output
from pathlib import Path
import json
import argparse
import time
import tkinter
from tkinter import ttk
import os


parser = argparse.ArgumentParser(description="Set workspace names")
parser.add_argument("--name-gui", action='store_true', help="Workspace name")
parser.add_argument("--name-cli", type=str, help="Workspace name")
parser.add_argument("--list-gui", action="store_true", help="List workspace names")
parser.add_argument("--no-timeout", action="store_true", help="Don't timeout")
parser.add_argument("--close-all", action="store_true", help="Close all open windows")
args = parser.parse_args()

project_dir = Path(__file__).parent.absolute()
pid_path = project_dir / "pids"
ws_names_path = project_dir / "ws-names.json"
if not ws_names_path.exists():
    json.dump({}, ws_names_path.open("w"))
ws_names = json.load(ws_names_path.open())

gui_time = 600

spaces = check_output(["yabai", "-m", "query", "--spaces"]).decode("utf-8")
active_space = check_output(["yabai", "-m", "query", "--spaces", "--space"]).decode("utf-8")
spaces = json.loads(spaces)
active_space = json.loads(active_space)

def get_name(space):
    uuid = space['uuid']
    display = '' #f"/{space['display']}" if space['display'] != 1 else ''
    if uuid in ws_names:
        name = ws_names[uuid]
        if name == "":
            r = f"{space['index']}{display}"
        else:
            r = f"{space['index']}{display}: {name}"
    else:
        r = f"{space['index']}{display}"

    if space['display'] != 1:
        r = f".{r}"
    else:
        r = f" {r}"
    if uuid == active_space['uuid']:
        r = f"*{r}"
    else:
        r = f" {r}"
    return r

def get_input_name(text_entry):
    ws_names[active_space['uuid']] = text_entry.get()
    json.dump(ws_names, ws_names_path.open("w"), indent=4, sort_keys=True)
    exit()

def do_nothing(*args):
    return "break"

funs = []
for i in range(100):
    funs.append(lambda: os.system(f'yabai -m space --focus {i}'))

def gui():
    win = tkinter.Tk()
    win.overrideredirect(1)
    #win.wm_attributes('-type', 'tooltip')
    win.attributes('-topmost', True)
    win.attributes('-alpha', 0.85)
    def center_window(win):
        w, h, ww, wh = (
            win.winfo_screenwidth(), 
            win.winfo_screenheight(), 
            win.winfo_width(),
            win.winfo_height())
        win.geometry(f"+{int(w//2-ww//2)}+{int(h//2-wh//2)}")

    font = ("Courier", 20)

    style = ttk.Style()
    style.configure("custom.TButton", font=font)

    if args.name_gui:
        label = ttk.Label(None, text=get_name(active_space), font=font)
        label.pack()
        text_entry = ttk.Entry(None, text='', font=font)
        text_entry.focus_set()
        text_entry.bind("<Return>", lambda x: get_input_name(text_entry))
        text_entry.pack()
        center_window(win)
    if args.list_gui or args.name_gui:
        names = [get_name(space) for space in spaces]
        for i, (n,s) in enumerate(zip(names, spaces)):
            idx = s['index']
            def f(idx=idx):
                cmd = f'yabai -m space --focus {idx}'
                os.system(cmd)
                if text_entry.get() != '':
                    get_input_name(text_entry)
                exit(0)
            if idx < 10:
                n = ' ' * (floor(log(len(spaces), 10)) - floor(log(idx, 10))) + n
            label = ttk.Button(win, text=n.ljust(12), command=f, style="custom.TButton")
            label.pack(anchor='w')
        if not args.no_timeout and not args.name_gui:
            win.after(600, exit)
        center_window(win)
        win.mainloop()

def cli(pids):
    if args.close_all:
        for p in pids:
            if p != os.getpid():
                try:
                    os.kill(p, 9)
                except:
                    pass
        pids = []
        with pid_path.open("w") as f:
            json.dump(pids, f)

def main():
    pids = []
    if pid_path.exists():
        pids = json.load(pid_path.open())
    with pid_path.open("w") as f:
        pids.append(os.getpid())
        json.dump(pids, f)

    cli(pids)

    if args.list_gui or args.name_gui:
        gui()

if __name__ == "__main__":
    try:
        main()
    finally:
        pids = []
        if pid_path.exists():
            pids = json.load(pid_path.open())
            if os.getpid() in pids:
                pids.remove(os.getpid())
            with pid_path.open("w") as f:
                json.dump(pids, f)