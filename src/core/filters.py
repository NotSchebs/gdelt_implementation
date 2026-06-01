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
                fips = str(row.get('FIPS 10-4') or row.get('FIPS') or '').strip().upper()
                iso = str(row.get('ISO 3166') or row.get('ISO') or '').strip().upper()
                name = str(row.get('Name') or row.get('name') or '').strip()
                if (fips or iso) and name:
                    countries.append({'fips': fips, 'iso': iso, 'name': name})
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
        self.country_listbox.bind('<<ListboxSelect>>', lambda e: self._update_active_display())
        for c in self.countries:
            # show both ISO and FIPS for clarity: Name (ISO/FIPS)
            iso = c.get('iso','')
            fips = c.get('fips','')
            display = f"{c['name']} ({iso}/{fips})"
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
        self.lang_listbox.bind('<<ListboxSelect>>', lambda e: self._update_active_display())
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
            cb = tk.Checkbutton(right, text=name, variable=var, command=self._update_active_display)
            cb.pack(anchor="w")
            self.group_vars[name] = var

        tk.Button(right, text="Select All Countries", command=self._select_all_countries).pack(fill=tk.X, pady=5)
        tk.Button(right, text="Clear All", command=self._clear_all).pack(fill=tk.X, pady=5)
        tk.Button(right, text="Apply", command=self._apply).pack(fill=tk.X, pady=10)
        tk.Button(right, text="Close", command=self.window.destroy).pack(fill=tk.X)

        # Pre-select initial
        self._restore_initial()

        # Active filters display (bottom) + interactive removal buttons
        self.active_label = tk.Label(frame, text="Active: None", font=("Arial", 10), fg="blue", wraplength=600, justify=tk.LEFT)
        self.active_label.pack(fill=tk.X, padx=5, pady=(10, 2))
        self.active_items_frame = tk.Frame(frame)
        self.active_items_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        self._update_active_display()

    def _select_all_countries(self):
        self.country_listbox.select_set(0, tk.END)
        self._update_active_display()

    def _clear_all(self):
        self.country_listbox.selection_clear(0, tk.END)
        self.lang_listbox.selection_clear(0, tk.END)
        for var in self.group_vars.values():
            var.set(False)
        self._update_active_display()

    def _restore_initial(self):
        # countries as ISO codes
        sel_countries = set([c.upper() for c in self.initial_filters.get('countries', [])])
        for i, c in enumerate(self.countries):
            if c.get('iso') in sel_countries or c.get('fips') in sel_countries or c['name'] in sel_countries:
                self.country_listbox.select_set(i)

        sel_langs = set([l.lower() for l in self.initial_filters.get('languages', [])])
        for i, l in enumerate(self.languages):
            if l['code'].lower() in sel_langs or l['name'].lower() in sel_langs:
                self.lang_listbox.select_set(i)

        for g in self.initial_filters.get('groups', []):
            if g in self.group_vars:
                self.group_vars[g].set(True)

    def _update_active_display(self):
        """Update the active filters display label."""
        # Collect active selections and names
        countries = []
        country_names = []
        for idx in self.country_listbox.curselection():
            item = self.country_listbox.get(idx)
            if '(' in item and item.endswith(')'):
                inner = item.split('(')[-1].strip(')')
                parts = [p.strip() for p in inner.split('/')]
                iso = parts[0] if parts else ''
                fips = parts[1] if len(parts) > 1 and parts[1] else iso
                countries.append(fips)
                country_names.append(item.split('(')[0].strip())

        langs = []
        lang_names = []
        for idx in self.lang_listbox.curselection():
            item = self.lang_listbox.get(idx)
            if '(' in item and item.endswith(')'):
                code = item.split('(')[-1].strip(')')
                langs.append(code)
                lang_names.append(item.split('(')[0].strip())

        groups = [name for name, var in self.group_vars.items() if var.get()]

        # Format display string (show names for readability)
        parts = []
        if country_names:
            parts.append(f"Countries: {', '.join(country_names)}")
        if lang_names:
            parts.append(f"Languages: {', '.join(lang_names)}")
        if groups:
            parts.append(f"Groups: {', '.join(groups)}")

        display_text = " | ".join(parts) if parts else "Active: None"
        self.active_label.config(text=display_text)

        # rebuild interactive active items
        for w in self.active_items_frame.winfo_children():
            w.destroy()

        def make_btn(text, cmd):
            b = tk.Button(self.active_items_frame, text=text, relief=tk.RIDGE, bd=1, padx=4, pady=2, command=cmd)
            b.pack(side=tk.LEFT, padx=2, pady=2)

        for iso in countries:
            make_btn(f"{iso} ×", lambda v=iso: self._remove_active_filter('country', v))
        for code in langs:
            make_btn(f"{code} ×", lambda v=code: self._remove_active_filter('language', v))
        for g in groups:
            make_btn(f"{g} ×", lambda v=g: self._remove_active_filter('group', v))

    def _apply(self):
        # collect selected countries
        selected_countries = []
        country_names = []
        selected_lang_names = []
        for idx in self.country_listbox.curselection():
            item = self.country_listbox.get(idx)
            # extract ISO in parentheses
            if '(' in item and item.endswith(')'):
                inner = item.split('(')[-1].strip(')')
                parts = [p.strip() for p in inner.split('/')]
                iso = parts[0] if parts else ''
                fips = parts[1] if len(parts) > 1 and parts[1] else iso
                selected_countries.append(fips)
                country_names.append(item.split('(')[0].strip())

        selected_langs = []
        for idx in self.lang_listbox.curselection():
            item = self.lang_listbox.get(idx)
            if '(' in item and item.endswith(')'):
                code = item.split('(')[-1].strip(')')
                selected_langs.append(code)
                selected_lang_names.append(item.split('(')[0].strip())

        selected_groups = [name for name, var in self.group_vars.items() if var.get()]

        # expand groups into countries
        # map group ISO codes to FIPS using countries_master
        iso_to_fips = {c.get('iso'): c.get('fips') for c in self.countries_master}
        for g in selected_groups:
            for iso_code in self.groups.get(g, []):
                fips_code = iso_to_fips.get(iso_code, iso_code)
                if fips_code and fips_code not in selected_countries:
                    selected_countries.append(fips_code)

        filters = {
            'countries': selected_countries,
            'country_names': country_names,
            'languages': selected_langs,
            'language_names': selected_lang_names,
            'groups': selected_groups,
        }

        if callable(self.on_apply):
            try:
                self.on_apply(filters)
            finally:
                self.window.destroy()

    def _lang_name_by_code(self, code: str) -> str:
        code = (code or '').lower()
        for l in self.languages:
            if l.get('code','').lower() == code:
                return l.get('name','')
        return code

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
                inner = item.split('(')[-1].strip(')')
                parts = [p.strip() for p in inner.split('/')]
                if parts:
                    sel_isos.add(parts[0])
                    if len(parts) > 1 and parts[1]:
                        sel_isos.add(parts[1])

        self.country_listbox.delete(0, tk.END)
        source = self.countries_master
        for c in source:
            iso = (c.get('iso') or '').strip()
            fips = (c.get('fips') or '').strip()
            display = f"{c.get('name','')} ({iso}/{fips})"
            if (not term
                    or term in c.get('name','').lower()
                    or (iso and term in iso.lower())
                    or (fips and term in fips.lower())):
                self.country_listbox.insert(tk.END, display)
        # re-select preserved
        for i, item in enumerate(self.country_listbox.get(0, tk.END)):
            if '(' in item and item.endswith(')'):
                inner = item.split('(')[-1].strip(')')
                parts = [p.strip() for p in inner.split('/')]
                iso_part = parts[0] if parts else ''
                fips_part = parts[1] if len(parts) > 1 else ''
                if iso_part in sel_isos or fips_part in sel_isos:
                    self.country_listbox.select_set(i)
        self._update_active_display()

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
            # language list only; do not touch country list here

        for i, item in enumerate(self.lang_listbox.get(0, tk.END)):
            if '(' in item and item.endswith(')') and item.split('(')[-1].strip(')') in sel_codes:
                self.lang_listbox.select_set(i)
        self._update_active_display()

    def _remove_active_filter(self, filter_type: str, value: str):
        """Remove a single active filter from the UI and update display."""
        if filter_type == 'country':
            # find item in listbox that ends with (ISO)
            for i, item in enumerate(self.country_listbox.get(0, tk.END)):
                if item.strip().endswith(f"({value})"):
                    self.country_listbox.selection_clear(i)
        elif filter_type == 'language':
            for i, item in enumerate(self.lang_listbox.get(0, tk.END)):
                if item.strip().endswith(f"({value})"):
                    self.lang_listbox.selection_clear(i)
        elif filter_type == 'group':
            if value in self.group_vars:
                self.group_vars[value].set(False)

        # refresh display
        self._update_active_display()