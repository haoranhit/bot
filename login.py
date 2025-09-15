import asyncio
import random
import requests
import time
import datetime
from playwright.async_api import async_playwright
import json
# cfg = {
#     "bls": {
#     "username": "你的BLS账号",
#     "password": "你的BLS密码",
#     "url": "https://usa.blsspainglobal.com/Global/account/login"
#   },
#   "prenotami": {
#     "username": "meilimajia@gmail.com",
#     "password": "Hhit1981*",
#     "url": "https://prenotami.esteri.it/"
#   },
#   "telegram": {
#     "token": "8024666853:AAG6QwcWOD0IIt6LZ9qoRVzT0Hj58lZaPkY",
#     "chat_id": "8335011829"
#   },
# "refresh_interval": 60  # 每60秒检查一次
# }
with open("config.json" , "r") as f:
    cfg = json.load(f)["user2"]
# ================= Error Detection and Exit Function =================
async def check_for_server_error_and_exit(page, browser, context="general"):
    """
    Check for server error and exit if found
    """
    try:
        page_content = await page.content()
        error_patterns = [
            "An error occurred while processing the request",
            "{47360f4d-be16-465b-a97f-b1dcd7cd00c7}",  # Your specific error ID
            "error occurred while processing"
        ]
        
        for pattern in error_patterns:
            if pattern in page_content:
                print(f"Server error detected in {context}: {pattern}")
                screenshot_name = f"server_error_{context}_{random.randint(1000, 9999)}.png"
                await page.screenshot(path=screenshot_name)
                
                # Send Telegram notification about the error
                error_message = f"🚨 VISA Bot Critical Error\n\n❌ Server error detected in {context}: '{pattern}'\n📸 Screenshot saved: {screenshot_name}\n🛑 Script will exit now\n🌐 URL: {page.url}"
                await send_telegram_message(error_message)
                
                # Exit the script
                print(f"Exiting script due to server error in {context}...")
                await browser.close()
                exit(1)
                
    except Exception as e:
        print(f"Error checking for server errors: {e}")

# ================= Telegram 消息发送函数 =================
async def send_telegram_message(message):
    """
    Send a message via Telegram bot
    """
    try:
        bot_token = cfg["telegram"]["token"]
        chat_id = cfg["telegram"]["chat_id"]
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print(f"Telegram message sent successfully: {message}")
        else:
            print(f"Failed to send Telegram message: {response.text}")
            
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

# ================= 处理无预约弹窗函数 =================
async def handle_no_appointments_popup(page):
    """
    Handle the popup that appears when no appointments are available
    Returns True if popup was found and handled, False otherwise
    """
    try:
        # Wait a bit for popup to appear
        await asyncio.sleep(random.uniform(1, 2))
        
        # Check if the popup exists
        popup_selectors = [
            '.jconfirm.jconfirm-open',
            '.jconfirm-content:has-text("All appointments for this service are currently booked")',
            '.jconfirm-box',
            'div:has-text("All appointments for this service are currently booked")'
        ]
        
        popup_found = False
        for selector in popup_selectors:
            popup = page.locator(selector)
            if await popup.count() > 0:
                print(f"Found no-appointments popup using selector: {selector}")
                popup_found = True
                break
        
        if popup_found:
            # Look for the OK button and click it - updated selectors based on actual HTML
            ok_button_selectors = [
                '.jconfirm-buttons button.btn.btn-blue',
                '.jconfirm-buttons button[type="button"]',
                'div.jconfirm-buttons button',
                '.jconfirm-box button.btn.btn-blue',
                '.jconfirm button.btn-blue',
                'button.btn.btn-blue:has-text("ok")',
                '.jconfirm-buttons button:has-text("ok")',
                'button:has-text("ok")'
            ]
            
            ok_clicked = False
            for selector in ok_button_selectors:
                try:
                    ok_button = page.locator(selector)
                    button_count = await ok_button.count()
                    print(f"Selector '{selector}' found {button_count} buttons")
                    
                    if button_count > 0:
                        print(f"Found OK button using: {selector}")
                        
                        # Human-like interaction
                        await ok_button.hover()
                        await asyncio.sleep(random.uniform(0.3, 0.8))
                        await ok_button.click()
                        
                        print("Successfully clicked OK button on no-appointments popup")
                        ok_clicked = True
                        break
                except Exception as e:
                    print(f"Failed to click OK with {selector}: {e}")
                    continue
            
            if not ok_clicked:
                print("Could not find OK button, trying Escape key...")
                await page.keyboard.press('Escape')
            
            # Wait for popup to disappear
            await asyncio.sleep(random.uniform(1, 2))
            return True
        else:
            print("No popup found")
            return False
            
    except Exception as e:
        print(f"Error handling popup: {e}")
        return False


