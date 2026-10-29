<<<<<<< HEAD
import re
import struct

DICTIONARY = "ABCDEFGHJKLMNOPQRSTUVWXYZabcdefhijkmnopqrstuvwxyz23456789"
DICT_LEN = len(DICTIONARY)  # 57

CODE_RE = re.compile(r"^(CSGO(-[\w]{5}){5}|CS[A-Za-z0-9]{44})$")
CS2_CODE_RE = re.compile(r"^CS[A-Za-z0-9]{44}$")

CS2_VERSION = 5
STYLE_NAMES = ["Default", "Default Static", "Classic", "Classic Dynamic", "Classic Static", "Legacy"]
PIXEL_STYLE_NAMES = ["Dynamic Cross", "Dynamic Circle", "Classic Dynamic", "Static Circle",
                     "Static Cross", "Static Cross (Shot Feedback)", "Dot Only",
                     "Dynamic Quadrant", "Static Square", "Static Quadrant"]
OUTLINE_MODES = ["Off", "Full", "Half"]
COLOR_NAMES = ["Red", "Green", "Yellow", "Blue", "Cyan", "Custom"]


# ---------- float32 helpers ----------
def f32(x: float) -> float:
    return struct.unpack("<f", struct.pack("<f", x))[0]

HUNDREDTH = f32(0.01)

def pct(v: float, offset: float = 0.0) -> float:
    x = f32(v * HUNDREDTH)
    return f32(x + f32(offset)) if offset else x

def roundf(x: float) -> int:
    return int(x + 0.5) if x >= 0 else -int(-x + 0.5)


def uint8_to_int8(v: int) -> int:
    return v - 256 if v >= 128 else v


# ---------- base-N ↔ bytes ----------
def share_code_to_bytes(code: str):
    if not CODE_RE.match(code):
        return None
    is_cs2 = bool(CS2_CODE_RE.match(code))
    chars = list(code[2:] if is_cs2 else re.sub(r"CSGO|-", "", code))[::-1]
    big = 0
    for ch in chars:
        i = DICTIONARY.find(ch)
        if i < 0:
            return None
        big = big * DICT_LEN + i
    size = 32 if is_cs2 else 18
    h = format(big, "x")
    if len(h) > size * 2:
        return None
    return bytes.fromhex(h.rjust(size * 2, "0"))


def bytes_to_share_code(b: bytes) -> str:
    total = int.from_bytes(b, "big")
    chars = []
    for _ in range(44):
        chars.append(DICTIONARY[total % DICT_LEN])
        total //= DICT_LEN
    return "CS" + "".join(chars)


# ---------- decoders ----------
def decode_crosshair(code: str):
    r = share_code_to_bytes(code)
    if r is None:
        return None
    if (sum(r[1:]) & 0xFF) != r[0]:
        return None
    if len(r) == 32:
        if r[1] == 1 and (r[2] | (r[3] << 8)):
            return decode_cs2_crosshair(r)
        return None
    if r[1] == 1:
        return decode_crosshair_v1(r)
    if r[1] in (3, 4):
        return decode_pixel_crosshair(r)
    return None


def decode_crosshair_v1(r: bytes) -> dict:
    return {
        "version": 1,
        "gap": uint8_to_int8(r[2]) / 10,
        "outline": r[3] / 2,
        "red": r[4], "green": r[5], "blue": r[6], "alpha": r[7],
        "splitDistance": r[8] & 7,
        "followRecoil": ((r[8] >> 4) & 8) == 8,
        "fixedCrosshairGap": uint8_to_int8(r[9]) / 10,
        "color": r[10] & 7,
        "outlineEnabled": (r[10] & 8) == 8,
        "innerSplitAlpha": (r[10] >> 4) / 10,
        "outerSplitAlpha": (r[11] & 0xF) / 10,
        "splitSizeRatio": (r[11] >> 4) / 10,
        "thickness": r[12] / 10,
        "centerDotEnabled": ((r[13] >> 4) & 1) == 1,
        "deployedWeaponGapEnabled": ((r[13] >> 4) & 2) == 2,
        "alphaEnabled": ((r[13] >> 4) & 4) == 4,
        "tStyleEnabled": ((r[13] >> 4) & 8) == 8,
        "style": (r[13] & 0xF) >> 1,
        "length": r[14] / 10,
    }


