import random
import sys
import time
import threading
from pathlib import Path
from pynput import keyboard

# ---------- Конфиг ----------
CSGO_CFG_PATH_PARTS = (
    "steamapps",
    "common",
    "Counter-Strike Global Offensive",
    "game",
    "csgo",
    "cfg",
)

PLAYSOUND = [
    r"play \sounds\ui\csgo_ui_crate_item_scroll.vsnd_c",
    r"play \sounds\ui\item_reveal3_rare.vsnd_c",
    r"play \sounds\ui\item_reveal4_mythical.vsnd_c",
    r"play \sounds\ui\item_reveal5_legendary.vsnd_c",
    r"play \sounds\ui\item_reveal6_ancient.vsnd_c",
]

APPLICATION_PATH = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve()
CONFIG_PATH = APPLICATION_PATH.parent / "random_crosshair.cfg"
KEY_PRESS_DURATION = 0.05
TRIGGER_KEY_VK = 0x50  # P
APPLY_KEY = keyboard.KeyCode.from_vk(0x4F)  # O

# ---------- Генераторы ----------
def _gen_crosshair_body(playsound_index=None):
    """Общая логика генерации. playsound_index=None -> случайный трек."""
    style = random.randint(0, 9)

    CROSSHAIR_RGBA = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), None]
    if random.choice([0, 1]) == 1:
        CROSSHAIR_RGBA[3] = random.randint(0, 255)
    else:
        CROSSHAIR_RGBA[3] = 255

    outline_type = random.choice([0, 1, 2])

    if random.choice([0, 1]) == 1:
        OUTLINE_RGBA = list(CROSSHAIR_RGBA)
    else:
        OUTLINE_RGBA = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), None]
        if random.choice([0, 1]) == 1:
            OUTLINE_RGBA[3] = random.randint(0, 255)
        else:
            OUTLINE_RGBA[3] = 255

    thickness = random.randint(0, 32)
    dot = random.choice([0, 1])
    length = random.randint(0, 255)
    gap = random.randint(0, 500)
    t = random.choice([0, 1])
    ironsight_color = random.choice([0, 1])
    ironsight_dot_scale = round(random.uniform(0.10, 2.0), 2)
    recoil = random.choice([0, 1])
    if random.choice([0, 1]) == 1:
        sniper_width = random.randint(-1, 20)
    else:
        sniper_width = random.randint(20, 700)

    if playsound_index is None:
        playsound_index = random.randint(1, len(PLAYSOUND) - 1)

    return {
        "cl_crosshairstyle": style,
        "cl_crosshaircolor_r": CROSSHAIR_RGBA[0],
        "cl_crosshaircolor_g": CROSSHAIR_RGBA[1],
        "cl_crosshaircolor_b": CROSSHAIR_RGBA[2],
        "cl_crosshaircolor_a": CROSSHAIR_RGBA[3],
        "cl_crosshair_drawoutline": outline_type,
        "cl_crosshairoutline_r": OUTLINE_RGBA[0],
        "cl_crosshairoutline_g": OUTLINE_RGBA[1],
        "cl_crosshairoutline_b": OUTLINE_RGBA[2],
        "cl_crosshairoutline_a": OUTLINE_RGBA[3],
        "cl_crosshair_thickness": thickness,
        "cl_crosshairdot": dot,
        "cl_crosshair_length": length,
        "cl_crosshair_gap": gap,
        "cl_crosshair_t": t,
        "cl_ironsight_usecrosshaircolor": ironsight_color,
        "cl_ironsight_dot_scale": ironsight_dot_scale,
        "cl_crosshair_recoil": recoil,
        "cl_crosshair_sniper_width": sniper_width,
        "snd_toolvolume": 0.3,
        PLAYSOUND[playsound_index]: "",
    }

def gen_crosshair_temp():
    """Временный прицел (звук = первый)."""
    return _gen_crosshair_body(playsound_index=0)


def gen_crosshair_final():
    """Основной прицел (случайный звук)."""
    return _gen_crosshair_body(playsound_index=None)


def gen_viewmodel():
    return {
        "viewmodel_fov": random.randint(54, 68),
        "viewmodel_offset_x": round(random.uniform(-2.5, 2.5), 2),
        "viewmodel_offset_y": round(random.uniform(-2.0, 2.0), 2),
        "viewmodel_offset_z": round(random.uniform(-2.0, 2.0), 2),
    }

