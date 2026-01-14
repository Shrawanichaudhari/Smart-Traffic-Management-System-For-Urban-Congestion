import os
from pathlib import Path

import pygame


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def make_ambulance_surface(size=(60, 30)) -> pygame.Surface:
    w, h = size
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    # Body
    surf.fill((255, 255, 255, 255))
    pygame.draw.rect(surf, (0, 0, 0), surf.get_rect(), 2)

    # Windows
    pygame.draw.rect(surf, (180, 220, 255), (w - 22, 8, 14, 10))

    # Red cross
    cx, cy = w // 3, h // 2
    pygame.draw.rect(surf, (220, 0, 0), (cx - 5, cy - 12, 10, 24))
    pygame.draw.rect(surf, (220, 0, 0), (cx - 12, cy - 5, 24, 10))

    # Light bar
    pygame.draw.rect(surf, (0, 120, 255), (w - 20, 2, 16, 5))

    # Wheels
    pygame.draw.circle(surf, (20, 20, 20), (w - 15, h - 3), 4)
    pygame.draw.circle(surf, (20, 20, 20), (w // 2, h - 3), 4)

    return surf


def main() -> None:
    pygame.init()

    base_dir = Path(__file__).resolve().parents[1]
    images_dir = base_dir / "images"

    base = make_ambulance_surface()

    outputs = {
        "right": base,
        "left": pygame.transform.rotate(base, 180),
        "up": pygame.transform.rotate(base, 90),
        "down": pygame.transform.rotate(base, -90),
    }

    for direction, surf in outputs.items():
        out_dir = images_dir / direction
        _ensure_dir(out_dir)
        out_path = out_dir / "ambulance.png"
        pygame.image.save(surf, str(out_path))
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    # Allow running from anywhere
    os.chdir(Path(__file__).resolve().parents[1])
    main()
