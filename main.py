import os
import flet as ft
import crosshair_degenerator as cd
import threading
from pynput import keyboard

TRIGGER_KEY_VK = 0xBB  # клавиша "="
_TRIGGER_FIELD_REF = None
_TRIGGER_CAPTURE_ACTIVE = False

# ---------- Обработчик клавиш ----------
_GENERATING = False
_LOCK = threading.Lock()
_KEYBOARD = keyboard.Controller()


def _start_trigger_key_capture(field: ft.TextField):
    global _TRIGGER_FIELD_REF, _TRIGGER_CAPTURE_ACTIVE
    _TRIGGER_FIELD_REF = field
    _TRIGGER_CAPTURE_ACTIVE = True


def _stop_trigger_key_capture():
    global _TRIGGER_CAPTURE_ACTIVE
    _TRIGGER_CAPTURE_ACTIVE = False


def _apply_trigger_key_value(vk: int):
    global TRIGGER_KEY_VK
    TRIGGER_KEY_VK = vk
    if _TRIGGER_FIELD_REF is not None:
        _TRIGGER_FIELD_REF.value = f"0x{vk:X}"
        _TRIGGER_FIELD_REF.update()


def _parse_trigger_key_value(raw_value: str) -> int:
    value = (raw_value or "").strip()
    if not value:
        raise ValueError("Пустое значение")
    try:
        return int(value, 0)
    except ValueError:
        return int(value, 16)


def build_settings_page(page: ft.Page):
    
    def go_back_local(e = None):
        if len(page.views) > 1:
            page.views.pop()
            page.update()

    trigger_field = ft.TextField(
        label="Кнопка дегенерации",
        value=f"0x{TRIGGER_KEY_VK:X}",
        width=180,
        on_focus=lambda e: _start_trigger_key_capture(trigger_field),
        on_blur=lambda e: _stop_trigger_key_capture(),
    )

    def save_settings(e):
        try:
            global TRIGGER_KEY_VK
            TRIGGER_KEY_VK = _parse_trigger_key_value(trigger_field.value)
            page.show_snack_bar(ft.SnackBar(ft.Text("Настройки сохранены")))
        except ValueError:
            page.show_snack_bar(
                ft.SnackBar(ft.Text("Введите корректные значения в hex или int формате"))
            )

    settings = [
        (
            "Кнопка дегенерации",
            trigger_field,
        )
    ]

    grid_controls = []
    for label_text, field in settings:
        grid_controls.append(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(label_text, width=220, weight=ft.FontWeight.W_500),
                        field,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=10,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                border=ft.Border.all(1, ft.Colors.OUTLINE),
                border_radius=8,
            )
        )

    return ft.View(
        route="/settings",
        controls=[
            ft.AppBar(
                title=ft.Text("Настройки"),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=go_back_local,
                ),
            ),
            ft.Container(
                content=ft.GridView(
                    expand=True,
                    runs_count=1,
                    max_extent=500,
                    child_aspect_ratio=2.4,
                    spacing=10,
                    run_spacing=10,
                    controls=grid_controls,
                ),
                padding=10,
                expand=True,
            ),
            ft.Row(
                controls=[
                    ft.Button("Сохранить", on_click = save_settings),
                ],
                alignment=ft.MainAxisAlignment.END,
                width=500,
            ),
        ],
    )


async def main(page: ft.Page):
    def open_section(title: str, route: str):
        if route == "/settings":
            page.views.append(build_settings_page(page))
        else:
            page.views.append(
                ft.View(
                    route=route,
                    appbar=ft.AppBar(
                        title=ft.Text(title),
                        leading=ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            on_click=lambda e: go_back(),
                        ),
                    ),
                    controls=[
                        ft.Text("Раздел подготовлен для дальнейшего оформления."),
                    ],
                )
            )
        page.update()

    def go_back(e=None):
        if len(page.views) > 1:
            page.views.pop()
            page.update()

    def generate_crosshair():
        global _GENERATING
        with _LOCK:
            if _GENERATING:
                print("[!] Генерация уже запущена")
                return
            _GENERATING = True
        try:
            cfg = cd.gen_crosshair()
            page.add(ft.Text(str(cfg)))
            page.update()
        finally:
            with _LOCK:
                _GENERATING = False

    # Инициализация окна
    icon_path = os.path.join(os.path.dirname(__file__), "./src/images/icon.ico")
    page.title = "HUD дегенератор"
    page.window.icon = icon_path

    page.views.append(
        ft.View(
            route="/",
            controls=[
                ft.Text(
                    "[!] Эта хуйня полностью сломает твой HUD, если ты еще не понял. Так что сделай копию своего конфига."
                ),
                ft.Text(
                    "[!] Для работы программы нужно вручную забиндить применение изменений (bind o \"exec random_crosshair.cfg\")"
                ),
                ft.Text("Нажми '=' чтобы запустить рулетку HUD."),
                ft.Button(
                    content="Настройки",
                    on_click=lambda e: open_section("Настройки", "/settings"),
                ),
                ft.Button(
                    content="История дегенерации",
                    on_click=lambda e: open_section(
                        "История дегенерации", "/degeneration-history"
                    ),
                ),
                ft.Button(
                    content="Сдегенерировать (\"=\")",
                    on_click=lambda e: generate_crosshair(),
                ),
            ],
        )
    )

    page.update()


def on_press(key):
    global _GENERATING
    global _LOCK
    try:
        vk = getattr(key, 'vk', None)

        if _TRIGGER_CAPTURE_ACTIVE and _TRIGGER_FIELD_REF is not None and vk is not None:
            _apply_trigger_key_value(vk)
            _stop_trigger_key_capture()
            return

        if vk == TRIGGER_KEY_VK:
            with _LOCK:
                if _GENERATING:
                    print("[!] Повторное нажатие недуступно, генерация уже запущена")
                    return
                _GENERATING = True
            threading.Thread(target=cd._spin_wrapper, daemon=True).start()
    except Exception as e:
        print("[!] Ошибка в обработчике:", e)
    finally:
        _GENERATING = False


def start_keyboard_listener():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


if __name__ == "__main__":
    threading.Thread(target=start_keyboard_listener, daemon=True).start()
    ft.run(main)