def gen_hud_and_radar():
    return {
        "cl_hud_color": random.randint(0, 11),
        "hud_scaling": round(random.uniform(0.9, 1.1), 2),
        "cl_radar_always_centered": random.choice([0, 1]),
        "cl_radar_scale": round(random.uniform(0.25, 1), 2),
        "cl_hud_radar_scale": round(random.uniform(0.8, 1.3), 2),
        "cl_radar_icon_scale_min": round(random.uniform(0.4, 1.25), 2),
        "cl_radar_rotate": random.choice([0, 1]),
        "cl_radar_square_with_scoreboard": random.choice([0, 1]),
        "cl_teamcounter_playercount_instead_of_avatars": random.choice([0, 1]),
        "cl_weapon_selection_rarity_color": random.choice([0, 1]),
        "cl_teammate_colors_show": random.randint(0, 2),
        "cl_teamid_overhead_mode": random.randint(0, 3),
        "cl_teamid_overhead_colors_show": random.choice([0, 1]),
    }

# ---------- Запись в файл ----------
def write_config(crosshair, viewmodel, hud_and_radar, path=CONFIG_PATH):
    lines = ["// Auto-generated CS2 crosshair + viewmodel config", ""]
    lines.append("// --- Crosshair ---")
    for k, v in crosshair.items():
        lines.append(f"{k} {v}")
    lines.append("")
    lines.append("// --- Viewmodel ---")
    for k, v in viewmodel.items():
        lines.append(f"{k} {v}")
    lines.append("")
    lines.append("// --- HUD and Radar ---")
    for k, v in hud_and_radar.items():
        lines.append(f"{k} {v}")
    lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------- Нажатия клавиш ----------
kb = keyboard.Controller()

def press_key(key):
    kb.press(key)
    try:
        time.sleep(KEY_PRESS_DURATION)
    finally:
        kb.release(key)


# ---------- "Рулетка" ----------
def spin_reveal():
    """
    1) Крутит временные прицелы с затухающей частотой (как кейс в CS2).
    2) В конце — финальный прицел + нажатие 'i'.
    """
    # Сколько временных шагов и с каким затуханием
    # (суммарно ~ как открытие кейса: быстро -> медленно)
    delays = [0.05, 0.05, 0.06, 0.07, 0.08, 0.10, 0.13, 0.17,
              0.22, 0.28, 0.36, 0.45, 0.55, 0.65]

    # Фаза 1: быстрые временные прицелы
    for d in delays:
        viewmodel = gen_viewmodel()
        crosshair = gen_crosshair_temp()
        hud_and_radar = gen_hud_and_radar()
        write_config(crosshair, viewmodel, hud_and_radar)
        press_key(APPLY_KEY)
        time.sleep(d)

    # Фаза 2: финальный основной прицел
    viewmodel = gen_viewmodel()
    crosshair = gen_crosshair_final()
    hud_and_radar = gen_hud_and_radar()
    write_config(crosshair, viewmodel, hud_and_radar)
    press_key(APPLY_KEY)

    print("[OK] Основной прицел сгенерирован и записан.")
    print("\n".join(f"{k} {v}" for k, v in crosshair.items()))


# ---------- Слушатель клавиш ----------
_spinning = False
_lock = threading.Lock()


def _is_in_csgo_cfg(application_path):
    parent_parts = Path(application_path).resolve().parent.parts
    expected_parts = tuple(part.casefold() for part in CSGO_CFG_PATH_PARTS)
    actual_parts = tuple(part.casefold() for part in parent_parts[-len(expected_parts):])
    return actual_parts == expected_parts


def on_press(key):
    global _spinning
    try:
        if getattr(key, 'vk', None) == TRIGGER_KEY_VK:
            with _lock:
                if _spinning:
                    print("[!] Уже идёт генерация, подожди.")
                    return
                _spinning = True
            threading.Thread(target=_spin_wrapper, daemon=True).start()
    except Exception as e:
        print("Ошибка в обработчике:", e)


def _spin_wrapper():
    global _spinning
    try:
        spin_reveal()
    except Exception as e:
        print("[!] Ошибка при генерации:", e)
    finally:
        with _lock:
            _spinning = False


if __name__ == "__main__":
    application_path = sys.executable if getattr(sys, "frozen", False) else __file__
    if not _is_in_csgo_cfg(application_path):
        print(
            "[!] Переместите приложение в папку "
            "steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\cfg."
        )
        input("Нажмите Enter для выхода...")
        raise SystemExit(1)

    print("Не забудь забиндить применение создаваемого конфига (bind o \"exec random_crosshair.cfg\")")
    print("Нажми 'P' чтобы запустить рулетку HUD.")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()