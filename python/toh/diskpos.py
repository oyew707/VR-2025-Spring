"""
-------------------------------------------------------
Simple Debug Script: Print All Disk Positions Repeatedly
-------------------------------------------------------
Author: ChatGPT for Alon
-------------------------------------------------------
"""

import time
import numpy as np
from env_utils import (
    setup_browser, enter_xr_mode,
    get_tower_state
)

# ─── Setup Browser ─────────────────────────────────────────────────────────
driver = setup_browser(render=True)
enter_xr_mode(driver)
time.sleep(5.0)  # Let XR load

print("✅ Browser setup complete. Starting full disk position monitoring...")

# ─── Main Loop ────────────────────────────────────────────────────────────
try:
    while True:
        tower_state = get_tower_state(driver)
        discs = list(tower_state['discs'].values())

        print("\n📋 Current Discs Positions:")
        for i, disc in enumerate(discs):
            pos = np.array(disc['position'])
            pos = (pos * 0.32) + np.array([0, 1 ,-0.5])
            print(f"  🥏 Disc {i}: x={pos[0]:.4f}, y={pos[1]:.4f}, z={pos[2]:.4f}")

        time.sleep(1.0)  # Print every second

except KeyboardInterrupt:
    print("\n⛔ Stopped by user.")

finally:
    driver.quit()
    print("✅ Browser closed.")