# ================= 点击VISAS/Schengen按钮函数 =================
async def click_schengen_book_button(page):
    """
    Click the VISAS/Schengen Book button
    Returns True if successful, False otherwise
    """
    try:
        print("Looking for VISAS/Schengen Book button...")
        
        # Check for server errors first
        page_content = await page.content()
        if "An error occurred while processing the request" in page_content:
            print("Server error detected on page!")
            await page.screenshot(path="server_error.png")
            
            # Send Telegram notification about the error
            error_message = f"🚨 VISA Bot Critical Error\n\n❌ Server error detected: 'An error occurred while processing the request'\n📸 Screenshot saved: server_error.png\n🛑 Script will exit now\n🌐 URL: {page.url}"
            await send_telegram_message(error_message)
            
            # Exit the script
            print("Exiting script due to server error...")
            await browser.close()
            exit(1)
        
        # Target the specific VISAS/Schengen Book button in the DataTable
        schengen_book_selectors = [
            # Most specific: target the exact row with VISAS and Schengen, then find the Book button
            '//tr[td[text()="VISAS"] and td[text()="Schengen"]]//a[@href="/Services/Booking/694"]/button',
            # Alternative: direct link to booking 694
            'a[href="/Services/Booking/694"] button.button.primary',
            'a[href="/Services/Booking/694"] button',
            # Table-based selectors
            '#dataTableServices tr:has(td:text("VISAS")):has(td:text("Schengen")) a[href*="694"] button',
            '#dataTableServices a[href="/Services/Booking/694"] button',
            # Fallback selectors
            'td a[href="/Services/Booking/694"] button.button.primary'
        ]
        
        for selector in schengen_book_selectors:
            try:
                if selector.startswith('//'):
                    # XPath selector
                    book_button = page.locator(f"xpath={selector}")
                else:
                    # CSS selector
                    book_button = page.locator(selector)
                
                button_count = await book_button.count()
                
                if button_count > 0:
                    print(f"Found VISAS/Schengen Book button using: {selector}")
                    
                    # Extra human-like behavior to avoid detection
                    # Random mouse movements before clicking
                    await page.mouse.move(random.randint(100, 300), random.randint(100, 300))
                    #await asyncio.sleep(random.uniform(0.5, 1.0))
                    
                    # Human-like interaction with random delay
                    #await asyncio.sleep(random.uniform(3, 7))  # Longer delay before clicking
                    await book_button.hover()
                    #await asyncio.sleep(random.uniform(1.0, 2.5))  # Longer hover time
                    await book_button.click()
                    
                    print("Successfully clicked VISAS/Schengen Book button!")
                    
                    # Wait and check for immediate errors
                    await asyncio.sleep(random.uniform(2, 4))
                    page_content_after = await page.content()
                    if "An error occurred while processing the request" in page_content_after:
                        print("Server error occurred after clicking!")
                        await page.screenshot(path="server_error_after_click.png")
                        
                        # Send Telegram notification about the error
                        error_message = f"🚨 VISA Bot Critical Error\n\n❌ Server error after clicking: 'An error occurred while processing the request'\n📸 Screenshot saved: server_error_after_click.png\n🛑 Script will exit now\n🌐 URL: {page.url}"
                        await send_telegram_message(error_message)
                        
                        # Exit the script
                        print("Exiting script due to server error after clicking...")
                        await browser.close()
                        exit(1)
                    
                    return True
                    
            except Exception as e:
                print(f"Failed to click VISAS/Schengen Book with '{selector}': {e}")
                continue
        
        print("Could not find VISAS/Schengen Book button")
        return False
        
    except Exception as e:
        print(f"Error clicking VISAS/Schengen Book button: {e}")
        return False

