import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import json
import os
import copy # For deepcopy in undo/redo
from collections import defaultdict # For counting duplicates

class JsonlEditorAppTk:
    MAX_UNDO_LEVELS = 50
    KEY_INSTRUCTION = "instruction"
    KEY_INPUT = "input"
    KEY_OUTPUT = "output"

    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Tkinter JSONL Editor (with Duplicate Input Detection)") # Updated title
        self.root.geometry("1000x700")

        # --- Data and State ---
        self.current_file_path = None
        self.data = []
        self.selected_index = -1 # Index in self.data

        self.undo_stack = []
        self.redo_stack = []

        self.is_dirty_file = False
        self.ui_text_field_is_dirty = False

        # --- Duplicate Detection State ---
        self.duplicate_input_indices = set() # Store indices of items with duplicate inputs
        self.input_counts = defaultdict(int) # To count occurrences of each input string

        # --- Theme Management ---
        self.themes = {
            "light": {
                "bg": "#f0f0f0", "fg": "black", "button_bg": "#e0e0e0", "button_fg": "black",
                "button_active_bg": "#d0d0d0", "text_bg": "white", "text_fg": "black",
                "text_select_bg": "#0078d7", "text_select_fg": "white", "listbox_bg": "white",
                "listbox_fg": "black", "listbox_select_bg": "#0078d7", "listbox_select_fg": "white",
                "disabled_fg": "#a0a0a0", "status_bar_bg": "#e0e0e0", "status_bar_fg": "black",
                "duplicate_item_bg": "#ffe0e0", # Light red for duplicate background in light theme
                "duplicate_item_fg": "black",  #
            },
            "dark": {
                "bg": "#2e2e2e", "fg": "white", "button_bg": "#555555", "button_fg": "white",
                "button_active_bg": "#6a6a6a", "text_bg": "#3c3c3c", "text_fg": "white",
                "text_select_bg": "#005f87", "text_select_fg": "white", "listbox_bg": "#3c3c3c",
                "listbox_fg": "white", "listbox_select_bg": "#005f87", "listbox_select_fg": "white",
                "disabled_fg": "#777777", "status_bar_bg": "#404040", "status_bar_fg": "white",
                "duplicate_item_bg": "#703030", # Darker red for duplicate background in dark theme
                "duplicate_item_fg": "white", #
            }
        }
        self.current_theme_name = "light"

        self._build_ui()
        self.apply_theme(self.current_theme_name)
        self._update_ui_element_states()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)


    def _build_ui(self):
        # ... (rest of your _build_ui method remains largely the same) ...
        # Top Frame
        self.top_frame = tk.Frame(self.root, pady=10)
        self.top_frame.pack(fill=tk.X)

        self.new_button = tk.Button(self.top_frame, text="New File", command=self.new_file)
        self.new_button.pack(side=tk.LEFT, padx=5)
        self.load_button = tk.Button(self.top_frame, text="Load JSONL", command=self.load_file)
        self.load_button.pack(side=tk.LEFT, padx=5)
        self.save_button = tk.Button(self.top_frame, text="Save", command=self.save_data_to_file_manual)
        self.save_button.pack(side=tk.LEFT, padx=5)
        self.save_as_button = tk.Button(self.top_frame, text="Save As...", command=self.save_data_as)
        self.save_as_button.pack(side=tk.LEFT, padx=5)
        self.undo_button = tk.Button(self.top_frame, text="Undo", command=self.undo_action)
        self.undo_button.pack(side=tk.LEFT, padx=5)
        self.redo_button = tk.Button(self.top_frame, text="Redo", command=self.redo_action)
        self.redo_button.pack(side=tk.LEFT, padx=5)
        self.theme_button = tk.Button(self.top_frame, text="Toggle Theme", command=self.toggle_theme)
        self.theme_button.pack(side=tk.LEFT, padx=5)
        self.file_label = tk.Label(self.top_frame, text="No file loaded.")
        self.file_label.pack(side=tk.LEFT, padx=10, expand=True, anchor="w")

        # Main Frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left: Listbox
        self.list_frame = tk.Frame(self.main_frame, width=300)
        self.list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        self.list_frame.pack_propagate(False)
        self.listbox_label = tk.Label(self.list_frame, text="JSONL Items (Duplicates Highlighted):") # Updated Label
        self.listbox_label.pack(anchor=tk.W)
        self.listbox_scrollbar = tk.Scrollbar(self.list_frame, orient=tk.VERTICAL)
        self.listbox = tk.Listbox(self.list_frame, yscrollcommand=self.listbox_scrollbar.set, exportselection=False)
        self.listbox_scrollbar.config(command=self.listbox.yview)
        self.listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.on_list_item_select)

        self.item_button_frame = tk.Frame(self.list_frame)
        self.item_button_frame.pack(fill=tk.X, pady=5)
        self.add_item_button = tk.Button(self.item_button_frame, text="Add Item", command=self.add_item)
        self.add_item_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,2))
        self.delete_item_button = tk.Button(self.item_button_frame, text="Delete Item", command=self.delete_item)
        self.delete_item_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2,0))

        # Right: Text areas
        self.details_frame = tk.Frame(self.main_frame)
        self.details_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.instruction_label = tk.Label(self.details_frame, text=f"{self.KEY_INSTRUCTION.capitalize()}:")
        self.instruction_label.pack(anchor=tk.W)
        self.instruction_text = scrolledtext.ScrolledText(self.details_frame, height=8, wrap=tk.WORD)
        self.instruction_text.pack(fill=tk.BOTH, expand=True, pady=(0,10))
        self.instruction_text.bind("<FocusOut>", self.on_text_edit_focus_out)
        self.instruction_text.bind("<KeyRelease>", lambda e: self.mark_ui_field_dirty())

        self.input_label = tk.Label(self.details_frame, text=f"{self.KEY_INPUT.capitalize()}:")
        self.input_label.pack(anchor=tk.W)
        self.input_text = scrolledtext.ScrolledText(self.details_frame, height=8, wrap=tk.WORD)
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(0,10))
        self.input_text.bind("<FocusOut>", self.on_text_edit_focus_out)
        self.input_text.bind("<KeyRelease>", lambda e: self.mark_ui_field_dirty())

        self.output_label = tk.Label(self.details_frame, text=f"{self.KEY_OUTPUT.capitalize()}:")
        self.output_label.pack(anchor=tk.W)
        self.output_text = scrolledtext.ScrolledText(self.details_frame, height=8, wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.bind("<FocusOut>", self.on_text_edit_focus_out)
        self.output_text.bind("<KeyRelease>", lambda e: self.mark_ui_field_dirty())

        # Status bar
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.themeable_widgets = [
            self.root, self.top_frame, self.main_frame, self.list_frame, self.item_button_frame, self.details_frame,
            self.new_button, self.load_button, self.save_button, self.save_as_button, self.undo_button, self.redo_button,
            self.theme_button, self.add_item_button, self.delete_item_button,
            self.file_label, self.listbox_label, self.instruction_label, self.input_label, self.output_label,
            self.status_bar, self.listbox,
            self.instruction_text, self.input_text, self.output_text
        ]
        self.root.bind_all("<Control-n>", lambda e: self.new_file())
        self.root.bind_all("<Control-o>", lambda e: self.load_file())
        self.root.bind_all("<Control-s>", lambda e: self.save_data_to_file_manual())
        self.root.bind_all("<Control-Shift-S>", lambda e: self.save_data_as())
        self.root.bind_all("<Control-z>", lambda e: self.undo_action())
        self.root.bind_all("<Control-y>", lambda e: self.redo_action())


    def _on_closing(self):
        # ... (same as before) ...
        self._commit_ui_edits_if_any()
        if self.is_dirty_file:
            response = messagebox.askyesnocancel("Unsaved Changes", "You have unsaved changes. Save before closing?")
            if response is True:
                if not self.save_data_to_file(autosave=False):
                    return
            elif response is None:
                return
        self.root.destroy()

    # --- Theme Management ---
    def toggle_theme(self):
        # ... (same as before) ...
        self.current_theme_name = "dark" if self.current_theme_name == "light" else "light"
        self.apply_theme(self.current_theme_name)

    def apply_theme(self, theme_name):
        # ... (same as before, but we'll use duplicate_item_bg in populate_listbox) ...
        colors = self.themes[theme_name]
        self.root.configure(bg=colors["bg"])

        for widget in self.themeable_widgets:
            widget_type = widget.winfo_class()
            try:
                if widget_type in ["Frame", "Toplevel"]:
                    widget.configure(bg=colors["bg"])
                elif widget_type == "Label":
                    widget.configure(bg=colors["bg"], fg=colors["fg"])
                    if widget == self.status_bar:
                         widget.configure(bg=colors["status_bar_bg"], fg=colors["status_bar_fg"])
                elif widget_type == "Button":
                    widget.configure(
                        bg=colors["button_bg"], fg=colors["button_fg"],
                        activebackground=colors["button_active_bg"],
                        activeforeground=colors["button_fg"],
                        disabledforeground=colors["disabled_fg"]
                    )
                elif widget_type == "Listbox":
                    widget.configure(
                        bg=colors["listbox_bg"], fg=colors["listbox_fg"],
                        selectbackground=colors["listbox_select_bg"],
                        selectforeground=colors["listbox_select_fg"]
                        # itemcget for individual item colors will be handled in populate_listbox
                    )
                elif widget_type == "ScrolledText":
                    text_widget = widget.component('text')
                    text_widget.configure(
                        background=colors["text_bg"], foreground=colors["text_fg"],
                        selectbackground=colors["text_select_bg"],
                        selectforeground=colors["text_select_fg"],
                        insertbackground=colors["text_fg"],
                        inactiveselectbackground=colors["text_select_bg"]
                    )
            except tk.TclError as e:
                print(f"Warning: Could not apply theme to {widget_type} ({widget}): {e}")
        
        # Re-apply item-specific colors if listbox is populated
        self.populate_listbox(force_refresh_colors=True) # Added force_refresh_colors


    # --- Undo/Redo Logic ---
    def _push_state_to_undo(self, description="Action"):
        # ... (same as before) ...
        current_data_snapshot = copy.deepcopy(self.data)
        current_selected_index_snapshot = self.selected_index
        if self.undo_stack:
            last_data, last_idx, _ = self.undo_stack[-1]
            if last_data == current_data_snapshot and last_idx == current_selected_index_snapshot:
                return

        if len(self.undo_stack) >= self.MAX_UNDO_LEVELS:
            self.undo_stack.pop(0)

        self.undo_stack.append((current_data_snapshot, current_selected_index_snapshot, description))
        self.redo_stack.clear()
        self._update_undo_redo_buttons_state()

    def _restore_state_from_stack(self, data_snapshot, selected_index_snapshot, action_description="Restored"):
        # ... (same as before, but will call populate_listbox which now handles dupes) ...
        self.data = copy.deepcopy(data_snapshot)
        self.selected_index = selected_index_snapshot

        self.populate_listbox() # This will re-evaluate duplicates

        if 0 <= self.selected_index < len(self.data):
            self._load_item_data_to_fields(self.data[self.selected_index])
        elif self.data:
            pass
        else:
            self.clear_text_fields()

        self.ui_text_field_is_dirty = False
        self.is_dirty_file = True
        self._update_ui_element_states()
        self._update_undo_redo_buttons_state()
        self._set_status(f"{action_description}. File has unsaved changes.")
        # self.apply_theme(self.current_theme_name) # populate_listbox now handles its colors


    def undo_action(self):
        # ... (same as before) ...
        if not self.undo_stack: return
        self._commit_ui_edits_if_any()

        current_state_for_redo = (copy.deepcopy(self.data), self.selected_index, "Redo State")
        self.redo_stack.append(current_state_for_redo)

        data_to_restore, idx_to_restore, desc = self.undo_stack.pop()
        self._restore_state_from_stack(data_to_restore, idx_to_restore, f"Undo: {desc}")


    def redo_action(self):
        # ... (same as before) ...
        if not self.redo_stack: return

        current_state_for_undo = (copy.deepcopy(self.data), self.selected_index, "Undo State after Redo")

        data_to_restore, idx_to_restore, desc_from_redo = self.redo_stack.pop()
        self.undo_stack.append((current_state_for_undo[0], current_state_for_undo[1], f"State before Redo of '{desc_from_redo.replace('Redo State', 'Action')}'"))

        self._restore_state_from_stack(data_to_restore, idx_to_restore, f"Redo: {desc_from_redo.replace('Redo State', 'Action')}")

    def _update_undo_redo_buttons_state(self):
        # ... (same as before) ...
        self.undo_button.config(state=tk.NORMAL if self.undo_stack else tk.DISABLED)
        self.redo_button.config(state=tk.NORMAL if self.redo_stack else tk.DISABLED)

    # --- UI Control and State Management ---
    def _set_status(self, message):
        # ... (same as before) ...
        filename_prefix = f"{os.path.basename(self.current_file_path)}{'*' if self.is_dirty_file else ''} - " if self.current_file_path else ""
        if not self.current_file_path and self.data and self.is_dirty_file: # For new, unsaved file with data
            filename_prefix = f"Untitled.jsonl* - "
        self.status_bar.config(text=f"{filename_prefix}{message}")


    def _update_ui_element_states(self):
        # ... (same as before) ...
        file_context_exists = bool(self.current_file_path or self.data)
        data_exists = bool(self.data)
        item_is_selected = (0 <= self.selected_index < len(self.data))

        self.save_button.config(state=tk.NORMAL if self.current_file_path and self.is_dirty_file else tk.DISABLED)
        self.save_as_button.config(state=tk.NORMAL if data_exists or self.current_file_path else tk.DISABLED)
        self.add_item_button.config(state=tk.NORMAL)
        self.delete_item_button.config(state=tk.NORMAL if item_is_selected else tk.DISABLED)

        text_fields_state = tk.NORMAL if item_is_selected else tk.DISABLED
        for widget in [self.instruction_text, self.input_text, self.output_text]:
            if widget.cget('state') != text_fields_state: # Avoid redundant config calls
                widget.config(state=text_fields_state)

        self._update_undo_redo_buttons_state()


    def mark_ui_field_dirty(self):
        # ... (same as before) ...
        if self.selected_index != -1 and self.instruction_text.cget("state") == tk.NORMAL:
             self.ui_text_field_is_dirty = True
             self.is_dirty_file = True
             self._update_ui_element_states()
             self._set_status(f"Editing Item {self.selected_index + 1}. Changes not saved.")

    # --- Duplicate Detection ---
    def _find_duplicate_inputs(self):
        self.input_counts.clear()
        self.duplicate_input_indices.clear()
        temp_input_indices = defaultdict(list) # Store all indices for each input

        for i, item_data in enumerate(self.data):
            input_val = item_data.get(self.KEY_INPUT, "").strip() # Normalize by stripping
            if input_val: # Only consider non-empty inputs for duplication
                self.input_counts[input_val] += 1
                temp_input_indices[input_val].append(i)

        for input_val, count in self.input_counts.items():
            if count > 1:
                for index in temp_input_indices[input_val]:
                    self.duplicate_input_indices.add(index)
        # print(f"DEBUG: Duplicate indices: {self.duplicate_input_indices}")


    # --- File Operations ---
    def new_file(self):
        # ... (same as before, but populate_listbox will handle dupe detection) ...
        self._commit_ui_edits_if_any()
        if self.is_dirty_file:
            if not messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Discard them and create a new file?"):
                return

        self.clear_all_app_state(is_new_file=True)
        self.file_label.config(text="Untitled.jsonl")
        self.is_dirty_file = False
        self._set_status("New file created. Add items or load data.")
        self._push_state_to_undo("New Empty File")
        self._update_ui_element_states()
        self._find_duplicate_inputs() # Check for duplicates in (empty) data
        self.populate_listbox() # Refresh listbox


    def load_file(self):
        # ... (same as before, but populate_listbox will handle dupe detection) ...
        self._commit_ui_edits_if_any()
        if self.is_dirty_file:
            if messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Save them before loading a new file?"):
                if not self.save_data_to_file(autosave=False): return

        filepath = filedialog.askopenfilename(
            defaultextension=".jsonl",
            filetypes=[("JSONL files", "*.jsonl"), ("All files", "*.*")]
        )
        if not filepath: return

        self.current_file_path = filepath
        loaded_data = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    line = line.strip()
                    if line:
                        try: loaded_data.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            messagebox.showerror("JSON Error", f"Error parsing JSON on line {line_num+1}: {e}\n\n'{line[:100]}{'...' if len(line)>100 else ''}'")
                            self.clear_all_app_state()
                            return

            self.data = loaded_data
            self.undo_stack.clear()
            self.redo_stack.clear()
            self._push_state_to_undo("Initial Load")

            self.populate_listbox() # This will now also color duplicates
            self.file_label.config(text=os.path.basename(filepath))
            self._set_status(f"Loaded {len(self.data)} items from {os.path.basename(filepath)}")

            if not self.data:
                self.clear_text_fields()

            self.is_dirty_file = False
            self.ui_text_field_is_dirty = False
            self._update_ui_element_states()

        except Exception as e:
            messagebox.showerror("Error loading file", str(e))
            self.clear_all_app_state()


    def save_data_to_file_manual(self):
        # ... (same as before) ...
        self._commit_ui_edits_if_any()
        if not self.current_file_path:
            self.save_data_as()
        else:
            self.save_data_to_file(autosave=False)


    def save_data_to_file(self, autosave=False):
        # ... (same as before) ...
        if not self.current_file_path:
            if not autosave:
                return self.save_data_as()
            return False

        if not self.data and not autosave:
            if not messagebox.askyesno("Empty Data", "The document is empty. Save an empty file?"):
                return False

        try:
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                for item in self.data: f.write(json.dumps(item) + '\n')

            self._set_status(f"{'Autosaved' if autosave else 'Saved'} to {os.path.basename(self.current_file_path)}")
            self.is_dirty_file = False
            self.file_label.config(text=os.path.basename(self.current_file_path))
            self._update_ui_element_states()
            return True
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save file: {e}")
            return False


    def save_data_as(self):
        # ... (same as before) ...
        self._commit_ui_edits_if_any()
        if not self.data and not self.current_file_path :
             if not messagebox.askyesno("Empty Data", "The document is empty. Still want to 'Save As'?"):
                return False

        initial_filename = os.path.basename(self.current_file_path) if self.current_file_path else "untitled.jsonl"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".jsonl",
            filetypes=[("JSONL files", "*.jsonl"), ("All files", "*.*")],
            initialfile=initial_filename
        )
        if not filepath: return False

        self.current_file_path = filepath
        if self.save_data_to_file(autosave=False):
            self.file_label.config(text=os.path.basename(self.current_file_path))
            self.is_dirty_file = False
            self._update_ui_element_states()
            return True
        return False

    # --- Listbox Handling ---
    def populate_listbox(self, force_refresh_colors=False): # Added force_refresh_colors
        current_selection_val = None
        if self.listbox.curselection():
            current_selection_val = self.listbox.get(self.listbox.curselection()[0])

        # Only re-find duplicates if data actually changed or forced
        # This is tricky if only one item's input changed.
        # For simplicity, always re-find on populate, or make it more granular.
        # If 'force_refresh_colors' is true, it implies a theme change, so don't need to re-find dups.
        if not force_refresh_colors:
            self._find_duplicate_inputs() # Detect duplicates before populating

        self.listbox.delete(0, tk.END)
        colors = self.themes[self.current_theme_name]

        for i, item_data in enumerate(self.data):
            preview_key = item_data.get(self.KEY_INSTRUCTION, item_data.get(self.KEY_INPUT, item_data.get(self.KEY_OUTPUT, 'No preview')))
            preview = str(preview_key)[:50].replace('\n', ' ') + "..."
            display_text = f"Item {i+1}: {preview}"

            self.listbox.insert(tk.END, display_text)
            if i in self.duplicate_input_indices:
                self.listbox.itemconfig(i, {'bg': colors["duplicate_item_bg"], 'fg': colors["duplicate_item_fg"]})
            else: # Explicitly set non-duplicate colors
                self.listbox.itemconfig(i, {'bg': colors["listbox_bg"], 'fg': colors["listbox_fg"]})


        if current_selection_val: # Try to reselect if possible
            try:
                idx_to_reselect = self.listbox.get(0, "end").index(current_selection_val)
                self.selected_index = idx_to_reselect
            except ValueError: # Item no longer exists or text changed
                self.selected_index = -1 # Fallback
        
        if 0 <= self.selected_index < self.listbox.size():
            self.listbox.selection_set(self.selected_index)
            self.listbox.see(self.selected_index)
            self.listbox.activate(self.selected_index)
            # If this selection is new or forced, on_list_item_select will handle data loading.
        elif self.listbox.size() > 0:
            self.selected_index = 0
            self.listbox.selection_set(0)
            self.listbox.see(0)
            self.listbox.activate(0)
            # Trigger selection event if data exists and first item is auto-selected
            self.root.after_idle(lambda: self.on_list_item_select(None)) # Simulate event
        else:
            self.selected_index = -1
            self.clear_text_fields()

        self._update_ui_element_states()


    def on_list_item_select(self, event):
        # ... (same as before) ...
        # Important: _commit_ui_edits_if_any may trigger populate_listbox if input changed
        # Need to be careful about re-entrancy or infinite loops.
        # Consider a flag to prevent re-entry if on_list_item_select is called from _commit.
        
        if event is not None: # Only commit if it's a user-driven selection
             self._commit_ui_edits_if_any()

        selection = self.listbox.curselection()
        if not selection:
            if not self.data:
                self.selected_index = -1
                self.clear_text_fields()
            self._update_ui_element_states()
            return

        new_idx = selection[0]

        if new_idx == self.selected_index and event is not None:
            self._update_ui_element_states()
            return

        self.selected_index = new_idx
        if not (0 <= self.selected_index < len(self.data)):
            self.selected_index = -1
            self.clear_text_fields()
            self._update_ui_element_states()
            return

        self._load_item_data_to_fields(self.data[self.selected_index])
        self._set_status(f"Displaying Item {self.selected_index + 1} of {len(self.data)}")
        self.ui_text_field_is_dirty = False
        self._update_ui_element_states()


    # --- Item Data and Text Field Handling ---
    def _load_item_data_to_fields(self, item_data):
        # ... (same as before) ...
        self._set_text_widget_content(self.instruction_text, item_data.get(self.KEY_INSTRUCTION, ''))
        self._set_text_widget_content(self.input_text, item_data.get(self.KEY_INPUT, ''))
        self._set_text_widget_content(self.output_text, item_data.get(self.KEY_OUTPUT, ''))

    def _set_text_widget_content(self, text_widget, content):
        # ... (same as before) ...
        original_state = text_widget.cget("state")
        if original_state == tk.DISABLED:
            text_widget.config(state=tk.NORMAL)

        text_widget.delete('1.0', tk.END)
        text_widget.insert('1.0', str(content) if content is not None else "")

        if original_state == tk.DISABLED:
             text_widget.config(state=tk.DISABLED)

    def clear_text_fields(self):
        # ... (same as before) ...
        self._set_text_widget_content(self.instruction_text, "")
        self._set_text_widget_content(self.input_text, "")
        self._set_text_widget_content(self.output_text, "")

    def clear_all_app_state(self, is_new_file=False):
        # ... (same as before, but populate_listbox will handle dupe detection) ...
        self.current_file_path = None
        self.data = []
        self.selected_index = -1

        self.listbox.delete(0, tk.END)
        self.clear_text_fields()

        if not is_new_file:
            self.file_label.config(text="No file loaded.")
            self._set_status("Ready")

        self.is_dirty_file = False
        self.ui_text_field_is_dirty = False

        self.undo_stack.clear()
        self.redo_stack.clear()
        self._update_ui_element_states()
        self._find_duplicate_inputs() # Clear duplicates for new state
        # self.populate_listbox() # Not needed here as listbox is already cleared


    def _commit_ui_edits_if_any(self):
        if self.ui_text_field_is_dirty and self.selected_index != -1 and \
           0 <= self.selected_index < len(self.data):
            self._push_state_to_undo(f"Edit Item {self.selected_index + 1}")

            if self.update_current_item_from_text_fields(): # This updates self.data
                self._find_duplicate_inputs() # Re-check duplicates after edit
                self.populate_listbox() # Refresh listbox to show new dupe status
                pass
            self.ui_text_field_is_dirty = False
            self._update_ui_element_states()


    def on_text_edit_focus_out(self, event):
        # ... (same as before, _commit_ui_edits_if_any now handles dupe re-check) ...
        self._commit_ui_edits_if_any()
        if self.is_dirty_file and self.current_file_path:
            self.save_data_to_file(autosave=True)

    def update_current_item_from_text_fields(self):
        # ... (same as before) ...
        # This method now doesn't call populate_listbox directly.
        # The caller (_commit_ui_edits_if_any) will handle it.
        if not (0 <= self.selected_index < len(self.data)): return False

        item = self.data[self.selected_index]
        updated = False
        # Check if the input field itself has changed before re-evaluating duplicates
        old_input_val = item.get(self.KEY_INPUT, "").strip()

        new_vals = {
            self.KEY_INSTRUCTION: self.instruction_text.get('1.0', tk.END).strip(),
            self.KEY_INPUT: self.input_text.get('1.0', tk.END).strip(),
            self.KEY_OUTPUT: self.output_text.get('1.0', tk.END).strip()
        }
        new_input_val = new_vals[self.KEY_INPUT]

        for key, new_val in new_vals.items():
            if item.get(key, "") != new_val:
                item[key] = new_val
                updated = True

        if updated:
            self.is_dirty_file = True
            # Preview update in listbox is now handled by populate_listbox in the caller
            if old_input_val != new_input_val: # If input changed, dupe status might change
                return True # Signal to caller that dupe check is needed
        return updated


    # --- Item Manipulation ---
    def add_item(self):
        # ... (same as before, but populate_listbox will handle dupe detection) ...
        self._commit_ui_edits_if_any()
        self._push_state_to_undo("Add Item")

        new_item = {self.KEY_INSTRUCTION: "New instruction", self.KEY_INPUT: "", self.KEY_OUTPUT: ""}
        insert_at = self.selected_index + 1 if self.selected_index != -1 and self.selected_index < len(self.data) else len(self.data)
        self.data.insert(insert_at, new_item)

        self.selected_index = insert_at

        self.populate_listbox() # Will find duplicates and color accordingly

        self.is_dirty_file = True
        self._set_status(f"Added new item. Now {len(self.data)} items.")
        if self.current_file_path:
            self.save_data_to_file(autosave=True)

        self._update_ui_element_states()
        self.instruction_text.focus_set()
        # self.instruction_text.edit_reset() # These might not be necessary with ScrolledText
        # self.instruction_text.edit_separator()


    def delete_item(self):
        # ... (same as before, but populate_listbox will handle dupe detection) ...
        if not (0 <= self.selected_index < len(self.data)):
            messagebox.showwarning("Delete Item", "No item selected or selection is invalid.")
            return
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Item {self.selected_index + 1}? This cannot be undone directly by standard text undo (use app's Undo)."):
            return

        self._commit_ui_edits_if_any()
        self._push_state_to_undo(f"Delete Item {self.selected_index + 1}")

        deleted_item_original_index = self.selected_index
        del self.data[deleted_item_original_index]

        new_selection_target_index = -1
        if self.data:
            if deleted_item_original_index < len(self.data):
                new_selection_target_index = deleted_item_original_index
            else:
                new_selection_target_index = len(self.data) - 1

        self.selected_index = new_selection_target_index

        self.populate_listbox() # Will find duplicates and color accordingly

        if 0 <= self.selected_index < len(self.data):
            self._load_item_data_to_fields(self.data[self.selected_index]) # Ensure fields are loaded for new selection
            self._set_status(f"Displaying Item {self.selected_index + 1} of {len(self.data)}. Previous item deleted.")
        elif not self.data:
            self._set_status(f"Deleted item. List is now empty.")
        else:
            self.clear_text_fields()
            self.selected_index = -1
            self._set_status("Item deleted. No item selected.")

        self.is_dirty_file = True
        if self.current_file_path:
            self.save_data_to_file(autosave=True)

        self._update_ui_element_states()


if __name__ == '__main__':
    root = tk.Tk()
    app = JsonlEditorAppTk(root)
    root.mainloop()
