import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
import os

# Import OpenTelemetry
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.mysql import MySQLInstrumentor

# Konfigurasi koneksi MySQL
DB_CONFIG = {
    "host": "localhost",
    "user": "egaldragon",
    "password": "iskander8884",
    "database": "user_db",
    #Windows
    "auth_plugin": "caching_sha2_password",
}

# Inisialisasi OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Eksportir untuk menampilkan trace ke konsol
span_processor = SimpleSpanProcessor(ConsoleSpanExporter())
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrumentasi koneksi MySQL
MySQLInstrumentor().instrument()

def test_connection():
    """Menguji koneksi ke database sebelum menjalankan aplikasi."""
    try:
        with mysql.connector.connect(**DB_CONFIG) as conn:
            return True
    except mysql.connector.Error as e:
        messagebox.showerror("Database Error", f"Gagal terhubung ke database: {e}")
        return False

def fetch_users():
    """Mengambil data pengguna dari database."""
    with tracer.start_as_current_span("fetch-users-span"):
        try:
            with mysql.connector.connect(**DB_CONFIG) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM users")
                return cursor.fetchall()
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Gagal mengambil data: {e}")
            return []

def add_user():
    """Menambahkan pengguna baru ke database."""
    name = simpledialog.askstring("Tambah User", "Masukkan nama user:")
    if name:
        with tracer.start_as_current_span("add-user-span"):
            try:
                with mysql.connector.connect(**DB_CONFIG) as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (name) VALUES (%s)", (name,))
                    conn.commit()
                show_users()
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", f"Gagal menambah user: {e}")

def delete_user():
    """Menghapus pengguna dari database."""
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Hapus User", "Pilih user yang ingin dihapus.")
        return
    user_id = tree.item(selected_item, "values")[0]
    with tracer.start_as_current_span("delete-user-span"):
        try:
            with mysql.connector.connect(**DB_CONFIG) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                conn.commit()
            show_users()
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Gagal menghapus user: {e}")

def update_user():
    """Memperbarui nama pengguna di database."""
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Edit User", "Pilih user yang ingin diubah.")
        return
    user_id, old_name = tree.item(selected_item, "values")
    new_name = simpledialog.askstring("Edit User", "Masukkan nama baru:", initialvalue=old_name)
    if new_name and new_name != old_name:
        with tracer.start_as_current_span("update-user-span"):
            try:
                with mysql.connector.connect(**DB_CONFIG) as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET name = %s WHERE id = %s", (new_name, user_id))
                    conn.commit()
                show_users()
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", f"Gagal mengupdate user: {e}")

def show_users():
    """Menampilkan data pengguna di TreeView."""
    for row in tree.get_children():
        tree.delete(row)
    users = fetch_users()
    for user in users:
        tree.insert("", "end", values=user)

# Cek koneksi database sebelum menjalankan GUI
if not test_connection():
    exit()

# Setup GUI utama
root = tk.Tk()
root.title("User Viewer")
root.geometry("500x400")

# Path ikon yang kompatibel dengan Windows
icon_path = "myapp.png"
# Path ikon yang kompatibel dengan Linux
# icon_path = "/usr/share/icons/hicolor/128x128/apps/myapp.png"

# Cek apakah ikon ada dan atur sesuai platform
if os.path.exists(icon_path):
    img = tk.PhotoImage(file=icon_path)
    root.tk.call('wm', 'iconphoto', root._w, img)
else:
    print("Warning: Ikon tidak ditemukan! Menggunakan ikon default.")

title_label = tk.Label(root, text="Daftar User", font=("Arial", 14, "bold"))
title_label.pack(pady=10)

# Setup Treeview
tree = ttk.Treeview(root, columns=("ID", "Name"), show="headings")
tree.heading("ID", text="ID")
tree.heading("Name", text="Name")
tree.column("ID", width=50, anchor="center")
tree.column("Name", width=200, anchor="w")
tree.pack(pady=10, fill=tk.BOTH, expand=True)

# Tombol aksi
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

tk.Button(button_frame, text="Tambah", command=add_user).grid(row=0, column=0, padx=5)
tk.Button(button_frame, text="Hapus", command=delete_user).grid(row=0, column=1, padx=5)
tk.Button(button_frame, text="Edit", command=update_user).grid(row=0, column=2, padx=5)
tk.Button(button_frame, text="Refresh", command=show_users).grid(row=0, column=3, padx=5)

# Load data pertama kali
show_users()

root.mainloop()