# ================= 点击IDENTITY/TRAVEL DOCUMENTS/Passport按钮函数 =================
async def click_passport_book_button(page):
    """
    Click the IDENTITY/TRAVEL DOCUMENTS/Passport Book button and then click Send new code
    Returns True if successful, False otherwise
    """
    try:
        print("Looking for IDENTITY/TRAVEL DOCUMENTS/Passport Book button...")
        
        # Check for server errors first
        page_content = await page.content()
        if "An error occurred while processing the request" in page_content:
            print("Server error detected on page!")
            await page.screenshot(path="server_error.png")
            
            # Send Telegram notification about the error
            error_message = f"🚨 VISA Bot Critical Error\n\n❌ Server error detected: 'An error occurred while processing the request'\n📸 Screenshot saved: server_error.png\n🛑 Script will exit now\n🌐 URL: {page.url}"
            await send_telegram_message(error_message)
            
            # Exit the script
            print("Exiting script due to server error...")
            await browser.close()
            exit(1)
        
        # Target the specific IDENTITY/TRAVEL DOCUMENTS/Id card Book button in the DataTable
        passport_book_selectors = [
            # Most specific: target the exact row with IDENTITY/TRAVEL DOCUMENTS and Passport, then find the Book button
            '//tr[td[text()="IDENTITY/TRAVEL DOCUMENTS"] and td[text()="Passport"]]//a[@href="/Services/Booking/656"]/button',
            # Alternative: direct link to booking 656
            'a[href="/Services/Booking/656"] button.button.primary',
            'a[href="/Services/Booking/656"] button',
            # Table-based selectors
            '#dataTableServices tr:has(td:text("IDENTITY/TRAVEL DOCUMENTS")):has(td:text("Passport")) a[href*="656"] button',
            '#dataTableServices a[href="/Services/Booking/656"] button',
            # Fallback selectors
            'td a[href="/Services/Booking/656"] button.button.primary'
        ]
        
        book_button_clicked = False
        for selector in passport_book_selectors:
            try:
                if selector.startswith('//'):
                    # XPath selector
                    book_button = page.locator(f"xpath={selector}")
                else:
                    # CSS selector
                    book_button = page.locator(selector)
                
                button_count = await book_button.count()
                
                if button_count > 0:
                    print(f"Found IDENTITY/TRAVEL DOCUMENTS/Passport Book button using: {selector}")
                    
                    # Extra human-like behavior to avoid detection
                    # Random mouse movements before clicking
                    await page.mouse.move(random.randint(100, 300), random.randint(100, 300))
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                    
                    # Human-like interaction with random delay
                    await asyncio.sleep(random.uniform(3, 7))  # Longer delay before clicking
                    await book_button.hover()
                    await asyncio.sleep(random.uniform(1.0, 2.5))  # Longer hover time
                    await book_button.click()
                    
                    print("Successfully clicked IDENTITY/TRAVEL DOCUMENTS/Passport Book button!")
                    book_button_clicked = True
                    
                    break
                    
            except Exception as e:
                print(f"Failed to click IDENTITY/TRAVEL DOCUMENTS/Passport Book with '{selector}': {e}")
                continue
        
        if not book_button_clicked:
            print("Could not find IDENTITY/TRAVEL DOCUMENTS/Passport Book button")
            return False
        
        # Wait for the booking page to load
        await asyncio.sleep(random.uniform(3, 6))
        
        # Check if we're on the booking page
        current_url = page.url
        print(f"Current URL after clicking: {current_url}")
        
        if "/Services/Booking/656" not in current_url:
            print("Did not navigate to expected booking page")
            return False
        
        # Check for server errors on the booking page
        page_content_after = await page.content()
        if "An error occurred while processing the request" in page_content_after:
            print("Server error occurred after clicking!")
            await page.screenshot(path="server_error_after_click.png")
            
            # Send Telegram notification about the error
            error_message = f"🚨 VISA Bot Critical Error\n\n❌ Server error after clicking: 'An error occurred while processing the request'\n📸 Screenshot saved: server_error_after_click.png\n🛑 Script will exit now\n🌐 URL: {page.url}"
            await send_telegram_message(error_message)
            
            # Exit the script
            print("Exiting script due to server error after clicking...")
            await browser.close()
            exit(1)
        


        print("Looking for 'Send new code' button...")
        
        otp_send_selectors = [
            '#otp-send',
            'button#otp-send',
            'button[onclick="sendOTP();"]',
            'button.button.primary#otp-send',
            'button:has-text("Send new code")',
            'button.primary:has-text("Send new code")'
        ]
        
        otp_button_clicked = False
        for selector in otp_send_selectors:
            try:
                otp_button = page.locator(selector)
                button_count = await otp_button.count()
                
                if button_count > 0:
                    print(f"Found 'Send new code' button using: {selector}")
                    
                    # Human-like interaction
                    # await asyncio.sleep(random.uniform(1, 4))
                    await otp_button.hover()
                    # await asyncio.sleep(random.uniform(1.0, 2.0))
                    await otp_button.click()
                    
                    print("Successfully clicked 'Send new code' button!")
                    otp_button_clicked = True
                    break
                    
            except Exception as e:
                print(f"Failed to click 'Send new code' button with '{selector}': {e}")
                continue
        
        if not otp_button_clicked:
            print("Could not find 'Send new code' button")
            return False
        
        # Wait after clicking the OTP button
        # await asyncio.sleep(random.uniform(2, 4))
        
        # Return to the previous webpage (Services page)
        print("Returning to Services page...")
        
        # Navigate back to Services page
        try:
            await page.goto("https://prenotami.esteri.it/Services")
            print("Successfully navigated back to Services page")
            
            # Wait for the Services page to load
            await asyncio.sleep(random.uniform(2, 4))
            
            # Wait for DataTable to load again
            try:
                await page.wait_for_selector("#dataTableServices", timeout=10000)
                print("DataTable loaded successfully after return")
            except:
                print("DataTable not found after return, taking screenshot...")
                await page.screenshot(path="datatable_missing_after_return.png")
            
            # Check for server errors on the returned Services page
            page_content_return = await page.content()
            if "An error occurred while processing the request" in page_content_return:
                print("Server error occurred after returning to Services page!")
                await page.screenshot(path="server_error_after_return.png")
                
                # Send Telegram notification about the error
                error_message = f"🚨 VISA Bot Critical Error\n\n❌ Server error after returning to Services page: 'An error occurred while processing the request'\n📸 Screenshot saved: server_error_after_return.png\n🛑 Script will exit now\n🌐 URL: {page.url}"
                await send_telegram_message(error_message)
                
                # Exit the script
                print("Exiting script due to server error after return...")
                await browser.close()
                exit(1)
            
            print(f"Current URL after return: {page.url}")
            
        except Exception as e:
            print(f"Error returning to Services page: {e}")
            # Try alternative navigation methods
            try:
                print("Trying browser back navigation...")
                await page.go_back()
                await asyncio.sleep(random.uniform(2, 4))
                print(f"Current URL after go_back: {page.url}")
            except Exception as back_error:
                print(f"Browser back navigation failed: {back_error}")
                return False
        
        return True
        
    except Exception as e:
        print(f"Error in click_passport_book_button: {e}")
        return False
