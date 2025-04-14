"""
-------------------------------------------------------
[Program Description]
-------------------------------------------------------
Author:  einsteinoyewole
Email:   eo223@nyu.edu
__updated__ = "4/12/25"
-------------------------------------------------------
"""

# Imports
from PIL import Image
import io
import time
import os
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Constants
EMULATOR_PATH = os.path.join(os.getcwd(), "Immersive-Web-Emulator-Chrome-Web-Store.crx")
URL = urlparse("http://localhost:2024/").geturl()
JS_GET_DEVICE = """
const allKeys = Object.getOwnPropertySymbols(navigator.xr);

// Find the correct symbol key that matches the pattern
const xrSymbol = allKeys.find(sym => 
    sym.toString().includes('webxr-polyfill/XR'));
const xrDevice = navigator.xr[xrSymbol].device;
"""
BUTTON_INDICES = {
    'TRIGGER': 0,
    'GRIP': 1,
    'STICK_PRESS': 3,
    'X_A': 4,  # X on left, A on right
    'Y_B': 5   # Y on left, B on right
}


def setup_browser(render: bool = True) -> webdriver.Chrome:
    """
    -------------------------------------------------------
    Set up the Chrome browser with necessary options and extensions
    for XR emulation.
    -------------------------------------------------------
    Parameters:
        render - Boolean indicating whether to run in headless mode
    Returns:
         driver - Configured Chrome WebDriver instance (webdriver.Chrome)
    -------------------------------------------------------
    """
    chrome_options = Options()
    chrome_options.add_extension(EMULATOR_PATH)

    # Enable Logging
    chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL', 'driver': 'ALL'})
    chrome_options.add_argument("--enable-logging")

    # Essential developer mode preferences
    chrome_options.add_experimental_option("prefs", {
        "extensions.ui.developer_mode": True,
        "devtools.preferences.currentDockState": '"undocked"',
        "devtools.preferences.devToolsPosition": '"bottom"'
    })

    # Required flags for WebXR
    chrome_options.add_argument("--enable-webxr")
    chrome_options.add_argument("--enable-features=WebXR")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-insecure-localhost")
    chrome_options.add_argument("--auto-open-devtools-for-tabs")

    # Security exceptions for local testing
    chrome_options.add_argument("--unsafely-treat-insecure-origin-as-secure=http://localhost:2024")

    # Headless mode not recommended for XR emulation
    if not render:
        chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def enter_xr_mode(driver: webdriver.Chrome):
    """
    -------------------------------------------------------
    Launch the application and enter XR mode. Reloads the page
    if already on the correct URL.
    -------------------------------------------------------
    Parameters:
         driver - Selenium WebDriver instance (webdriver.Chrome)
    -------------------------------------------------------
    """
    # Open the application URL/ Reload the page
    if urlparse(driver.current_url).geturl() != URL:
        driver.get(URL)
    else:
        driver.refresh()

    # Click Tower of Hanoi mode button
    toh_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(@onclick, 'towerOfHanoi')]"))
    )
    driver.execute_script("arguments[0].click();", toh_button)

    # Wait for the XR button to be clickable
    time.sleep(2)

    # Click Enter XR button (with explicit wait for state change)
    xr_button = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.webvr-ui-button[title='Enter XR']"))
    )
    driver.execute_script("""
            const btn = arguments[0];
            btn.classList.add('webxr-session-initiated');
            btn.click();
        """, xr_button)


def get_screenshot(driver: webdriver.Chrome) -> Image:
    """
    -------------------------------------------------------
    Take a screenshot of the current XR view.
    -------------------------------------------------------
    Parameters:
        driver - Selenium WebDriver instance (webdriver.Chrome)
    Returns:
       image - Screenshot image (PIL.Image)
    -------------------------------------------------------
    """
    assert driver is not None, "Driver is not initialized"

    assert urlparse(driver.current_url).geturl() == URL, f"Driver is not on the correct URL {driver.current_url}"
    # Take screenshot
    screenshot = driver.get_screenshot_as_png()
    image = Image.open(io.BytesIO(screenshot))
    return image


def get_headset_state(driver: webdriver.Chrome) -> dict:
    """
    -------------------------------------------------------
    Get the position and angles of the headset.
    -------------------------------------------------------
    Parameters:
        driver - Selenium WebDriver instance (webdriver.Chrome)
    Returns:
        headset_state - Dictionary containing headset state information
    -------------------------------------------------------
    """
    assert driver is not None, "Driver is not initialized"
    assert urlparse(driver.current_url).geturl() == URL, f"Driver is not on the correct URL {driver.current_url}"

    # Get headset state
    headset_state = driver.execute_script(f"""
    {JS_GET_DEVICE}
    return {{
        'position': xrDevice.position,
        'angles': xrDevice.quaternion,
    }}
    """)
    return headset_state