def decode_pixel_crosshair(r: bytes) -> dict:
    bits = r[10] | (r[11] << 8) | (r[12] << 16) | (r[13] << 24)
    if r[1] == 4:
        outline_mode = (r[13] >> 4) & 3
    else:
        outline_mode = 1 if (r[2] & 0x20) else 0
    return {
        "version": r[1],
        "style": r[2] & 0xF,
        "followRecoil": (r[2] & 0x10) == 0x10,
        "centerDotEnabled": (r[2] & 0x40) == 0x40,
        "tStyleEnabled": (r[2] & 0x80) == 0x80,
        "red": r[3], "green": r[4], "blue": r[5], "alpha": r[6],
        "gap": r[7],
        "length": r[8],
        "dynamicSpreadLimit": r[9],
        "splitDistance": bits & 0x7F,
        "innerSplitAlpha": pct(roundf(((bits >> 7) & 0x1F) * 0.05 / 0.01)),
        "outerSplitAlpha": pct(roundf(((bits >> 12) & 0xF) * 0.05 / 0.01), 0.3),
        "splitSizeRatio": pct((bits >> 16) & 0x7F),
        "thickness": (bits >> 23) & 0x1F,
        "screenHeight": r[14] | (r[15] << 8),
        "outlineMode": outline_mode,
        "color": 5,
        "alphaEnabled": True,
        "outlineEnabled": outline_mode != 0,
        "outline": 1 if outline_mode else 0,
    }


def decode_cs2_crosshair(r: bytes) -> dict:
    bits = (r[18] | (r[19] << 8) | (r[20] << 16) | (r[21] << 24)) & 0xFFFFFFFF
    gap = r[14] | (r[15] << 8)
    if gap & 0x8000:
        gap -= 0x10000
    outline_mode = min(r[13] >> 6, 2)
    return {
        "version": CS2_VERSION,
        "screenHeight": max(240, r[2] | (r[3] << 8)),
        "style": min(r[4] & 0x1F, 9),
        "followRecoil": bool(r[4] & 0x20),
        "centerDotEnabled": bool(r[4] & 0x40),
        "tStyleEnabled": bool(r[4] & 0x80),
        "red": r[5], "green": r[6], "blue": r[7], "alpha": r[8],
        "outlineRed": r[9], "outlineGreen": r[10], "outlineBlue": r[11], "outlineAlpha": r[12],
        "thickness": min(r[13] & 0x3F, 32),
        "outlineMode": outline_mode,
        "gap": max(-3840, min(gap, 3840)),
        "length": r[16],
        "dynamicSpreadLimit": r[17],
        "splitDistance": min(bits & 0x7F, 127),
        "innerSplitAlpha": pct(min((bits >> 7) & 0x7F, 100)),
        "outerSplitAlpha": pct(min((bits >> 14) & 0x7F, 70), 0.3),
        "splitSizeRatio": pct(min((bits >> 21) & 0x7F, 100)),
        "scopeDotUseColor": bool(bits & 0x10000000),
        "scopeDotScale": pct(min(r[22], 190), 0.1),
        "color": 5,
        "alphaEnabled": True,
        "outlineEnabled": outline_mode != 0,
        "outline": 1 if outline_mode else 0,
    }


# ---------- encoder (только новый "CS"-формат, как в CS2) ----------
def clamp_int(v, lo, hi) -> int:
    return max(lo, min(int(round(v)), hi))


def pct_byte(v: float, lo: float, hi: float) -> int:
    v = min(max(v, lo), hi)
    return roundf(f32(f32(v - lo) / HUNDREDTH))


def encode_crosshair(cfg: dict) -> str:
    alpha = clamp_int(cfg.get("alpha", 255), 0, 255)
    gap_u = clamp_int(cfg.get("gap", 0), -3840, 3840) & 0xFFFF
    h = clamp_int(cfg.get("screenHeight", 1080), 0, 65535)

    bits = (
        clamp_int(cfg.get("splitDistance", 35), 0, 127)
        | (pct_byte(cfg.get("innerSplitAlpha", 0.0), 0.0, 1.0) << 7)
        | (pct_byte(cfg.get("outerSplitAlpha", 0.3), f32(0.3), 1.0) << 14)
        | (pct_byte(cfg.get("splitSizeRatio", 0.5), 0.0, 1.0) << 21)
        | (0x10000000 if cfg.get("scopeDotUseColor") else 0)
    ) & 0xFFFFFFFF

    oa = cfg.get("outlineAlpha")
    oa = alpha if oa is None else clamp_int(oa, 0, 255)

    style_byte = (
        clamp_int(cfg.get("style", 0), 0, 9)
        | (0x20 if cfg.get("followRecoil") else 0)
        | (0x40 if cfg.get("centerDotEnabled") else 0)
        | (0x80 if cfg.get("tStyleEnabled") else 0)
    )
    thick_byte = clamp_int(cfg.get("thickness", 1), 0, 32) | (clamp_int(cfg.get("outlineMode", 0), 0, 2) << 6)

    bytes_ = [
        0, 1, h & 0xFF, (h >> 8) & 0xFF,
        style_byte,
        clamp_int(cfg.get("red", 0), 0, 255),
        clamp_int(cfg.get("green", 255), 0, 255),
        clamp_int(cfg.get("blue", 0), 0, 255),
        alpha,
        clamp_int(cfg.get("outlineRed", 0) or 0, 0, 255),
        clamp_int(cfg.get("outlineGreen", 0) or 0, 0, 255),
        clamp_int(cfg.get("outlineBlue", 0) or 0, 0, 255),
        oa,
        thick_byte,
        gap_u & 0xFF, (gap_u >> 8) & 0xFF,
        clamp_int(cfg.get("length", 5), 0, 255),
        clamp_int(cfg.get("dynamicSpreadLimit", 100), 0, 255),
        bits & 0xFF, (bits >> 8) & 0xFF, (bits >> 16) & 0xFF, (bits >> 24) & 0xFF,
        pct_byte(cfg.get("scopeDotScale", 1.0), f32(0.1), 2.0),
        0, 0, 0, 0, 0, 0, 0, 0, 0,
    ]
    bytes_[0] = sum(bytes_[1:]) & 0xFF
    return bytes_to_share_code(bytes(bytes_))


