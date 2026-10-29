import re
import tkinter as tk
from tkinter import ttk, messagebox


def parse_console_lines(text: str) -> str:
    pattern = re.compile(
        r"\[Console\]\s*([A-Za-z0-9_]+)\s*=\s*(.*?)(?=\[Console\]|$)",
        re.DOTALL,
    )

    pairs = []
    for match in pattern.finditer(text):
        name = match.group(1).strip()
        value = match.group(2).rstrip(";").strip()
        pairs.append(f"{name} {value}")

    return "; ".join(pairs) + (";" if pairs else "")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CS2 Console Parser")
        self.geometry("800x600")
        self.minsize(600, 400)

        self._build_ui()

    def _build_ui(self):
        # Верхняя панель с кнопками
        toolbar = ttk.Frame(self, padding=(8, 8, 8, 0))
        toolbar.pack(fill="x")

        ttk.Button(toolbar, text="Обработать", command=self.on_parse).pack(side="left")
        ttk.Button(toolbar, text="Из буфера обмена", command=self.on_paste).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Копировать результат", command=self.on_copy).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Очистить", command=self.on_clear).pack(side="left", padx=(8, 0))

        # Метка + поле ввода
        ttk.Label(self, text="Входной текст ([Console] ...):", padding=(8, 8, 8, 0)).pack(anchor="w")
        input_frame = ttk.Frame(self, padding=(8, 0, 8, 0))
        input_frame.pack(fill="both", expand=True)

        self.input_text = tk.Text(input_frame, wrap="word", height=10, undo=True)
        input_scroll = ttk.Scrollbar(input_frame, orient="vertical", command=self.input_text.yview)
        self.input_text.configure(yscrollcommand=input_scroll.set)
        self.input_text.pack(side="left", fill="both", expand=True)
        input_scroll.pack(side="right", fill="y")

        # Метка + поле результата
        ttk.Label(self, text="Результат:", padding=(8, 8, 8, 0)).pack(anchor="w")
        output_frame = ttk.Frame(self, padding=(8, 0, 8, 8))
        output_frame.pack(fill="both", expand=True)

        self.output_text = tk.Text(output_frame, wrap="word", height=10, undo=True)
        output_scroll = ttk.Scrollbar(output_frame, orient="vertical", command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=output_scroll.set)
        self.output_text.pack(side="left", fill="both", expand=True)
        output_scroll.pack(side="right", fill="y")

        # Статус-бар
        self.status = tk.StringVar(value="Готово")
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w", padding=(6, 2)).pack(fill="x", side="bottom")

    # --- handlers ---
    def on_parse(self):
        raw = self.input_text.get("1.0", "end").strip()
        if not raw:
            self.status.set("Пустой ввод — нечего обрабатывать.")
            return

        result = parse_console_lines(raw)
        if not result:
            self.output_text.delete("1.0", "end")
            self.status.set("Не найдено ни одного параметра в формате [Console] name = value")
            messagebox.showwarning("Ничего не найдено",
                                   "Во входных данных не найден ни один параметр вида\n"
                                   "[Console] name = value")
            return

        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", result)

        count = result.count("=")
        self.status.set(f"Обработано параметров: {count}")

    def on_paste(self):
        try:
            data = self.clipboard_get()
        except tk.TclError:
            self.status.set("Буфер обмена пуст.")
            return
        self.input_text.insert("insert", data)
        self.status.set("Вставлено из буфера обмена.")

    def on_copy(self):
        result = self.output_text.get("1.0", "end").strip()
        if not result:
            self.status.set("Результат пуст — нечего копировать.")
            return
        self.clipboard_clear()
        self.clipboard_append(result)
        self.status.set("Результат скопирован в буфер обмена.")

    def on_clear(self):
        self.input_text.delete("1.0", "end")
        self.output_text.delete("1.0", "end")
        self.status.set("Очищено.")


if __name__ == "__main__":
    App().mainloop()