def get_controller_state(driver: webdriver.Chrome, hand: str) -> dict:
    """
    -------------------------------------------------------
    Get the position and angles of the controller.
    -------------------------------------------------------
    Parameters:
        driver - Selenium WebDriver instance (webdriver.Chrome)
        hand - 'left' or 'right' to specify which controller to get the state of
    Returns:
        controller_state - Dictionary containing controller state information
    -------------------------------------------------------
    """
    assert hand in ['left', 'right'], "Invalid hand specified. Use 'left' or 'right'."
    assert driver is not None, "Driver is not initialized"
    assert urlparse(driver.current_url).geturl() == URL, f"Driver is not on the correct URL {driver.current_url}"

    # Get controller state
    controllerIndex = 1 if hand == 'left' else 0
    controller_state = driver.execute_script(f"""
        {JS_GET_DEVICE}
        const gamepad = xrDevice.gamepads[{controllerIndex}];
        
        return {{
            'position': gamepad.pose.position,
            'angles': gamepad.pose.orientation,
        }}""")
    return controller_state


def headset_input(driver: webdriver.Chrome, delta_position: list[float], delta_angles: list[float]):
    """
    -------------------------------------------------------
    Controls the headset position and angles. Affects the
    observation of the environment.
    -------------------------------------------------------
    Parameters:
       driver - Selenium WebDriver instance (webdriver.Chrome)
       delta_position - List of 3 floats representing the change in position
       delta_angles - List of 4 floats representing the change in angles
    -------------------------------------------------------
    """
    assert driver is not None, "Driver is not initialized"
    assert urlparse(driver.current_url).geturl() == URL, f"Driver is not on the correct URL {driver.current_url}"

    # Get headset state
    headset_state = get_headset_state(driver)
    current_position = headset_state['position']
    current_angles = headset_state['angles']
    # Set headset position and angles
    driver.execute_script(f"""
        {JS_GET_DEVICE}
        xrDevice.position[0] = {delta_position[0]+current_position[0]};
        xrDevice.position[1] = {delta_position[1]+current_position[1]};
        xrDevice.position[2] = {delta_position[2]+current_position[2]};
        xrDevice.quaternion[0] = {delta_angles[0]+current_angles[0]};
        xrDevice.quaternion[1] = {delta_angles[0]+current_angles[1]};
        xrDevice.quaternion[2] = {delta_angles[0]+current_angles[2]};
        xrDevice.quaternion[3] = {delta_angles[0]+current_angles[3]};
    """)


def controller_input(driver: webdriver.Chrome, hand: str, delta_position: list[float],
                     delta_angles: list[float], buttonIndex: int = 1, buttonState: str = 'released'):
    """
    -------------------------------------------------------
    Controller input function to simulate controller actions.
    Simulates movement and button presses.
    -------------------------------------------------------
    Parameters:
       driver - Selenium WebDriver instance (webdriver.Chrome)
       hand - 'left' or 'right' to specify which controller to simulate
       delta_position - List of 3 floats representing the change in position
       delta_angles - List of 4 floats representing the change in angles
       buttonIndex - Index of the button to simulate (default: 1 for grip)
       buttonState - 'pressed' or 'released' to specify the button state (default: 'released')
    -------------------------------------------------------
    """
    assert buttonIndex in BUTTON_INDICES.values(), "Button not supported"
    assert buttonState in ['pressed', 'released'], "Button state must be 'pressed' or 'released'"
    assert hand in ['left', 'right'], "Hand must be 'left' or 'right'"
    assert driver is not None, "Driver is not initialized"
    assert urlparse(driver.current_url).geturl() == URL, f"Driver is not on the correct URL {driver.current_url}"
    assert buttonIndex == 1, "Only the grip button is supported"

    # Get controller state
    controller_state = get_controller_state(driver, hand)
    current_position = controller_state['position']
    current_angles = controller_state['angles']
    controllerIndex = 1 if hand == 'left' else 0

    touched = 'true' if buttonState == 'pressed' else 'false'
    pressed = 'true' if buttonState == 'pressed' else 'false'
    value = '1' if buttonState == 'pressed' else '0'

    # Set controller input
    driver.execute_script(f"""
        {JS_GET_DEVICE}
        const gamepad = xrDevice.gamepads[{controllerIndex}];
        
        // Set Position
        gamepad.pose.position[0] = {delta_position[0] + current_position[0]};
        gamepad.pose.position[1] = {delta_position[1] + current_position[1]};
        gamepad.pose.position[2] = {delta_position[2] + current_position[2]};
        gamepad.pose.orientation[0] = {delta_angles[0] + current_angles[0]};
        gamepad.pose.orientation[1] = {delta_angles[0] + current_angles[1]};
        gamepad.pose.orientation[2] = {delta_angles[0] + current_angles[2]};
        gamepad.pose.orientation[3] = {delta_angles[0] + current_angles[3]};
        
        // Set Button State
        gamepad.buttons[{buttonIndex}].pressed = {pressed};
        gamepad.buttons[{buttonIndex}].touched = {touched};
        gamepad.buttons[{buttonIndex}].value = {value};
    """)




