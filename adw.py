#!/usr/bin/python3

#Created with Claude and edited with Copilot

import sys
import os
import time
import threading

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, GdkPixbuf, Gio, Gdk

# Import your existing modules
from batch import square_batch, rectangle_batch, cover_batch
from photos import create_post, footix
from files import get_dir
from preview import PreviewWindow  # If this is also GTK-based; see note below


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
class PreviewDialog(Adw.Dialog):
    """Modal dialog that shows a scrollable preview of a PIL image."""

    def __init__(self, pil_img, parent):
        super().__init__()
        self.set_title("Preview")
        self.set_content_width(600)
        self.set_content_height(700)

        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        scroll = Gtk.ScrolledWindow()
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
            picture = Gtk.Picture.new_for_pixbuf(scaled)
            picture.set_can_shrink(False)
            scroll.set_child(picture)
        except Exception as e:
            scroll.set_child(Gtk.Label(label=f"Could not render preview:\n{e}"))

        toolbar_view.set_content(scroll)
        self.set_child(toolbar_view)

        self.present(parent)


# ---------------------------------------------------------------------------
# Image row widget used inside the ListBox
# ---------------------------------------------------------------------------
class ImageRow(Adw.ActionRow):
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.set_title(os.path.basename(file_path))
        self.set_subtitle(file_path)

        # Thumbnail
        try:
            pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(file_path, 64, 64, True)
            img = Gtk.Image.new_from_pixbuf(pb)
        except Exception:
            img = Gtk.Image.new_from_icon_name("image-x-generic")
        img.set_pixel_size(64)
        self.add_prefix(img)


