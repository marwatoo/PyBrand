#!/usr/bin/python3

# Created with Claude and edited with Copilot
# GTK3 rewrite

import sys
import os
import time
import threading

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GdkPixbuf, Gio

# Import your existing modules
from batch import square_batch, rectangle_batch, cover_batch
from photos import create_post, footix
from files import get_dir
from preview import PreviewWindow  # If this is also GTK-based


# ---------------------------------------------------------------------------
# Helper: load a PIL image into a GdkPixbuf (for the preview path)
# ---------------------------------------------------------------------------
def pil_to_pixbuf(pil_img):
    """Convert a PIL/Pillow Image to a GdkPixbuf."""
    import io
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)
    loader = GdkPixbuf.PixbufLoader.new_with_type("png")
    loader.write(buf.read())
    loader.close()
    return loader.get_pixbuf()


# ---------------------------------------------------------------------------
# Preview window (replaces the PyQt PreviewWindow)
# ---------------------------------------------------------------------------
class PreviewDialog(Gtk.Dialog):
    """Dialog that shows a scrollable preview of a PIL image."""

    def __init__(self, pil_img, parent):
        super().__init__(title="Preview", parent=parent, flags=Gtk.DialogFlags.MODAL)
        self.set_default_size(600, 700)

        content_area = self.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        content_area.set_margin_start(10)
        content_area.set_margin_end(10)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)

        try:
            pixbuf = pil_to_pixbuf(pil_img)
            # Scale down to fit in the dialog while keeping aspect ratio
            max_w, max_h = 560, 620
            orig_w = pixbuf.get_width()
            orig_h = pixbuf.get_height()
            scale = min(max_w / orig_w, max_h / orig_h, 1.0)
            new_w = int(orig_w * scale)
            new_h = int(orig_h * scale)
            scaled = pixbuf.scale_simple(new_w, new_h, GdkPixbuf.InterpType.BILINEAR)
            image = Gtk.Image.new_from_pixbuf(scaled)
            scroll.add(image)
        except Exception as e:
            label = Gtk.Label(label=f"Could not render preview:\n{e}")
            scroll.add(label)

        content_area.add(scroll)

        self.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        self.show_all()
        self.run()
        self.destroy()


# ---------------------------------------------------------------------------
# Image row widget used inside the ListBox
# ---------------------------------------------------------------------------
class ImageRow(Gtk.ListBoxRow):
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(8)
        box.set_margin_end(8)

        # Thumbnail
        try:
            pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(file_path, 64, 64, True)
            img = Gtk.Image.new_from_pixbuf(pb)
        except Exception:
            img = Gtk.Image.new_from_icon_name("image-x-generic", Gtk.IconSize.DND)

        box.add(img)

        # File info
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_label = Gtk.Label(label=os.path.basename(file_path))
        title_label.set_halign(Gtk.Align.START)
        title_label.set_ellipsize(True)
        subtitle_label = Gtk.Label(label=file_path)
        subtitle_label.set_halign(Gtk.Align.START)
        subtitle_label.set_opacity(0.7)
        subtitle_label.set_ellipsize(True)
        info_box.add(title_label)
        info_box.add(subtitle_label)

        box.pack_start(info_box, True, True, 0)
        self.add(box)
        self.show_all()