# ---------- демо ----------
if __name__ == "__main__":
    cfg = {
        "style": 0, "followRecoil": False, "centerDotEnabled": True,
        "tStyleEnabled": False,
        "red": 0, "green": 255, "blue": 0, "alpha": 255,
        "outlineRed": 0, "outlineGreen": 0, "outlineBlue": 0, "outlineAlpha": 200,
        "thickness": 1, "outlineMode": 1,
        "gap": -5, "length": 5, "dynamicSpreadLimit": 100,
        "splitDistance": 35, "innerSplitAlpha": 0.0,
        "outerSplitAlpha": 0.3, "splitSizeRatio": 0.5,
        "screenHeight": 1080,
        "scopeDotUseColor": False, "scopeDotScale": 1.0,
    }
    code = encode_crosshair(cfg)
    print("encoded:", code)

    decoded = decode_crosshair(code)
    print("decoded:")
    for k, v in decoded.items():
=======
import re
import struct

DICTIONARY = "ABCDEFGHJKLMNOPQRSTUVWXYZabcdefhijkmnopqrstuvwxyz23456789"
DICT_LEN = len(DICTIONARY)  # 57

CODE_RE = re.compile(r"^(CSGO(-[\w]{5}){5}|CS[A-Za-z0-9]{44})$")
CS2_CODE_RE = re.compile(r"^CS[A-Za-z0-9]{44}$")

CS2_VERSION = 5
STYLE_NAMES = ["Default", "Default Static", "Classic", "Classic Dynamic", "Classic Static", "Legacy"]
PIXEL_STYLE_NAMES = ["Dynamic Cross", "Dynamic Circle", "Classic Dynamic", "Static Circle",
                     "Static Cross", "Static Cross (Shot Feedback)", "Dot Only",
                     "Dynamic Quadrant", "Static Square", "Static Quadrant"]
OUTLINE_MODES = ["Off", "Full", "Half"]
COLOR_NAMES = ["Red", "Green", "Yellow", "Blue", "Cyan", "Custom"]


# ---------- float32 helpers ----------
def f32(x: float) -> float:
    return struct.unpack("<f", struct.pack("<f", x))[0]

HUNDREDTH = f32(0.01)

def pct(v: float, offset: float = 0.0) -> float:
    x = f32(v * HUNDREDTH)
    return f32(x + f32(offset)) if offset else x

def roundf(x: float) -> int:
    return int(x + 0.5) if x >= 0 else -int(-x + 0.5)


def uint8_to_int8(v: int) -> int:
    return v - 256 if v >= 128 else v


# ---------- base-N ↔ bytes ----------
def share_code_to_bytes(code: str):
    if not CODE_RE.match(code):
        return None
    is_cs2 = bool(CS2_CODE_RE.match(code))
    chars = list(code[2:] if is_cs2 else re.sub(r"CSGO|-", "", code))[::-1]
    big = 0
    for ch in chars:
        i = DICTIONARY.find(ch)
        if i < 0:
            return None
        big = big * DICT_LEN + i
    size = 32 if is_cs2 else 18
    h = format(big, "x")
    if len(h) > size * 2:
        return None
    return bytes.fromhex(h.rjust(size * 2, "0"))


