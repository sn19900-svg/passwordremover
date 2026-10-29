"""
PDF Password Recovery Tool
---------------------------
أداة لاسترجاع/كسر كلمة سر ملفات PDF المحمية، عن طريق:
  1) هجوم القاموس (Dictionary Attack) - تجربة كلمات من ملف نصي
  2) القوة الغاشمة (Brute Force) - تجربة كل التركيبات الممكنة ضمن طول وخصائص محددة

مخصصة لاسترجاع كلمة سر لملفاتك الخاصة التي نسيتها أو لديك إذن بفتحها.

المتطلبات:
    pip install pikepdf

التشغيل:
    python pdf_password_recovery.py
"""

import itertools
import os
import string
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import pikepdf
except ImportError:
    pikepdf = None


class PasswordCrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Password Recovery")
        self.root.geometry("640x560")
        self.root.resizable(False, False)

        self.pdf_path = tk.StringVar()
        self.wordlist_path = tk.StringVar()
        self.output_path = tk.StringVar()

        self.mode = tk.StringVar(value="dictionary")  # dictionary | bruteforce
        self.min_len = tk.IntVar(value=1)
        self.max_len = tk.IntVar(value=4)
        self.use_lower = tk.BooleanVar(value=True)
        self.use_upper = tk.BooleanVar(value=False)
        self.use_digits = tk.BooleanVar(value=True)
        self.use_symbols = tk.BooleanVar(value=False)
        self.threads = tk.IntVar(value=max(2, os.cpu_count() or 2))

        self.stop_flag = threading.Event()
        self.found_password = None
        self.attempts = 0
        self.start_time = None

        self._build_ui()

    # ---------------- UI ----------------
    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # PDF file
        frm_file = tk.LabelFrame(self.root, text="ملف PDF المحمي")
        frm_file.pack(fill="x", **pad)
        tk.Entry(frm_file, textvariable=self.pdf_path, width=55).pack(side="left", padx=6, pady=6)
        tk.Button(frm_file, text="اختيار...", command=self.browse_pdf).pack(side="left", padx=6)

        if pikepdf is None:
            tk.Label(
                self.root,
                text="⚠ مكتبة pikepdf غير مثبّتة. شغّل: pip install pikepdf",
                fg="red",
            ).pack(**pad)

        # Mode
        frm_mode = tk.LabelFrame(self.root, text="طريقة الكسر")
        frm_mode.pack(fill="x", **pad)
        tk.Radiobutton(frm_mode, text="هجوم القاموس (Dictionary)", variable=self.mode,
                        value="dictionary", command=self._refresh_mode).pack(anchor="w")
        tk.Radiobutton(frm_mode, text="القوة الغاشمة (Brute Force)", variable=self.mode,
                        value="bruteforce", command=self._refresh_mode).pack(anchor="w")

        # Dictionary options
        self.frm_dict = tk.LabelFrame(self.root, text="ملف القاموس (كلمة بكل سطر)")
        self.frm_dict.pack(fill="x", **pad)
        tk.Entry(self.frm_dict, textvariable=self.wordlist_path, width=55).pack(side="left", padx=6, pady=6)
        tk.Button(self.frm_dict, text="اختيار...", command=self.browse_wordlist).pack(side="left", padx=6)

        # Brute force options
        self.frm_brute = tk.LabelFrame(self.root, text="إعدادات القوة الغاشمة")
        self.frm_brute.pack(fill="x", **pad)

        row1 = tk.Frame(self.frm_brute)
        row1.pack(fill="x", pady=4)
        tk.Label(row1, text="أقل طول:").pack(side="left", padx=4)
        tk.Spinbox(row1, from_=1, to=12, textvariable=self.min_len, width=5).pack(side="left")
        tk.Label(row1, text="أطول طول:").pack(side="left", padx=10)
        tk.Spinbox(row1, from_=1, to=12, textvariable=self.max_len, width=5).pack(side="left")

        row2 = tk.Frame(self.frm_brute)
        row2.pack(fill="x", pady=4)
        tk.Checkbutton(row2, text="أحرف صغيرة a-z", variable=self.use_lower).pack(side="left", padx=4)
        tk.Checkbutton(row2, text="أحرف كبيرة A-Z", variable=self.use_upper).pack(side="left", padx=4)
        tk.Checkbutton(row2, text="أرقام 0-9", variable=self.use_digits).pack(side="left", padx=4)
        tk.Checkbutton(row2, text="رموز !@#$", variable=self.use_symbols).pack(side="left", padx=4)

        row3 = tk.Frame(self.frm_brute)
        row3.pack(fill="x", pady=4)
        tk.Label(row3, text="عدد الخيوط (threads):").pack(side="left", padx=4)
        tk.Spinbox(row3, from_=1, to=16, textvariable=self.threads, width=5).pack(side="left")

        tk.Label(
            self.frm_brute,
            text="ملاحظة: كل خانة إضافية تزيد الوقت بشكل كبير جداً. يفضل تبدأ بطول صغير.",
            fg="gray", wraplength=580, justify="right",
        ).pack(pady=4)

        # Output
        frm_out = tk.LabelFrame(self.root, text="مكان حفظ الملف بعد فك الحماية")
        frm_out.pack(fill="x", **pad)
        tk.Entry(frm_out, textvariable=self.output_path, width=55).pack(side="left", padx=6, pady=6)
        tk.Button(frm_out, text="اختيار...", command=self.browse_output).pack(side="left", padx=6)

        # Progress
        self.progress_label = tk.Label(self.root, text="جاهز.")
        self.progress_label.pack(**pad)
        self.progress_bar = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress_bar.pack(fill="x", padx=10)

        # Buttons
        frm_btns = tk.Frame(self.root)
        frm_btns.pack(pady=14)
        self.start_btn = tk.Button(frm_btns, text="ابدأ", width=14, bg="#2e7d32", fg="white", command=self.start)
        self.start_btn.pack(side="left", padx=8)
        self.stop_btn = tk.Button(frm_btns, text="إيقاف", width=14, bg="#c62828", fg="white",
                                   command=self.stop, state="disabled")
        self.stop_btn.pack(side="left", padx=8)

        self._refresh_mode()

    def _refresh_mode(self):
        if self.mode.get() == "dictionary":
            self.frm_dict.pack(fill="x", padx=10, pady=6)
            self.frm_brute.pack_forget()
        else:
            self.frm_brute.pack(fill="x", padx=10, pady=6)
            self.frm_dict.pack_forget()

    # ---------------- File pickers ----------------
    def browse_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            self.pdf_path.set(path)
            if not self.output_path.get():
                base, ext = os.path.splitext(path)
                self.output_path.set(f"{base}_unlocked.pdf")

    def browse_wordlist(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            self.wordlist_path.set(path)

    def browse_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if path:
            self.output_path.set(path)

    # ---------------- Logic ----------------
    def start(self):
        if pikepdf is None:
            messagebox.showerror("خطأ", "مكتبة pikepdf غير مثبتة. شغّل: pip install pikepdf")
            return
        if not self.pdf_path.get() or not os.path.isfile(self.pdf_path.get()):
            messagebox.showerror("خطأ", "اختر ملف PDF صالح أولاً.")
            return
        if self.mode.get() == "dictionary" and not os.path.isfile(self.wordlist_path.get() or ""):
            messagebox.showerror("خطأ", "اختر ملف قاموس صالح.")
            return
        if not self.output_path.get():
            messagebox.showerror("خطأ", "حدد مكان حفظ الملف الناتج.")
            return

        self.stop_flag.clear()
        self.found_password = None
        self.attempts = 0
        self.start_time = time.time()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.progress_bar.start(10)

        thread = threading.Thread(target=self._run_cracker, daemon=True)
        thread.start()

    def stop(self):
        self.stop_flag.set()
        self.progress_label.config(text="جاري الإيقاف...")

    def _try_password(self, pwd):
        if self.stop_flag.is_set():
            return None
        try:
            with pikepdf.open(self.pdf_path.get(), password=pwd):
                return pwd
        except pikepdf.PasswordError:
            return None
        except Exception:
            return None

    def _candidate_generator(self):
        if self.mode.get() == "dictionary":
            with open(self.wordlist_path.get(), "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    yield line.rstrip("\n").rstrip("\r")
        else:
            charset = ""
            if self.use_lower.get():
                charset += string.ascii_lowercase
            if self.use_upper.get():
                charset += string.ascii_uppercase
            if self.use_digits.get():
                charset += string.digits
            if self.use_symbols.get():
                charset += "!@#$%^&*()-_=+"
            if not charset:
                charset = string.digits
            for length in range(self.min_len.get(), self.max_len.get() + 1):
                for combo in itertools.product(charset, repeat=length):
                    yield "".join(combo)

    def _run_cracker(self):
        found = None
        n_threads = max(1, self.threads.get())

        try:
            with ThreadPoolExecutor(max_workers=n_threads) as executor:
                futures = {}
                gen = self._candidate_generator()
                batch_size = n_threads * 50

                while not self.stop_flag.is_set():
                    batch = list(itertools.islice(gen, batch_size))
                    if not batch:
                        break
                    futures = {executor.submit(self._try_password, pwd): pwd for pwd in batch}
                    for fut in as_completed(futures):
                        self.attempts += 1
                        if self.attempts % 25 == 0:
                            self._update_progress()
                        result = fut.result()
                        if result is not None:
                            found = result
                            self.stop_flag.set()
                            break
                    if found:
                        break
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("خطأ", str(e)))

        self.found_password = found
        self.root.after(0, self._finish)

    def _update_progress(self):
        elapsed = time.time() - self.start_time
        rate = self.attempts / elapsed if elapsed > 0 else 0
        text = f"عدد المحاولات: {self.attempts}  |  السرعة: {rate:.0f} محاولة/ثانية"
        self.root.after(0, lambda: self.progress_label.config(text=text))

    def _finish(self):
        self.progress_bar.stop()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

        if self.found_password is not None:
            self.progress_label.config(text=f"✅ تم العثور على كلمة السر: {self.found_password}")
            try:
                with pikepdf.open(self.pdf_path.get(), password=self.found_password) as pdf:
                    pdf.save(self.output_path.get())
                messagebox.showinfo(
                    "تم بنجاح",
                    f"كلمة السر: {self.found_password}\n\nتم حفظ نسخة بدون حماية في:\n{self.output_path.get()}",
                )
            except Exception as e:
                messagebox.showerror("خطأ بالحفظ", str(e))
        else:
            if self.stop_flag.is_set() and self.attempts > 0:
                self.progress_label.config(text="تم الإيقاف يدوياً دون إيجاد كلمة السر.")
            else:
                self.progress_label.config(text="❌ لم يتم إيجاد كلمة السر ضمن النطاق المحدد.")
                messagebox.showwarning(
                    "لم يتم الإيجاد",
                    "لم يتم العثور على كلمة السر. جرب قاموس أكبر أو وسّع نطاق القوة الغاشمة.",
                )


def main():
    root = tk.Tk()
    app = PasswordCrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