# ================= fill in booking page information.  =================
async def fill_booking_page(page):
    """
    Fill in the booking page required information including passport number.
    """
    try:
        # Check for server errors first
        page_content_after = await page.content()
        if "An error occurred while processing the request" in page_content_after:
            print("Server error occurred after clicking!")
            # Send Telegram notification about the error
            error_message = f"🚨 VISA Bot Critical Error\n\n❌ Server error after clicking: 'An error occurred while processing the request'\nScript will exit now\n🌐 URL: {page.url}"
            await send_telegram_message(error_message)
            
            # Exit the script
            print("Exiting script due to server error after clicking...")
            await browser.close()
            exit(1)

        print("Starting to fill booking page information...")
        
        # Wait for the page to fully load
        
        # Look for passport number field
        print("Looking for passport number field...")
        
        passport_field_selectors = [
            '#DatiAddizionaliPrenotante_2___testo',
            'input[name="DatiAddizionaliPrenotante[2]._testo"]',
            'input[id*="DatiAddizionaliPrenotante_2___testo"]',
            '#datoaddizionale_2 input[type="text"]',
            'input[maxlength="100"][name*="DatiAddizionaliPrenotante"]'
        ]
        
        passport_field_found = False
        for selector in passport_field_selectors:
            try:
                passport_field = page.locator(selector)
                if await passport_field.count() > 0:
                    print(f"Found passport field using selector: {selector}")
                    
                    # Click and fill the passport field
                    await passport_field.click()
                    # await asyncio.sleep(random.uniform(0.3, 0.8))
                    
                    # Clear the field first
                    # await passport_field.fill("")
                    # await asyncio.sleep(0.2)
                    
                    # Type passport number character by character
                    passport_number = cfg["prenotami"]["passport"]
                    
                    await page.keyboard.type(passport_number)
                    
                    print("Successfully filled passport number field")
                    passport_field_found = True
                    break
                    
                    
            except Exception as e:
                print(f"Failed to fill passport field with selector '{selector}': {e}")
                continue
        
        if not passport_field_found:
            print("❌ Could not find passport number field!")
            await page.screenshot(path="passport_field_not_found.png")
            return False
        
        # Look for address field - Full residence address
        print("Looking for Full residence address field...")
        
        address_field_selectors = [
            '#DatiAddizionaliPrenotante_6___testo',
            'input[name="DatiAddizionaliPrenotante[6]._testo"]',
            'input[id*="DatiAddizionaliPrenotante_6___testo"]',
            '#datoaddizionale_6 input[type="text"]',
            'input[maxlength="100"][name*="DatiAddizionaliPrenotante"][name*="6"]'
        ]
        
        address_field_found = False
        for selector in address_field_selectors:
            try:
                address_field = page.locator(selector)
                if await address_field.count() > 0:
                    print(f"Found address field using selector: {selector}")
                    
                    # Click and fill the address field
                    await address_field.click()
                    
                    # Type address quickly (no delays between characters)
                    address = cfg["prenotami"]["address"]
                    
                    await page.keyboard.type(address)
                    
                    print("Successfully filled address field")
                    address_field_found = True
                    break
                    
                    
            except Exception as e:
                print(f"Failed to fill address field with selector '{selector}': {e}")
                continue
        
        if not address_field_found:
            print("❌ Address field not found!")
            await page.screenshot(path="address_field_not_found.png")
        
        # Wait a bit after filling fields
        await asyncio.sleep(random.uniform(1, 3))
        
        print("✅ Booking page information filled successfully")
        
        # Take a screenshot for verification
        await page.screenshot(path="booking_page_filled.png")
        print("Screenshot saved: booking_page_filled.png")
        
        print("Press Ctrl+C to stop or let the script continue...")
        
        breakpoint()
        # await asyncio.sleep(10)  # 10 second pause instead of breakpoint
        
        return True
        
    except Exception as e:
        print(f"❌ Error in fill_booking_page: {e}")
        await page.screenshot(path="fill_booking_error.png")
        
        # Send error notification
        error_message = f"🚨 VISA Bot Error\n\n❌ Failed to fill booking page\n🔍 Error: {str(e)}\n📸 Screenshot: fill_booking_error.png\n🌐 URL: {page.url}"
        await send_telegram_message(error_message)
        
        return False