def bytes_to_share_code(b: bytes) -> str:
    total = int.from_bytes(b, "big")
    chars = []
    for _ in range(44):
        chars.append(DICTIONARY[total % DICT_LEN])
        total //= DICT_LEN
    return "CS" + "".join(chars)


# ---------- decoders ----------
def decode_crosshair(code: str):
    r = share_code_to_bytes(code)
    if r is None:
        return None
    if (sum(r[1:]) & 0xFF) != r[0]:
        return None
    if len(r) == 32:
        if r[1] == 1 and (r[2] | (r[3] << 8)):
            return decode_cs2_crosshair(r)
        return None
    if r[1] == 1:
        return decode_crosshair_v1(r)
    if r[1] in (3, 4):
        return decode_pixel_crosshair(r)
    return None


def decode_crosshair_v1(r: bytes) -> dict:
    return {
        "version": 1,
        "gap": uint8_to_int8(r[2]) / 10,
        "outline": r[3] / 2,
        "red": r[4], "green": r[5], "blue": r[6], "alpha": r[7],
        "splitDistance": r[8] & 7,
        "followRecoil": ((r[8] >> 4) & 8) == 8,
        "fixedCrosshairGap": uint8_to_int8(r[9]) / 10,
        "color": r[10] & 7,
        "outlineEnabled": (r[10] & 8) == 8,
        "innerSplitAlpha": (r[10] >> 4) / 10,
        "outerSplitAlpha": (r[11] & 0xF) / 10,
        "splitSizeRatio": (r[11] >> 4) / 10,
        "thickness": r[12] / 10,
        "centerDotEnabled": ((r[13] >> 4) & 1) == 1,
        "deployedWeaponGapEnabled": ((r[13] >> 4) & 2) == 2,
        "alphaEnabled": ((r[13] >> 4) & 4) == 4,
        "tStyleEnabled": ((r[13] >> 4) & 8) == 8,
        "style": (r[13] & 0xF) >> 1,
        "length": r[14] / 10,
    }


def decode_pixel_crosshair(r: bytes) -> dict:
    bits = r[10] | (r[11] << 8) | (r[12] << 16) | (r[13] << 24)
    if r[1] == 4:
        outline_mode = (r[13] >> 4) & 3
    else:
        outline_mode = 1 if (r[2] & 0x20) else 0
    return {
        "version": r[1],
        "style": r[2] & 0xF,
        "followRecoil": (r[2] & 0x10) == 0x10,
        "centerDotEnabled": (r[2] & 0x40) == 0x40,
        "tStyleEnabled": (r[2] & 0x80) == 0x80,
        "red": r[3], "green": r[4], "blue": r[5], "alpha": r[6],
        "gap": r[7],
        "length": r[8],
        "dynamicSpreadLimit": r[9],
        "splitDistance": bits & 0x7F,
        "innerSplitAlpha": pct(roundf(((bits >> 7) & 0x1F) * 0.05 / 0.01)),
        "outerSplitAlpha": pct(roundf(((bits >> 12) & 0xF) * 0.05 / 0.01), 0.3),
        "splitSizeRatio": pct((bits >> 16) & 0x7F),
        "thickness": (bits >> 23) & 0x1F,
        "screenHeight": r[14] | (r[15] << 8),
        "outlineMode": outline_mode,
        "color": 5,
        "alphaEnabled": True,
        "outlineEnabled": outline_mode != 0,
        "outline": 1 if outline_mode else 0,
    }


def decode_cs2_crosshair(r: bytes) -> dict:
    bits = (r[18] | (r[19] << 8) | (r[20] << 16) | (r[21] << 24)) & 0xFFFFFFFF
    gap = r[14] | (r[15] << 8)
    if gap & 0x8000:
        gap -= 0x10000
    outline_mode = min(r[13] >> 6, 2)
    return {
        "version": CS2_VERSION,
        "screenHeight": max(240, r[2] | (r[3] << 8)),
        "style": min(r[4] & 0x1F, 9),
        "followRecoil": bool(r[4] & 0x20),
        "centerDotEnabled": bool(r[4] & 0x40),
        "tStyleEnabled": bool(r[4] & 0x80),
        "red": r[5], "green": r[6], "blue": r[7], "alpha": r[8],
        "outlineRed": r[9], "outlineGreen": r[10], "outlineBlue": r[11], "outlineAlpha": r[12],
        "thickness": min(r[13] & 0x3F, 32),
        "outlineMode": outline_mode,
        "gap": max(-3840, min(gap, 3840)),
        "length": r[16],
        "dynamicSpreadLimit": r[17],
        "splitDistance": min(bits & 0x7F, 127),
        "innerSplitAlpha": pct(min((bits >> 7) & 0x7F, 100)),
        "outerSplitAlpha": pct(min((bits >> 14) & 0x7F, 70), 0.3),
        "splitSizeRatio": pct(min((bits >> 21) & 0x7F, 100)),
        "scopeDotUseColor": bool(bits & 0x10000000),
        "scopeDotScale": pct(min(r[22], 190), 0.1),
        "color": 5,
        "alphaEnabled": True,
        "outlineEnabled": outline_mode != 0,
        "outline": 1 if outline_mode else 0,
    }


