import tkinter as tk
from tkinter import ttk
import pandas as pd
import os
from typing import Callable, Dict, List


class FiltersWindow:
    """A popup to select country, language, and predefined group filters.

    Usage: FiltersWindow(parent, initial_filters, on_apply)
    - `initial_filters` is a dict with keys: countries (list), languages (list), groups (list)
    - `on_apply` is a callable(filters_dict) invoked when user applies selections.
    """

    FILTERS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'Filters')

    def __init__(self, parent, initial_filters: Dict = None, on_apply: Callable = None):
        self.parent = parent
        self.initial_filters = initial_filters or {}
        self.on_apply = on_apply

        self.window = tk.Toplevel(parent)
        self.window.title("Filters")
        self.window.geometry("700x500")
        self.window.transient(parent)
        self.window.grab_set()

        # Load lists (keep masters for filtering)
        self.countries = self._load_countries()
        self.countries_master = list(self.countries)
        self.languages = self._load_languages()
        self.languages_master = list(self.languages)

        # Groupings: continents and common country groups
        self.groups = {
            "G7": ["CA", "FR", "DE", "IT", "JP", "GB", "US"],
            "G20": ["AR","AU","BR","CA","CN","FR","DE","IN","ID","IT","JP","MX","RU","SA","ZA","KR","TR","GB","US"],
            "BRICS": ["BR","RU","IN","CN","ZA"],
            "EU (sample)": ["FR", "DE", "IT", "ES", "NL", "BE", "SE", "PL"],
            "Europe": ["GB","FR","DE","IT","ES","NL","BE","SE","PL","GR","PT","IE","AT","CH","CZ","HU","RO","BG","DK","FI","NO","SK","SI","HR","LT","LV","EE","LU","MT","IS","AD","LI","MC","SM","VA","BA","AL","MK","ME","RS"],
            "Asia": ["CN","JP","IN","KR","ID","PK","BD","IR","SA","TR","TH","VN","MY","PH","AE","IL","IQ","KZ","UZ","SG","LK","NP","MM","KH"],
            "Africa": ["NG","EG","ZA","DZ","MA","KE","ET","GH","TZ","CM","UG","SN","CI","MZ","ZM","ZW"],
            "North America": ["US","CA","MX"],
            "South America": ["BR","AR","CO","PE","VE","CL","EC","BO","UY","PY","SR","GY"],
            "Oceania": ["AU","NZ","PG","FJ","SB","VU"],
            "Antarctica": ["AQ"],
        }

        self._build_ui()

    def _load_countries(self) -> List[Dict]:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Filters'))
        path = os.path.join(base, 'country_codes.csv')
        try:
            df = pd.read_csv(path)
            # Normalize headers
            df.columns = [c.strip().strip('"') for c in df.columns]
            countries = []
            for _, row in df.iterrows():
                iso = str(row.get('ISO 3166') or row.get('ISO') or '').strip().upper()
                name = str(row.get('Name') or row.get('name') or '').strip()
                if iso and name:
                    countries.append({'iso': iso, 'name': name})
            # sort
            countries = sorted(countries, key=lambda x: x['name'])
            return countries
        except Exception:
            return []

    def _load_languages(self) -> List[Dict]:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Filters'))
        path = os.path.join(base, 'language_codes.csv')
        try:
            df = pd.read_csv(path, header=0)
            langs = []
            for _, row in df.iterrows():
                code = str(row.get('639-1') or row.get('639_1') or '').strip()
                name = str(row.get('name') or row.get('Name') or row.get('name') or '').strip()
                if code and name:
                    langs.append({'code': code, 'name': name})
            langs = sorted(langs, key=lambda x: x['name'])
            return langs
        except Exception:
            return []

    def _build_ui(self):
        frame = tk.Frame(self.window, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Countries listbox
        left = tk.Frame(frame)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(left, text="Countries", font=("Arial", 12, "bold")).pack(anchor="w")
        # Search box for countries
        self.country_search = tk.Entry(left)
        self.country_search.pack(fill=tk.X, padx=5)
        self.country_search.insert(0, "Search countries")
        self.country_search.bind('<FocusIn>', lambda e: self._clear_placeholder(self.country_search, 'Search countries'))
        self.country_search.bind('<KeyRelease>', lambda e: self._filter_countries(self.country_search.get()))

        self.country_listbox = tk.Listbox(left, selectmode=tk.MULTIPLE)
        self.country_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        for c in self.countries:
            display = f"{c['name']} ({c['iso']})"
            self.country_listbox.insert(tk.END, display)

        # Languages listbox
        mid = tk.Frame(frame)
        mid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(mid, text="Languages", font=("Arial", 12, "bold")).pack(anchor="w")
        # Search box for languages
        self.lang_search = tk.Entry(mid)
        self.lang_search.pack(fill=tk.X, padx=5)
        self.lang_search.insert(0, "Search languages")
        self.lang_search.bind('<FocusIn>', lambda e: self._clear_placeholder(self.lang_search, 'Search languages'))
        self.lang_search.bind('<KeyRelease>', lambda e: self._filter_languages(self.lang_search.get()))

        self.lang_listbox = tk.Listbox(mid, selectmode=tk.MULTIPLE)
        self.lang_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        for l in self.languages:
            display = f"{l['name']} ({l['code']})"
            self.lang_listbox.insert(tk.END, display)

        # Groups and actions
        right = tk.Frame(frame)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(right, text="Groups", font=("Arial", 12, "bold")).pack(anchor="w")
        self.group_vars = {}
        for name in self.groups.keys():
            var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(right, text=name, variable=var)
            cb.pack(anchor="w")
            self.group_vars[name] = var

        tk.Button(right, text="Select All Countries", command=self._select_all_countries).pack(fill=tk.X, pady=5)
        tk.Button(right, text="Clear All", command=self._clear_all).pack(fill=tk.X, pady=5)
        tk.Button(right, text="Apply", command=self._apply).pack(fill=tk.X, pady=10)
        tk.Button(right, text="Close", command=self.window.destroy).pack(fill=tk.X)

        # Pre-select initial
        self._restore_initial()

    def _select_all_countries(self):
        self.country_listbox.select_set(0, tk.END)

    def _clear_all(self):
        self.country_listbox.selection_clear(0, tk.END)
        self.lang_listbox.selection_clear(0, tk.END)
        for var in self.group_vars.values():
            var.set(False)

    def _restore_initial(self):
        # countries as ISO codes
        sel_countries = set([c.upper() for c in self.initial_filters.get('countries', [])])
        for i, c in enumerate(self.countries):
            if c['iso'] in sel_countries or c['name'] in sel_countries:
                self.country_listbox.select_set(i)

        sel_langs = set([l.lower() for l in self.initial_filters.get('languages', [])])
        for i, l in enumerate(self.languages):
            if l['code'].lower() in sel_langs or l['name'].lower() in sel_langs:
                self.lang_listbox.select_set(i)

        for g in self.initial_filters.get('groups', []):
            if g in self.group_vars:
                self.group_vars[g].set(True)

    def _apply(self):
        # collect selected countries
        selected_countries = []
        for idx in self.country_listbox.curselection():
            item = self.country_listbox.get(idx)
            # extract ISO in parentheses
            if '(' in item and item.endswith(')'):
                iso = item.split('(')[-1].strip(')')
                selected_countries.append(iso)

        selected_langs = []
        for idx in self.lang_listbox.curselection():
            item = self.lang_listbox.get(idx)
            if '(' in item and item.endswith(')'):
                code = item.split('(')[-1].strip(')')
                selected_langs.append(code)

        selected_groups = [name for name, var in self.group_vars.items() if var.get()]

        # expand groups into countries
        for g in selected_groups:
            for iso in self.groups.get(g, []):
                if iso not in selected_countries:
                    selected_countries.append(iso)

        filters = {
            'countries': selected_countries,
            'languages': selected_langs,
            'groups': selected_groups,
        }

        if callable(self.on_apply):
            try:
                self.on_apply(filters)
            finally:
                self.window.destroy()

    def _clear_placeholder(self, entry: tk.Entry, placeholder: str):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)

    def _filter_countries(self, term: str):
        term = term.strip().lower()
        # preserve current selection ISO codes
        sel_isos = set()
        for idx in self.country_listbox.curselection():
            item = self.country_listbox.get(idx)
            if '(' in item and item.endswith(')'):
                sel_isos.add(item.split('(')[-1].strip(')'))

        self.country_listbox.delete(0, tk.END)
        source = self.countries_master
        for c in source:
            display = f"{c['name']} ({c['iso']})"
            if not term or term in c['name'].lower() or term in c['iso'].lower():
                self.country_listbox.insert(tk.END, display)
        # re-select preserved
        for i, item in enumerate(self.country_listbox.get(0, tk.END)):
            if '(' in item and item.endswith(')') and item.split('(')[-1].strip(')') in sel_isos:
                self.country_listbox.select_set(i)

    def _filter_languages(self, term: str):
        term = term.strip().lower()
        sel_codes = set()
        for idx in self.lang_listbox.curselection():
            item = self.lang_listbox.get(idx)
            if '(' in item and item.endswith(')'):
                sel_codes.add(item.split('(')[-1].strip(')'))

        self.lang_listbox.delete(0, tk.END)
        source = self.languages_master
        for l in source:
            display = f"{l['name']} ({l['code']})"
            if not term or term in l['name'].lower() or term in l['code'].lower():
                self.lang_listbox.insert(tk.END, display)

        for i, item in enumerate(self.lang_listbox.get(0, tk.END)):
            if '(' in item and item.endswith(')') and item.split('(')[-1].strip(')') in sel_codes:
                self.lang_listbox.select_set(i)