# ================= 检查空档函数 =================
async def check_appointments(page):
    await page.reload()
    # TODO: 修改下面的选择器为实际空档判断逻辑
    content = await page.content()
    if "No appointments available" not in content:  # 示例逻辑
        await send_telegram("Prenot@mi 意大利有空档！快去预约！\n链接: https://prenotami.esteri.it")
        print("空档发现，消息已发送！")



async def main():
    async with async_playwright() as p:
        # Launch Firefox browser
        print("Launching Firefox browser...")
        browser = await p.firefox.launch(
            headless=False,
            slow_mo=1000  # Add 1 second delay between actions for more human-like behavior
        )
        print("Successfully launched Firefox browser")
        
        # Create new page with additional stealth settings
        page = await browser.new_page()
        
        # Set viewport to common resolution
        await page.set_viewport_size({"width": 1366, "height": 768})
        
        # Add extra headers to look more human (Firefox-specific)
        await page.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0'
        })
        
        # Override navigator properties (works for all browsers)
        await page.add_init_script("""
            // Override webdriver detection
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Override automation flags
            window.chrome = window.chrome || {};
            window.chrome.runtime = window.chrome.runtime || {};
            
            // Remove Playwright signatures
            delete window.__playwright;
            delete window.__pw_manual;
            delete window.__PW_inspect;
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        await page.goto("https://prenotami.esteri.it")
        print(f"Navigated to: {page.url}")
        
        # Check for server errors immediately after navigation
        await check_for_server_error_and_exit(page, browser, "initial_navigation")
        
        # Add random delay to simulate human reading time
        await asyncio.sleep(random.uniform(2, 4))

        # Debug: Check if EN button exists
        try:
            en_button = page.locator("a[href*='/Language/']:has-text('En')")
            if await en_button.count() > 0:
                print("Found EN button, clicking...")
                await en_button.hover()
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await en_button.click()
            else:
                print("EN button not found, trying alternative selectors...")
                # Try alternative selectors for language switch
                alt_selectors = ["a:has-text('EN')", "button:has-text('EN')", "[lang='en']", ".lang-en"]
                for selector in alt_selectors:
                    try:
                        await page.click(selector, timeout=2000)
                        print(f"Clicked EN using selector: {selector}")
                        break
                    except:
                        continue
        except Exception as e:
            print(f"Error with EN button: {e}")
        
        # Wait for page to load
        await asyncio.sleep(random.uniform(2, 4))
        print(f"Current URL after EN click: {page.url}")

        # Debug: Check if login form exists
        try:
            email_field = page.locator("#login-email")
            password_field = page.locator("#login-password")
            
            if await email_field.count() == 0:
                print("Email field #login-email not found, trying alternatives...")
                # Try alternative email field selectors
                email_selectors = ["input[type='email']", "input[name*='email']", "input[placeholder*='email']", "#email", ".email"]
                for selector in email_selectors:
                    if await page.locator(selector).count() > 0:
                        email_field = page.locator(selector)
                        print(f"Found email field using: {selector}")
                        break
                        
            if await password_field.count() == 0:
                print("Password field #login-password not found, trying alternatives...")
                # Try alternative password field selectors
                password_selectors = ["input[type='password']", "input[name*='password']", "#password", ".password"]
                for selector in password_selectors:
                    if await page.locator(selector).count() > 0:
                        password_field = page.locator(selector)
                        print(f"Found password field using: {selector}")
                        break

            # Fill email field
            print("Filling email field...")
            await email_field.click()
            await asyncio.sleep(random.uniform(0.03, 0.08))
            
            # Clear field first
            await email_field.fill("")
            await asyncio.sleep(0.2)
            
            # Type email character by character with random delays
            for char in cfg["prenotami"]["username"]:
                await page.keyboard.type(char)
                await asyncio.sleep(random.uniform(0.00004, 0.00008))
            
            # Move to password field
            print("Filling password field...")
            # await asyncio.sleep(random.uniform(0.5, 1.2))
            await password_field.click()
            await asyncio.sleep(random.uniform(0.00004, 0.00008))
            
            # Clear field first
            await password_field.fill("")
            await asyncio.sleep(0.02)
            
            # Type password character by character
            for char in cfg["prenotami"]["password"]:
                await page.keyboard.type(char)
                await asyncio.sleep(random.uniform(0.05, 0.15))

            print("Form filled, looking for submit button...")
            
            # Human-like mouse movement and pause before clicking submit
            await asyncio.sleep(random.uniform(1, 3))
            
            # Move mouse in a more natural way (small movements)
            current_x, current_y = 500, 400  # Starting position
            for _ in range(random.randint(2, 5)):
                current_x += random.randint(-50, 50)
                current_y += random.randint(-30, 30)
                await page.mouse.move(current_x, current_y)
                await asyncio.sleep(random.uniform(0.1, 0.3))
            
            # Try multiple submit button selectors
            submit_selectors = [
                "text=/forward/i",
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Login')",
                "button:has-text('Sign in')",
                "button:has-text('Accedi')",
                ".login-button",
                "#login-button"
            ]
            
            submit_clicked = False
            for selector in submit_selectors:
                try:
                    submit_button = page.locator(selector)
                    if await submit_button.count() > 0:
                        print(f"Found submit button using: {selector}")
                        await submit_button.hover()
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                        await submit_button.click()
                        submit_clicked = True
                        break
                except Exception as e:
                    print(f"Failed to click submit with {selector}: {e}")
                    continue
                    
            if not submit_clicked:
                print("Could not find submit button, trying Enter key...")
                await page.keyboard.press('Enter')
                
        except Exception as e:
            print(f"Error during login process: {e}")
            # Take a screenshot for debugging
            await page.screenshot(path="login_error.png")
            print("Screenshot saved as login_error.png")


 # ================= 循环检查空档 =================
        # while True:
        #     try:
        #         await check_appointments(page)
        #     except Exception as e:
        #         print("检查出错:", e)
        #     await asyncio.sleep(cfg["refresh_interval"])


        await page.wait_for_selector("nav.app-menu")

        print("登录完成，当前 URL:", page.url)
        
        # Check for server errors after login
        await check_for_server_error_and_exit(page, browser, "after_login")

        # await browser.close()
        # await page.reload()
        # 点击 EN
        await page.click("text=/ENG/i")
        print("Clicked ENG button")
        
        # Wait for navigation and check current URL
        await asyncio.sleep(random.uniform(1, 4))
        print(f"Current URL after ENG click: {page.url}")
        
        # Navigate to Services page if not already there
        if "/Services" not in page.url:
            try:
                # Try to click Book in navigation menu first
                await page.wait_for_selector("nav.app-menu", timeout=10000)
                
                book_nav_selectors = [
                    'nav.app-menu a:has-text("Book")',
                    'nav.app-menu button:has-text("Book")',
                    '.app-menu a:has-text("Book")',
                    'text=/BOOK/i'
                ]
                
                book_nav_clicked = False
                for selector in book_nav_selectors:
                    try:
                        await page.click(selector, timeout=3000)
                        print(f"Clicked Book navigation using: {selector}")
                        book_nav_clicked = True
                        break
                    except:
                        continue
                        
                if not book_nav_clicked:
                    print("Could not find Book in navigation, trying direct URL...")
                    await page.goto("https://prenotami.esteri.it/Services")
                    
            except Exception as e:
                print(f"Error navigating to Services: {e}")
        
        # Wait for Services page to load
        await asyncio.sleep(random.uniform(2, 4))
        print(f"Current URL: {page.url}")
        
        # Check for server errors on Services page
        await check_for_server_error_and_exit(page, browser, "services_page")
        
        # Wait for DataTable to load
        try:
            await page.wait_for_selector("#dataTableServices", timeout=10000)
            print("DataTable loaded successfully")
        except:
            print("DataTable not found, taking screenshot...")
            await page.screenshot(path="datatable_missing.png")
        
        # get_otp_code()
        await click_passport_book_button(page)
        # ================= 尝试预约循环 =================
        # Try to book VISAS/Schengen appointments with retry logic
        wait_time_flag = True
        target_hour, target_minute, target_sec = 14, 59, 59
        #target_hour, target_minute, target_sec = 23, 29, 30
        now = datetime.datetime.now()
        target_time = datetime.datetime(now.year, now.month, now.day, target_hour, target_minute, target_sec)
        # If target time for today has passed, set it for tomorrow (to run every day)
        if now > target_time:
            target_time += datetime.timedelta(days=1)
        sleep_seconds = (target_time - now).total_seconds()
        print(f"Waiting for {sleep_seconds:.2f} seconds until {target_time.strftime('%H:%M:%S')}...")
        time.sleep(sleep_seconds)
        print(f"It's {target_time.strftime('%H:%M:%S')}! Clicking the VISA appointment ...")
        time.sleep(0.99)

        max_attempts = 2
        for attempt in range(max_attempts):
            print(f"\n=== Booking Attempt {attempt + 1}/{max_attempts} ===")
            
            # Check for server errors before attempting
            try:
                page_content = await page.content()
                if "An error occurred while processing the request" in page_content:
                    print("Server error detected before booking attempt!")
                    await page.screenshot(path=f"server_error_attempt_{attempt + 1}.png")
                    
                    # Send Telegram notification about the error
                    error_message = f"🚨 VISA Bot Critical Error\n\n❌ Server error before booking attempt {attempt + 1}: 'An error occurred while processing the request'\n📸 Screenshot saved: server_error_attempt_{attempt + 1}.png\n🛑 Script will exit now\n🌐 URL: {page.url}"
                    await send_telegram_message(error_message)
                    
                    # Exit the script
                    print("Exiting script due to server error before booking attempt...")
                    await browser.close()
                    exit(1)
            except Exception as e:
                print(f"Error checking page content: {e}")
            
            # Click the VISAS/Schengen Book button
            await click_schengen_book_button(page)
            
            # if book_success:
            # await asyncio.sleep(random.uniform(3, 6))  # Longer wait to avoid server stress
            
            # Check if we're on the new booking page
            current_url = page.url
            print(f"Current URL after clicking: {current_url}")
            #handle not appointment availabe page 
            if "/Services/Booking/694" not in current_url:
                # Check for and handle no-appointments popup
                await handle_no_appointments_popup(page)

                    # Send Telegram notification
                telegram_message = f"🔄 VISA Bot Update - Attempt {attempt + 1}/{max_attempts}\n\n❌ No appointments available for VISAS/Schengen\n⏰ Will retry in 5-15 seconds\n🌐 URL: {page.url}"
                await send_telegram_message(telegram_message)
                print(telegram_message)
                await browser.close()
                exit(1)
            else:
                # In the booking page. fill in necessary information. 
                fill_booking_page(page)

        # await page.reload()
        # # 找到同时包含 VISAS 和 Schengen 的行，然后点击该行的 Book 按钮
        # await page.click("//tr[td[text()='VISAS'] and td[text()='Schengen']]//button[text()='Book']")

        # Keep the page open for 10 minutes
        # await asyncio.sleep(1000)  # 600 seconds = 10 minutes
        
        # await browser.close()


asyncio.run(main())