# ---------- encoder (только новый "CS"-формат, как в CS2) ----------
def clamp_int(v, lo, hi) -> int:
    return max(lo, min(int(round(v)), hi))


def pct_byte(v: float, lo: float, hi: float) -> int:
    v = min(max(v, lo), hi)
    return roundf(f32(f32(v - lo) / HUNDREDTH))


def encode_crosshair(cfg: dict) -> str:
    alpha = clamp_int(cfg.get("alpha", 255), 0, 255)
    gap_u = clamp_int(cfg.get("gap", 0), -3840, 3840) & 0xFFFF
    h = clamp_int(cfg.get("screenHeight", 1080), 0, 65535)

    bits = (
        clamp_int(cfg.get("splitDistance", 35), 0, 127)
        | (pct_byte(cfg.get("innerSplitAlpha", 0.0), 0.0, 1.0) << 7)
        | (pct_byte(cfg.get("outerSplitAlpha", 0.3), f32(0.3), 1.0) << 14)
        | (pct_byte(cfg.get("splitSizeRatio", 0.5), 0.0, 1.0) << 21)
        | (0x10000000 if cfg.get("scopeDotUseColor") else 0)
    ) & 0xFFFFFFFF

    oa = cfg.get("outlineAlpha")
    oa = alpha if oa is None else clamp_int(oa, 0, 255)

    style_byte = (
        clamp_int(cfg.get("style", 0), 0, 9)
        | (0x20 if cfg.get("followRecoil") else 0)
        | (0x40 if cfg.get("centerDotEnabled") else 0)
        | (0x80 if cfg.get("tStyleEnabled") else 0)
    )
    thick_byte = clamp_int(cfg.get("thickness", 1), 0, 32) | (clamp_int(cfg.get("outlineMode", 0), 0, 2) << 6)

    bytes_ = [
        0, 1, h & 0xFF, (h >> 8) & 0xFF,
        style_byte,
        clamp_int(cfg.get("red", 0), 0, 255),
        clamp_int(cfg.get("green", 255), 0, 255),
        clamp_int(cfg.get("blue", 0), 0, 255),
        alpha,
        clamp_int(cfg.get("outlineRed", 0) or 0, 0, 255),
        clamp_int(cfg.get("outlineGreen", 0) or 0, 0, 255),
        clamp_int(cfg.get("outlineBlue", 0) or 0, 0, 255),
        oa,
        thick_byte,
        gap_u & 0xFF, (gap_u >> 8) & 0xFF,
        clamp_int(cfg.get("length", 5), 0, 255),
        clamp_int(cfg.get("dynamicSpreadLimit", 100), 0, 255),
        bits & 0xFF, (bits >> 8) & 0xFF, (bits >> 16) & 0xFF, (bits >> 24) & 0xFF,
        pct_byte(cfg.get("scopeDotScale", 1.0), f32(0.1), 2.0),
        0, 0, 0, 0, 0, 0, 0, 0, 0,
    ]
    bytes_[0] = sum(bytes_[1:]) & 0xFF
    return bytes_to_share_code(bytes(bytes_))


# ---------- демо ----------
if __name__ == "__main__":
    cfg = {
        "style": 0, "followRecoil": False, "centerDotEnabled": True,
        "tStyleEnabled": False,
        "red": 0, "green": 255, "blue": 0, "alpha": 255,
        "outlineRed": 0, "outlineGreen": 0, "outlineBlue": 0, "outlineAlpha": 200,
        "thickness": 1, "outlineMode": 1,
        "gap": -5, "length": 5, "dynamicSpreadLimit": 100,
        "splitDistance": 35, "innerSplitAlpha": 0.0,
        "outerSplitAlpha": 0.3, "splitSizeRatio": 0.5,
        "screenHeight": 1080,
        "scopeDotUseColor": False, "scopeDotScale": 1.0,
    }
    code = encode_crosshair(cfg)
    print("encoded:", code)

    decoded = decode_crosshair(code)
    print("decoded:")
    for k, v in decoded.items():
>>>>>>> 7ac03284276f982b4971a66577f32abc96968e2a
        print(f"  {k}: {v}")