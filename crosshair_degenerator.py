import random
import keyboard

CROSSHAIR_RGBA = None
OUTLINE_RGBA = None
PLAYSOUND = [
    r"play \sounds\ui\csgo_ui_crate_item_scroll.vsnd_c",
    r"play \sounds\ui\item_reveal3_rare.vsnd_c",
    r"play \sounds\ui\item_reveal4_mythical.vsnd_c",
    r"play \sounds\ui\item_reveal5_legendary.vsnd_c",
    r"play \sounds\ui\item_reveal6_ancient.vsnd_c"
]

def gen_crosshair():
    style = random.randint(0, 10) #???
    
    CROSSHAIR_RGBA = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), None]
    crosshair_transparency = random.choice([0, 1])
    if crosshair_transparency == 1:
        CROSSHAIR_RGBA[3] = random.randint(0, 255)
    else:
        CROSSHAIR_RGBA[3] = 255
        
    outline_type = random.choice([0, 1, 2]) #жестко
    
    outline_matches_crosshair = random.choice([0, 1])
    if outline_matches_crosshair == 1:
        OUTLINE_RGBA = CROSSHAIR_RGBA
    else:
        OUTLINE_RGBA = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), None]
        outline_transparency = random.choice([0, 1])
        if outline_transparency == 1:
            OUTLINE_RGBA[3] = random.randint(0, 255)
        else:
            OUTLINE_RGBA[3] = 255

    thickness = random.randint(0, 32) #жестко
    dot = random.choice([0, 1]) #жестко
    length = random.randint(0, 255) #жестко
    gap = random.randint(0, 500) #можно выше
    t = random.choice([0, 1])
    ironsight_color = random.choice([0, 1])
    ironsight_dot_scale = round(random.uniform(0.10, 2.0), 2) #жестко
    recoil = random.choice([0, 1])
    sniper_width = random.randint(-1, 700) #можно выше

    return {
        "snd_toolvolume": 0.3,
        PLAYSOUND[random.randint(1, len(PLAYSOUND) - 1)]: "",
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
    }

def gen_viewmodel():
    return {
        "viewmodel_fov": random.randint(54, 68),
        "viewmodel_offset_x": round(random.uniform(-2.5, 2.5), 2),
        "viewmodel_offset_y": round(random.uniform(-2.0, 2.0), 2),
        "viewmodel_offset_z": round(random.uniform(-2.0, 2.0), 2),
    }


def main():
    print("Press 0 to exit")
    print("Press P to degenerate")

    while 1==1:
        if keyboard.is_pressed('0'):
            break
        if keyboard.is_pressed('P'):
            crosshair = gen_crosshair()
            viewmodel = gen_viewmodel()

            lines = ["// Auto-generated CS2 crosshair + viewmodel config", ""]
            lines.append("// --- Crosshair ---")
            for k, v in crosshair.items():
                lines.append(f"{k} {v}")

            lines.append("")
            lines.append("// --- Viewmodel ---")
            for k, v in viewmodel.items():
                lines.append(f"{k} {v}")

            lines.append("")

            with open("random_crosshair.cfg", "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            print("Сгенерирован random_crosshair.cfg:")
            print("\n".join(lines))


if __name__ == "__main__":
    main()