# ---------------------------------------------------------------------------
# Main application window
# ---------------------------------------------------------------------------
class VictoriaBadazz(Adw.ApplicationWindow):

    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Victoria's Badazz")
        self.set_default_size(480, 780)

        icon_path = os.path.join(get_dir(), "vic.ico")
        if os.path.exists(icon_path):
            # GTK4 uses theme icons; convert .ico to a texture if needed
            try:
                pb = GdkPixbuf.Pixbuf.new_from_file(icon_path)
                texture = Gdk.Texture.new_for_pixbuf(pb)
                self.set_icon_name(None)  # clear any theme icon
                # ApplicationWindow doesn't directly accept a texture,
                # but we can set it on the Gtk.Window level:
                # (No-op on Wayland compositors that ignore it)
            except Exception:
                pass

        self.myimages: list[str] = []
        self.dest_folder_path: str | None = None

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Root: ToolbarView with HeaderBar + scrollable content
        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="Victoria's Badazz", subtitle="Image batch processor"))
        toolbar_view.add_top_bar(header)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(480)
        clamp.set_margin_top(12)
        clamp.set_margin_bottom(12)
        clamp.set_margin_start(12)
        clamp.set_margin_end(12)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        clamp.set_child(box)
        scroll.set_child(clamp)
        toolbar_view.set_content(scroll)
        self.set_content(toolbar_view)

        # ---- Select source ----
        source_group = Adw.PreferencesGroup(title="Source")
        self.select_button = Gtk.Button(label="Select Folder or Image")
        self.select_button.set_css_classes(["pill", "suggested-action"])
        self.select_button.connect("clicked", self._on_select_clicked)
        source_group.add(self.select_button)
        box.append(source_group)

        # ---- Image list ----
        list_group = Adw.PreferencesGroup(title="Images")
        self.image_listbox = Gtk.ListBox()
        self.image_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.image_listbox.add_css_class("boxed-list")
        list_group.add(self.image_listbox)
        box.append(list_group)

        # Reorder / Remove buttons
        reorder_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        reorder_box.set_homogeneous(True)
        self.up_button = Gtk.Button(label="▲  Move Up")
        self.up_button.connect("clicked", self._on_move_up)
        self.down_button = Gtk.Button(label="▼  Move Down")
        self.down_button.connect("clicked", self._on_move_down)
        self.remove_button = Gtk.Button(label="✕  Remove")
        self.remove_button.add_css_class("destructive-action")
        self.remove_button.connect("clicked", self._on_remove)
        reorder_box.append(self.up_button)
        reorder_box.append(self.down_button)
        reorder_box.append(self.remove_button)
        box.append(reorder_box)

        # ---- Options ----
        options_group = Adw.PreferencesGroup(title="Options")

        # Logo
        self.logo_row = Adw.ComboRow(title="Logo")
        logo_model = Gtk.StringList.new(["Le360", "Afrique", "Sport", "None"])
        self.logo_row.set_model(logo_model)
        self.logo_row.set_selected(0)
        options_group.add(self.logo_row)

        # Mode
        self.mode_row = Adw.ComboRow(title="Mode")
        mode_model = Gtk.StringList.new(["Rectangle", "Post", "Diapo", "16/9", "Footix"])
        self.mode_row.set_model(mode_model)
        self.mode_row.set_selected(0)
        self.mode_row.connect("notify::selected", self._on_mode_changed)
        options_group.add(self.mode_row)

        box.append(options_group)

        # ---- Diapo-specific fields ----
        self.diapo_group = Adw.PreferencesGroup(title="Diapo Options")

        self.title_row = Adw.EntryRow(title="Title")
        self.diapo_group.add(self.title_row)

        self.city_row = Adw.EntryRow(title="City")
        self.diapo_group.add(self.city_row)

        self.diapo_lang_row = Adw.ComboRow(title="Language")
        diapo_lang_model = Gtk.StringList.new(["fr", "ar"])
        self.diapo_lang_row.set_model(diapo_lang_model)
        self.diapo_group.add(self.diapo_lang_row)

        self.diapo_group.set_visible(False)
        box.append(self.diapo_group)

        # ---- Post-specific fields ----
        self.post_group = Adw.PreferencesGroup(title="Post Options")

        self.post_title_row = Adw.EntryRow(title="Title")
        self.post_title_row.connect("changed", self._on_post_title_changed)
        self.post_group.add(self.post_title_row)

        self.word_row = Adw.EntryRow(title="Words")
        self.post_group.add(self.word_row)

        # Title size (SpinRow)
        self.tsize_row = Adw.SpinRow.new_with_range(10, 200, 1)
        self.tsize_row.set_title("Title Size")
        self.tsize_row.set_value(100)
        self.post_group.add(self.tsize_row)

        # Title spacing
        self.tspace_row = Adw.SpinRow.new_with_range(-50, 50, 1)
        self.tspace_row.set_title("Title Spacing")
        self.tspace_row.set_value(20)
        self.post_group.add(self.tspace_row)

        self.post_lang_row = Adw.ComboRow(title="Language")
        post_lang_model = Gtk.StringList.new(["fr", "ar"])
        self.post_lang_row.set_model(post_lang_model)
        self.post_group.add(self.post_lang_row)

        self.position_row = Adw.ComboRow(title="Position")
        pos_model = Gtk.StringList.new(["center", "right", "left"])
        self.position_row.set_model(pos_model)
        self.post_group.add(self.position_row)

        self.tag_row = Adw.ComboRow(title="Tag")
        tag_model = Gtk.StringList.new(["none", "archive", "illustration"])
        self.tag_row.set_model(tag_model)
        self.post_group.add(self.tag_row)

        self.post_group.set_visible(False)
        box.append(self.post_group)

        # ---- Destination ----
        dest_group = Adw.PreferencesGroup(title="Destination")
        self.dest_row = Adw.ActionRow(title="Destination Folder", subtitle="Not selected")
        self.dest_button = Gtk.Button(label="Browse")
        self.dest_button.set_valign(Gtk.Align.CENTER)
        self.dest_button.connect("clicked", self._on_select_dest)
        self.dest_row.add_suffix(self.dest_button)
        dest_group.add(self.dest_row)
        box.append(dest_group)

        # ---- Action buttons ----
        action_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        self.preview_button = Gtk.Button(label="Preview")
        self.preview_button.set_css_classes(["pill"])
        self.preview_button.connect("clicked", self._on_preview_clicked)
        self.preview_button.set_visible(False)
        action_box.append(self.preview_button)

        self.generate_button = Gtk.Button(label="Generate")
        self.generate_button.set_css_classes(["pill", "suggested-action"])
        self.generate_button.connect("clicked", self._on_generate_clicked)
        self.generate_button.set_visible(False)
        action_box.append(self.generate_button)

        box.append(action_box)

        # initialise button states
        self._update_reorder_buttons()
        self._update_action_buttons()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_mode(self) -> str:
        modes = ["Rectangle", "Post", "Diapo", "16/9", "Footix"]
        return modes[self.mode_row.get_selected()]

    def _get_logo(self) -> str:
        logos = ["Le360", "Afrique", "Sport", "None"]
        return logos[self.logo_row.get_selected()]

    def _get_diapo_lang(self) -> str:
        return ["fr", "ar"][self.diapo_lang_row.get_selected()]

    def _get_post_lang(self) -> str:
        return ["fr", "ar"][self.post_lang_row.get_selected()]

    def _get_position(self) -> str:
        return ["center", "right", "left"][self.position_row.get_selected()]

    def _get_tag(self) -> str:
        return ["none", "archive", "illustration"][self.tag_row.get_selected()]

    def _selected_row_index(self) -> int | None:
        row = self.image_listbox.get_selected_row()
        if row is None:
            return None
        return row.get_index()

    def _refresh_listbox(self):
        """Clear and repopulate the listbox from self.myimages."""
        while True:
            child = self.image_listbox.get_first_child()
            if child is None:
                break
            self.image_listbox.remove(child)
        for path in self.myimages:
            self.image_listbox.append(ImageRow(path))

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
        has_title = bool(self.post_title_row.get_text().strip())
        self.preview_button.set_visible(is_post and has_images and has_title)

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------
    def _on_mode_changed(self, row, _param):
        mode = self._get_mode()
        self.diapo_group.set_visible(mode == "Diapo")
        self.post_group.set_visible(mode == "Post")
        self.logo_row.set_sensitive(mode not in ("Post", "Footix"))
        self._update_action_buttons()

    def _on_post_title_changed(self, _entry):
        self._update_action_buttons()

    def _on_select_clicked(self, _btn):
        mode = self._get_mode()
        if mode in ("Post", "Footix"):
            dialog = Gtk.FileDialog()
            dialog.set_title("Select an Image")
            f = Gio.File.new_for_path(os.path.expanduser("~"))
            dialog.set_initial_folder(f)
            filter_images = Gtk.FileFilter()
            filter_images.set_name("Image Files")
            for ext in ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.gif", "*.webp"]:
                filter_images.add_pattern(ext)
            filters = Gio.ListStore.new(Gtk.FileFilter)
            filters.append(filter_images)
            dialog.set_filters(filters)
            dialog.open(self, None, self._on_single_image_chosen)
        else:
            dialog = Gtk.FileDialog()
            dialog.set_title("Select Folder with Images")
            dialog.select_folder(self, None, self._on_folder_chosen)

    def _on_single_image_chosen(self, dialog, result):
        try:
            gfile = dialog.open_finish(result)
        except GLib.Error:
            return
        path = gfile.get_path()
        if path:
            self.myimages = [path]
            self._refresh_listbox()
            self._update_reorder_buttons()
            self._update_action_buttons()

    def _on_folder_chosen(self, dialog, result):
        try:
            gfile = dialog.select_folder_finish(result)
        except GLib.Error:
            return
        folder_path = gfile.get_path()
        if not folder_path:
            return
        exts = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
        self.myimages = [
            os.path.join(folder_path, f)
            for f in sorted(os.listdir(folder_path))
            if os.path.splitext(f.lower())[1] in exts
        ]
        self._refresh_listbox()
        self._update_reorder_buttons()
        self._update_action_buttons()

    def _on_select_dest(self, _btn):
        dialog = Gtk.FileDialog()
        dialog.set_title("Select Destination Folder")
        dialog.select_folder(self, None, self._on_dest_chosen)

    def _on_dest_chosen(self, dialog, result):
        try:
            gfile = dialog.select_folder_finish(result)
        except GLib.Error:
            return
        path = gfile.get_path()
        if path:
            self.dest_folder_path = path
            self.dest_row.set_subtitle(path)
            self._update_action_buttons()

    def _on_move_up(self, _btn):
        idx = self._selected_row_index()
        if idx is None or idx == 0:
            return
        self.myimages[idx - 1], self.myimages[idx] = self.myimages[idx], self.myimages[idx - 1]
        self._refresh_listbox()
        row = self.image_listbox.get_row_at_index(idx - 1)
        if row:
            self.image_listbox.select_row(row)
        self._update_reorder_buttons()
        self._update_action_buttons()

    def _on_move_down(self, _btn):
        idx = self._selected_row_index()
        if idx is None or idx >= len(self.myimages) - 1:
            return
        self.myimages[idx + 1], self.myimages[idx] = self.myimages[idx], self.myimages[idx + 1]
        self._refresh_listbox()
        row = self.image_listbox.get_row_at_index(idx + 1)
        if row:
            self.image_listbox.select_row(row)
        self._update_reorder_buttons()
        self._update_action_buttons()

    def _on_remove(self, _btn):
        idx = self._selected_row_index()
        if idx is None:
            return
        self.myimages.pop(idx)
        self._refresh_listbox()
        self._update_reorder_buttons()
        self._update_action_buttons()

    def _on_generate_clicked(self, _btn):
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
            params["title"] = self.title_row.get_text().upper()
            params["city"] = self.city_row.get_text().upper()
            params["language"] = self._get_diapo_lang()
        elif mode == "Post":
            params["titre"] = self.post_title_row.get_text().upper()
            params["mot"] = self.word_row.get_text().upper()
            params["position"] = self._get_position()
            params["lang"] = self._get_post_lang()
            params["tsize"] = int(self.tsize_row.get_value())
            params["tspace"] = int(self.tspace_row.get_value())
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

    def _on_generate_done(self, elapsed: float, error: str | None):
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

    def _on_preview_clicked(self, _btn):
        if not self.myimages:
            self._show_error("Preview", "No image selected.")
            return
        if self._get_mode() != "Post":
            self._show_error("Preview", "Preview is only available in Post mode.")
            return
        titre = self.post_title_row.get_text().upper().strip()
        if not titre:
            self._show_error("Preview", "Please enter a title before previewing.")
            return
        mot = self.word_row.get_text().upper()
        try:
            pil_img = create_post(
                self.myimages[0], "preview", 1080, 1350,
                self._get_position(), titre, mot,
                self._get_post_lang(),
                int(self.tsize_row.get_value()),
                int(self.tspace_row.get_value()),
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
        dialog = Adw.AlertDialog(
            heading=title,
            body=message,
        )
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.present(self)

    def _show_error(self, title: str, message: str):
        dialog = Adw.AlertDialog(
            heading=title,
            body=message,
        )
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.present(self)


# ---------------------------------------------------------------------------
# Application entry point
# ---------------------------------------------------------------------------
class VictoriaApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.victoria.badazz",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self._on_activate)

    def _on_activate(self, app):
        win = VictoriaBadazz(app)
        win.present()


if __name__ == "__main__":
    app = VictoriaApp()
    sys.exit(app.run(sys.argv))