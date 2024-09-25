import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import subprocess
import os
import json
import time
import ctypes

# File to store shortcuts
APP_DATA_FILE = "shortcuts.json"


# Load or create the shortcuts file
def load_shortcuts():
	if os.path.exists(APP_DATA_FILE):
		with open(APP_DATA_FILE, 'r') as file:
			return json.load(file)
	else:
		return {}


def save_shortcuts(shortcuts):
	with open(APP_DATA_FILE, 'w') as file:
		json.dump(shortcuts, file)


# Load existing shortcuts
applications = load_shortcuts()


# Bring the application window to the forefront (Windows only)
def bring_to_front(app_process):
	if os.name == 'nt':
		time.sleep(1)  # Give the application some time to open
		hwnd = ctypes.windll.user32.GetForegroundWindow()
		ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW
		ctypes.windll.user32.SetForegroundWindow(hwnd)


# Main Application class
class AppLauncher(tk.Tk):
	def __init__(self):
		super().__init__()

		# Set the title of the window to "Launcher"
		self.title("Launcher")

		# Set the height and width of the window (adjustable)
		self.geometry("200x400")

		# Remove titlebar and make window non-resizable
		self.overrideredirect(True)
		self.resizable(False, False)

		# Center the window on the screen
		self.center_window()

		# Bind the focus-out event to close the launcher (we'll modify this)
		self.bind("<FocusOut>", self.check_focus)

		# Create a frame to hold everything
		main_frame = tk.Frame(self)
		main_frame.grid(sticky="nsew")

		# Configure grid weights for responsiveness
		self.grid_rowconfigure(0, weight=1)
		self.grid_columnconfigure(0, weight=1)

		main_frame.grid_rowconfigure(1, weight=1)  # Let listbox grow/shrink
		main_frame.grid_columnconfigure(0, weight=1)  # Let everything expand horizontally

		# Store original application list
		self.original_applications = applications.copy()

		# Create an Entry widget for filtering the list
		self.search_var = tk.StringVar()
		self.search_var.trace("w", self.update_list)
		self.search_entry = tk.Entry(main_frame, textvariable=self.search_var)
		self.search_entry.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="ew")

		# Make sure filter input is always focused
		self.search_entry.focus_set()

		# Override arrow keys to navigate the listbox
		self.search_entry.bind("<Up>", self.move_selection_up)
		self.search_entry.bind("<Down>", self.move_selection_down)
		self.search_entry.bind("<Return>", self.launch_selected_from_filter)

		# Create Listbox with scrollbar
		self.listbox = tk.Listbox(main_frame, height=10, justify='center', activestyle="dotbox")
		self.listbox.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

		# Create a scrollbar and attach it to the listbox
		self.scrollbar = tk.Scrollbar(self.listbox)
		self.listbox.config(yscrollcommand=self.scrollbar.set)
		self.scrollbar.config(command=self.listbox.yview)

		# Bind double-click to launch the app
		self.listbox.bind("<Double-Button-1>", self.launch_selected)

		# Populate Listbox
		self.populate_listbox()

		# Bind events for key handling
		self.listbox.bind("<Delete>", self.delete_selected)
		self.listbox.bind("<Return>", self.launch_selected)
		self.listbox.bind("<MouseWheel>", self.on_mouse_wheel)  # Mouse scroll
		self.bind("<Escape>", self.close_launcher)  # Close launcher on Escape

		# Add button to add new shortcuts, and make it full width with space below
		self.add_button = tk.Button(main_frame, text="Add Shortcut", command=self.open_add_dialog)
		self.add_button.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="ew")  # Padding adjusted for space below

	# Center the window on the screen
	def center_window(self):
		self.update_idletasks()
		width = self.winfo_width()
		height = self.winfo_height()
		screen_width = self.winfo_screenwidth()
		screen_height = self.winfo_screenheight()
		x = (screen_width // 2) - (width // 2)
		y = (screen_height // 2) - (height // 2)
		self.geometry(f"{width}x{height}+{x}+{y}")

	# Populate the Listbox with apps
	def populate_listbox(self):
		self.listbox.delete(0, tk.END)
		for app_title in applications.keys():
			self.listbox.insert(tk.END, app_title)
		# Select the first item if available
		if self.listbox.size() > 0:
			self.listbox.select_set(0)
			self.listbox.activate(0)

	# Update list based on search input
	def update_list(self, *args):
		search_term = self.search_var.get().lower()
		if search_term:
			filtered_apps = {key: value for key, value in self.original_applications.items() if search_term in key.lower()}
			global applications
			applications = filtered_apps
		else:
			applications = self.original_applications.copy()
		self.populate_listbox()

	# Check if the focus is lost to an external window, and close the launcher
	def check_focus(self, event):
		# Only quit if the focus is lost for reasons other than an active dialog
		if self.focus_get() is None and not self.winfo_exists():
			self.quit()

	# Launch the app from filter input or list selection
	def launch_selected_from_filter(self, event):
		if self.listbox.size() > 0:
			self.launch_selected(None)

	# Delete the selected shortcut
	def delete_selected(self, event):
		try:
			selected_app = self.listbox.get(self.listbox.curselection())
			if selected_app in applications:
				del applications[selected_app]
				save_shortcuts(applications)
				self.original_applications = applications.copy()  # Update original list
				self.populate_listbox()
		except:
			messagebox.showwarning("Warning", "Please select an item to delete.")

	# Launch the selected application and close the launcher
	def launch_selected(self, event):
		try:
			selected_app = self.listbox.get(self.listbox.curselection())
			app_path = applications[selected_app]
			app_process = subprocess.Popen(app_path)
			bring_to_front(app_process)
			self.quit()  # Close the launcher app
		except Exception as e:
			messagebox.showerror("Error", f"Failed to launch {selected_app}: {str(e)}")

	# Move the selection up in the listbox
	def move_selection_up(self, event):
		current_selection = self.listbox.curselection()
		if current_selection:
			current_index = current_selection[0]
			if current_index > 0:
				self.listbox.selection_clear(current_index)
				self.listbox.selection_set(current_index - 1)
				self.listbox.activate(current_index - 1)

	# Move the selection down in the listbox
	def move_selection_down(self, event):
		current_selection = self.listbox.curselection()
		if current_selection:
			current_index = current_selection[0]
			if current_index < self.listbox.size() - 1:
				self.listbox.selection_clear(current_index)
				self.listbox.selection_set(current_index + 1)
				self.listbox.activate(current_index + 1)

	# Enable scrolling through the listbox with the mouse wheel
	def on_mouse_wheel(self, event):
		self.listbox.yview_scroll(int(-1 * (event.delta / 120)), "units")

	# Close the launcher when Escape or on focus loss
	def close_launcher(self, event):
		self.quit()

	# Open a dialog to add a new shortcut
	def open_add_dialog(self):
		# Ask for the app title
		app_title = simpledialog.askstring("Input", "Enter the title of the application:")
		if not app_title:
			return

		# Ask for the app file path
		app_path = filedialog.askopenfilename(title="Select Application")
		if not app_path:
			return

		# Save the new shortcut
		applications[app_title] = app_path
		save_shortcuts(applications)
		self.original_applications = applications.copy()  # Update original list
		self.populate_listbox()


if __name__ == "__main__":
	# Initialize and run the app
	app = AppLauncher()
	app.mainloop()