# ---------------------------------------------------------------------------
# Main application window
# ---------------------------------------------------------------------------
class VictoriaBadazz(Gtk.ApplicationWindow):

    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Victoria's Badazz")
        self.set_default_size(480, 780)
        self.set_border_width(0)

        icon_path = os.path.join(get_dir(), "vic.ico")
        if os.path.exists(icon_path):
            try:
                self.set_icon_from_file(icon_path)
            except Exception:
                pass

        self.myimages: list = []
        self.dest_folder_path: str = None

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Root: VBox with HeaderBar (implicit in ApplicationWindow)
        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(root_box)

        # Create main scrollable area
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)

        # Main content area with padding
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)

        scroll.add_with_viewport(main_box)
        root_box.pack_start(scroll, True, True, 0)

        # ---- Select source ----
        source_frame = self._create_frame("Source")
        self.select_button = Gtk.Button(label="Select Folder or Image")
        self.select_button.get_style_context().add_class("suggested-action")
        self.select_button.connect("clicked", self._on_select_clicked)
        source_frame.add(self.select_button)
        main_box.add(source_frame)

        # ---- Image list ----
        list_frame = self._create_frame("Images")
        self.image_listbox = Gtk.ListBox()
        self.image_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        list_frame.add(self.image_listbox)
        main_box.add(list_frame)

        # Reorder / Remove buttons
        reorder_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        reorder_box.set_homogeneous(True)
        self.up_button = Gtk.Button(label="▲  Move Up")
        self.up_button.connect("clicked", self._on_move_up)
        self.down_button = Gtk.Button(label="▼  Move Down")
        self.down_button.connect("clicked", self._on_move_down)
        self.remove_button = Gtk.Button(label="✕  Remove")
        self.remove_button.get_style_context().add_class("destructive-action")
        self.remove_button.connect("clicked", self._on_remove)
        reorder_box.add(self.up_button)
        reorder_box.add(self.down_button)
        reorder_box.add(self.remove_button)
        main_box.add(reorder_box)

        # ---- Options ----
        options_frame = self._create_frame("Options")
        options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        # Logo
        logo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        logo_label = Gtk.Label(label="Logo:", xalign=0)
        logo_label.set_size_request(100, -1)
        self.logo_combo = Gtk.ComboBoxText()
        self.logo_combo.append_text("Le360")
        self.logo_combo.append_text("Afrique")
        self.logo_combo.append_text("Sport")
        self.logo_combo.append_text("None")
        self.logo_combo.set_active(0)
        logo_box.add(logo_label)
        logo_box.pack_start(self.logo_combo, True, True, 0)
        options_box.add(logo_box)

        # Mode
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        mode_label = Gtk.Label(label="Mode:", xalign=0)
        mode_label.set_size_request(100, -1)
        self.mode_combo = Gtk.ComboBoxText()
        self.mode_combo.append_text("Rectangle")
        self.mode_combo.append_text("Post")
        self.mode_combo.append_text("Diapo")
        self.mode_combo.append_text("16/9")
        self.mode_combo.append_text("Footix")
        self.mode_combo.set_active(0)
        self.mode_combo.connect("changed", self._on_mode_changed)
        mode_box.add(mode_label)
        mode_box.pack_start(self.mode_combo, True, True, 0)
        options_box.add(mode_box)

        options_frame.add(options_box)
        main_box.add(options_frame)

        # ---- Diapo-specific fields ----
        self.diapo_frame = self._create_frame("Diapo Options")
        diapo_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        title_box = self._create_entry_row("Title")
        self.title_entry = title_box[1]
        diapo_box.add(title_box[0])

        city_box = self._create_entry_row("City")
        self.city_entry = city_box[1]
        diapo_box.add(city_box[0])

        diapo_lang_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        diapo_lang_label = Gtk.Label(label="Language:", xalign=0)
        diapo_lang_label.set_size_request(100, -1)
        self.diapo_lang_combo = Gtk.ComboBoxText()
        self.diapo_lang_combo.append_text("fr")
        self.diapo_lang_combo.append_text("ar")
        self.diapo_lang_combo.set_active(0)
        diapo_lang_box.add(diapo_lang_label)
        diapo_lang_box.pack_start(self.diapo_lang_combo, True, True, 0)
        diapo_box.add(diapo_lang_box)

        self.diapo_frame.add(diapo_box)
        self.diapo_frame.hide()
        main_box.add(self.diapo_frame)

        # ---- Post-specific fields ----
        self.post_frame = self._create_frame("Post Options")
        post_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        post_title_box = self._create_entry_row("Title")
        self.post_title_entry = post_title_box[1]
        self.post_title_entry.connect("changed", self._on_post_title_changed)
        post_box.add(post_title_box[0])

        word_box = self._create_entry_row("Words")
        self.word_entry = word_box[1]
        post_box.add(word_box[0])

        # Title size (SpinButton)
        tsize_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        tsize_label = Gtk.Label(label="Title Size:", xalign=0)
        tsize_label.set_size_request(100, -1)
        self.tsize_spin = Gtk.SpinButton()
        self.tsize_spin.set_range(10, 200)
        self.tsize_spin.set_increments(1, 10)
        self.tsize_spin.set_value(100)
        tsize_box.add(tsize_label)
        tsize_box.pack_start(self.tsize_spin, True, True, 0)
        post_box.add(tsize_box)

        # Title spacing
        tspace_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        tspace_label = Gtk.Label(label="Title Spacing:", xalign=0)
        tspace_label.set_size_request(100, -1)
        self.tspace_spin = Gtk.SpinButton()
        self.tspace_spin.set_range(-50, 50)
        self.tspace_spin.set_increments(1, 10)
        self.tspace_spin.set_value(20)
        tspace_box.add(tspace_label)
        tspace_box.pack_start(self.tspace_spin, True, True, 0)
        post_box.add(tspace_box)

        post_lang_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        post_lang_label = Gtk.Label(label="Language:", xalign=0)
        post_lang_label.set_size_request(100, -1)
        self.post_lang_combo = Gtk.ComboBoxText()
        self.post_lang_combo.append_text("fr")
        self.post_lang_combo.append_text("ar")
        self.post_lang_combo.set_active(0)
        post_lang_box.add(post_lang_label)
        post_lang_box.pack_start(self.post_lang_combo, True, True, 0)
        post_box.add(post_lang_box)

        position_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        position_label = Gtk.Label(label="Position:", xalign=0)
        position_label.set_size_request(100, -1)
        self.position_combo = Gtk.ComboBoxText()
        self.position_combo.append_text("center")
        self.position_combo.append_text("right")
        self.position_combo.append_text("left")
        self.position_combo.set_active(0)
        position_box.add(position_label)
        position_box.pack_start(self.position_combo, True, True, 0)
        post_box.add(position_box)

        tag_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        tag_label = Gtk.Label(label="Tag:", xalign=0)
        tag_label.set_size_request(100, -1)
        self.tag_combo = Gtk.ComboBoxText()
        self.tag_combo.append_text("none")
        self.tag_combo.append_text("archive")
        self.tag_combo.append_text("illustration")
        self.tag_combo.set_active(0)
        tag_box.add(tag_label)
        tag_box.pack_start(self.tag_combo, True, True, 0)
        post_box.add(tag_box)

        self.post_frame.add(post_box)
        self.post_frame.hide()
        main_box.add(self.post_frame)

        # ---- Destination ----
        dest_frame = self._create_frame("Destination")
        dest_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        dest_label = Gtk.Label(label="Destination Folder:")
        self.dest_path_label = Gtk.Label(label="Not selected")
        self.dest_path_label.set_halign(Gtk.Align.START)
        self.dest_path_label.set_opacity(0.7)
        self.dest_button = Gtk.Button(label="Browse")
        self.dest_button.connect("clicked", self._on_select_dest)
        dest_box.add(dest_label)
        dest_box.pack_start(self.dest_path_label, True, True, 0)
        dest_box.add(self.dest_button)
        dest_frame.add(dest_box)
        main_box.add(dest_frame)

        # ---- Action buttons ----
        action_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        self.preview_button = Gtk.Button(label="Preview")
        self.preview_button.connect("clicked", self._on_preview_clicked)
        self.preview_button.hide()
        action_box.add(self.preview_button)

        self.generate_button = Gtk.Button(label="Generate")
        self.generate_button.get_style_context().add_class("suggested-action")
        self.generate_button.connect("clicked", self._on_generate_clicked)
        self.generate_button.hide()
        action_box.add(self.generate_button)

        main_box.add(action_box)

        self.show_all()

        # initialise button states
        self._update_reorder_buttons()
        self._update_action_buttons()

    def _create_frame(self, title: str) -> Gtk.Frame:
        """Create a labeled frame."""
        frame = Gtk.Frame(label=title)
        frame.set_label_align(0.0, 0.5)
        frame.set_shadow_type(Gtk.ShadowType.NONE)
        frame.set_margin_top(6)
        frame.set_margin_bottom(6)
        return frame

    def _create_entry_row(self, label_text: str):
        """Create a labeled entry field."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        label = Gtk.Label(label=label_text + ":", xalign=0)
        label.set_size_request(100, -1)
        entry = Gtk.Entry()
        box.add(label)
        box.pack_start(entry, True, True, 0)
        return (box, entry)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_mode(self) -> str:
        modes = ["Rectangle", "Post", "Diapo", "16/9", "Footix"]
        return modes[self.mode_combo.get_active()]

    def _get_logo(self) -> str:
        logos = ["Le360", "Afrique", "Sport", "None"]
        return logos[self.logo_combo.get_active()]

    def _get_diapo_lang(self) -> str:
        return ["fr", "ar"][self.diapo_lang_combo.get_active()]

    def _get_post_lang(self) -> str:
        return ["fr", "ar"][self.post_lang_combo.get_active()]

    def _get_position(self) -> str:
        return ["center", "right", "left"][self.position_combo.get_active()]

    def _get_tag(self) -> str:
        tags = ["none", "archive", "illustration"]
        tag_idx = self.tag_combo.get_active()
        return tags[tag_idx] if tag_idx >= 0 else "none"

    def _selected_row_index(self) -> int:
        row = self.image_listbox.get_selected_row()
        if row is None:
            return None
        return row.get_index()

    def _refresh_listbox(self):
        """Clear and repopulate the listbox from self.myimages."""
        for child in self.image_listbox.get_children():
            self.image_listbox.remove(child)
        for path in self.myimages:
            self.image_listbox.add(ImageRow(path))

    def _update_reorder_buttons(self):
        mode = self._get_mode()
        n = len(self.myimages)
        self.up_button.set_visible(n >= 2)
        self.down_button.set_visible(n >= 2)
        # Hide remove button in Post mode (only one image allowed)
        self.remove_button.set_visible(n >= 1 and mode != "Post")

    def _update_action_buttons(self):
        mode = self._get_mode()
        has_images = bool(self.myimages)
        has_dest = bool(self.dest_folder_path)
        self.generate_button.set_visible(has_images and has_dest)

        is_post = (mode == "Post")
        has_title = bool(self.post_title_entry.get_text().strip())
        self.preview_button.set_visible(is_post and has_images and has_title)

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------
    def _on_mode_changed(self, combo):
        mode = self._get_mode()
        self.diapo_frame.set_visible(mode == "Diapo")
        self.post_frame.set_visible(mode == "Post")
        self.logo_combo.set_sensitive(mode not in ("Post", "Footix"))
        self._update_action_buttons()

    def _on_post_title_changed(self, entry):
        self._update_action_buttons()

    def _on_select_clicked(self, btn):
        mode = self._get_mode()
        if mode in ("Post", "Footix"):
            dialog = Gtk.FileChooserDialog(
                title="Select an Image",
                parent=self,
                action=Gtk.FileChooserAction.OPEN
            )
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK
            )
            filter_images = Gtk.FileFilter()
            filter_images.set_name("Image Files")
            for ext in ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.gif", "*.webp"]:
                filter_images.add_pattern(ext)
            dialog.add_filter(filter_images)
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                path = dialog.get_filename()
                if path:
                    self.myimages = [path]
                    self._refresh_listbox()
                    self._update_reorder_buttons()
                    self._update_action_buttons()
            dialog.destroy()
        else:
            dialog = Gtk.FileChooserDialog(
                title="Select Folder with Images",
                parent=self,
                action=Gtk.FileChooserAction.SELECT_FOLDER
            )
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK
            )
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                folder_path = dialog.get_filename()
                if folder_path:
                    exts = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
                    self.myimages = [
                        os.path.join(folder_path, f)
                        for f in sorted(os.listdir(folder_path))
                        if os.path.splitext(f.lower())[1] in exts
                    ]
                    self._refresh_listbox()
                    self._update_reorder_buttons()
                    self._update_action_buttons()
            dialog.destroy()

    def _on_select_dest(self, btn):
        dialog = Gtk.FileChooserDialog(
            title="Select Destination Folder",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            path = dialog.get_filename()
            if path:
                self.dest_folder_path = path
                self.dest_path_label.set_text(path)
                self._update_action_buttons()
        dialog.destroy()

    def _on_move_up(self, btn):
        idx = self._selected_row_index()
        if idx is None or idx == 0:
            return
        self.myimages[idx - 1], self.myimages[idx] = self.myimages[idx], self.myimages[idx - 1]
        self._refresh_listbox()
        self.image_listbox.select_row(self.image_listbox.get_row_at_index(idx - 1))
        self._update_reorder_buttons()

    def _on_move_down(self, btn):
        idx = self._selected_row_index()
        if idx is None or idx >= len(self.myimages) - 1:
            return
        self.myimages[idx + 1], self.myimages[idx] = self.myimages[idx], self.myimages[idx + 1]
        self._refresh_listbox()
        self.image_listbox.select_row(self.image_listbox.get_row_at_index(idx + 1))
        self._update_reorder_buttons()

    def _on_remove(self, btn):
        idx = self._selected_row_index()
        if idx is None:
            return
        self.myimages.pop(idx)
        self._refresh_listbox()
        self._update_reorder_buttons()
        self._update_action_buttons()

    def _on_generate_clicked(self, btn):
        if not self.myimages or not self.dest_folder_path:
            return

        # Disable generate button while running
        self.generate_button.set_sensitive(False)
        self.generate_button.set_label("Generating…")

        mode = self._get_mode()

        # Collect all parameters before spawning thread
        params = {
            "mode": mode,
            "logo": self._get_logo(),
            "dest": self.dest_folder_path,
            "images": list(self.myimages),
        }
        if mode == "Diapo":
            params["title"] = self.title_entry.get_text().upper()
            params["city"] = self.city_entry.get_text().upper()
            params["language"] = self._get_diapo_lang()
        elif mode == "Post":
            params["titre"] = self.post_title_entry.get_text().upper()
            params["mot"] = self.word_entry.get_text().upper()
            params["position"] = self._get_position()
            params["lang"] = self._get_post_lang()
            params["tsize"] = int(self.tsize_spin.get_value())
            params["tspace"] = int(self.tspace_spin.get_value())
            params["tag"] = self._get_tag()

        def worker():
            stime = time.time()
            try:
                m = params["mode"]
                if m == "Diapo":
                    square_batch(params["images"], params["logo"], params["dest"],
                                 params["city"], params["title"], params["language"])
                elif m == "Rectangle":
                    rectangle_batch(params["images"], params["logo"], params["dest"])
                elif m == "16/9":
                    cover_batch(params["images"], params["logo"], params["dest"])
                elif m == "Post":
                    create_post(
                        params["images"][0], params["dest"], 1080, 1350,
                        params["position"], params["titre"], params["mot"],
                        params["lang"], params["tsize"], params["tspace"],
                        "#FFFFFF", "#FF7A14", params["tag"]
                    )
                elif m == "Footix":
                    footix(params["images"][0], params["dest"], "center")
                elapsed = time.time() - stime
                GLib.idle_add(self._on_generate_done, elapsed, None)
            except Exception as e:
                GLib.idle_add(self._on_generate_done, 0.0, str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _on_generate_done(self, elapsed: float, error: str):
        self.generate_button.set_sensitive(True)
        self.generate_button.set_label("Generate")
        if error:
            self._show_error("Generation Failed", error)
        else:
            self._show_info("Done", f"Completed in {elapsed:.2f} seconds.")
            self.myimages.clear()
            self._refresh_listbox()
            self._update_reorder_buttons()
            self._update_action_buttons()
        return GLib.SOURCE_REMOVE

    def _on_preview_clicked(self, btn):
        if not self.myimages:
            self._show_error("Preview", "No image selected.")
            return
        if self._get_mode() != "Post":
            self._show_error("Preview", "Preview is only available in Post mode.")
            return
        titre = self.post_title_entry.get_text().upper().strip()
        if not titre:
            self._show_error("Preview", "Please enter a title before previewing.")
            return
        mot = self.word_entry.get_text().upper()
        try:
            pil_img = create_post(
                self.myimages[0], "preview", 1080, 1350,
                self._get_position(), titre, mot,
                self._get_post_lang(),
                int(self.tsize_spin.get_value()),
                int(self.tspace_spin.get_value()),
                "#FFFFFF", "#FF7A14", self._get_tag()
            )
        except Exception as e:
            self._show_error("Preview Error", str(e))
            return
        PreviewDialog(pil_img, self)

    # ------------------------------------------------------------------
    # Dialogs
    # ------------------------------------------------------------------
    def _show_info(self, title: str, message: str):
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            message_format=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def _show_error(self, title: str, message: str):
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            message_format=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()


# ---------------------------------------------------------------------------
# Application entry point
# ---------------------------------------------------------------------------
class VictoriaApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.victoria.badazz")
        self.connect("activate", self._on_activate)

    def _on_activate(self, app):
        win = VictoriaBadazz(app)
        win.present()


if __name__ == "__main__":
    app = VictoriaApp()
    sys.exit(app.run(sys.argv))
