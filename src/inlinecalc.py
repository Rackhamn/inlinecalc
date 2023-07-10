import sys

from gi.repository import GObject, Gtk, Gdk, Xed
from decimal import * # arbitrary-precision decimal module :)
import math

import rp # solve_texts()

# COMMAND_TOKENS	= ('§', '$')
USER_KEYS		= ('Return', 'ISO_Enter') # 'section'
MENU_PATH		= "/MenuBar/ToolsMenu/ToolsOps_2"

class Calculation(object):
	def __init__(self, input, answer):
		self.input = input
		self.answer = self.answer

class InlineCalc(GObject.Object, Xed.WindowActivatable):
	__gtype_name__ = "InlineCalc"
	window = GObject.property(type=Xed.Window)
	ev_id = 0
	widget_win = None

	# booleans
	debug = True # does nothing atm
	output_newline = False

	def __init__(self):
		GObject.Object.__init__(self)

	def do_activate(self):
		self.window.add_events(Gdk.EventMask.KEY_PRESS_MASK)
		self.ev_id = self.window.connect('key_press_event', self.on_key_press_event)
		self._insert_menu()

		# make user settable and reset on runs.
		# tell Decimal to deal with rounding and precision:
		getcontext().prec = 9
		getcontext().rounding = ROUND_HALF_EVEN

	def do_deactivate(self):
		if self.debug:
			print("try save some stuff to file")
		self._remove_menu()
		self.window.disconnect(self.ev_id)
		self.ev_id = 0

	def _insert_menu(self):
		manager = self.window.get_ui_manager()
		self._ui_id = manager.new_merge_id()

		# NOTE: action_group is depricated after GTK 3.10, use Gio.Action and Gtk.Menu

		# "<Ctrl>section"
		self._action_group = Gtk.ActionGroup(name="InlineCalcActions")

		# hotkey open settings menu
		self._action_group.add_actions([("InlineCalcActing", None, _("_InlineCalc Settings"), "<Ctrl>section", _("InlineCalc's Editable Settings"), self._widget_function)])

		manager.insert_action_group(self._action_group)
		manager.add_ui(self._ui_id,
						MENU_PATH,
						"InlineCalcActing", # path
						"InlineCalcActing",	# action
						Gtk.UIManagerItemType.MENUITEM,
						False)

	def _remove_menu(self):
		manager = self.window.get_ui_manager()
		manager.remove_ui(self._ui_id)
		manager.remove_action_group(self._action_group)
		manager.ensure_update()

	def _widget_function(self, action):
			# NOTE: please load from an XML file.

			win = Gtk.Window()
			win.set_position(Gtk.WindowPosition.CENTER)
			win.set_border_width(10)
			win.set_default_size(600, 600) # drop
			win.set_title("Inline Calc Settings")

			# TODO:
			# clean the settings into a explanations box
			# add a section on the loaded functions
			# use degrees or radians check (convert check)
			# only store the tokens not the real string

			# Gtk.Stack()
			grid = Gtk.Grid() # Gtk.Paned
			win.add(grid)

			# TOGGLE BUTTONS:
			bt_debug = Gtk.CheckButton(label="Printout Debug Info?")
			bt_debug.connect("clicked", self._btn_toggle_debug)
			bt_debug.set_active(self.debug)
			grid.attach(bt_debug, 0, 1, 1, 1)

			bt_output_newline = Gtk.CheckButton(label="Answer On New Line?")
			bt_output_newline.connect("clicked", self._btn_toggle_output_newline)
			bt_output_newline.set_active(self.output_newline)
			grid.attach(bt_output_newline, 0, 4, 1, 1)

			# also, save on destroy into file???
			win.connect("destroy", self._kill_widget_function)
			win.show_all()
			self.widget_win = win

	def _kill_widget_function(self, action):
		if self.widget_win != None:
			self.widget_win.destroy()
			self.widget_win = None

	def _btn_toggle_debug(self, widget):
		if self.debug:
			print("toggle_debug")
		self.debug = widget.get_active()

	def _btn_toggle_output_newline(self, widget):
		if self.debug:
			print("toggle_output_newline")
		self.output_newline = widget.get_active()

	def do_update_state(self):
		pass

	def on_key_press_event(self, window, event):
		key = Gdk.keyval_name(event.keyval) # string
		# if something goes wrong, xed will do a regular action (whatever that might be)
		# if it goes right then we return True to say that we have correctly intercepted event
		if event.state & Gdk.ModifierType.CONTROL_MASK and key in USER_KEYS:
			return self._do_inlinecalc()
		return False

	# please reduce size -> just get the text
	def _do_inlinecalc(self):
		view = self.window.get_active_view()
		if view == None:
			return False

		buf = view.get_buffer()

		# get the iterator for the current cursor line
		it = buf.get_iter_at_mark(buf.get_insert())
		start = it.copy()
		end = it.copy()

		# move iterator to start of line, then search until end for first matching TOKEN
		start.set_line_offset(0) # note: need to check this better, .starts_line()
		if start.ends_line() == True:
			if self.debug:
				print("empty line")
			return False

		if end.ends_line() != True:
			end.forward_to_line_end() # note: need to check this better!!!
		it = start.copy()

		# copy the string into line
		line = buf.get_text(it, end, False)

		result = rp.solve_text(line)
		self.calculations.append([str(line), str(result)])

		if result == None:
			return False

		out = ""
		# start writing the new line there.

		if self.output_newline:
			out += "\n"

		out += " = " + str(result)
		it = end.copy()
		buf.begin_user_action()
		buf.insert(it, out)
		buf.end_user_action()
		return True

