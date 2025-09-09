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
    cfg = json.load(f)["user1"]
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

# ================= 点击IDENTITY/TRAVEL DOCUMENTS/Id card按钮函数 =================
async def click_passport_book_button(page):
    """
    Click the IDENTITY/TRAVEL DOCUMENTS/Id card Book button and then click Send new code
    Returns True if successful, False otherwise
    """
    try:
        print("Looking for IDENTITY/TRAVEL DOCUMENTS/Id card Book button...")
        
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
            # Most specific: target the exact row with IDENTITY/TRAVEL DOCUMENTS and Id card, then find the Book button
            '//tr[td[text()="IDENTITY/TRAVEL DOCUMENTS"] and td[text()="Id card"]]//a[@href="/Services/Booking/4874"]/button',
            # Alternative: direct link to booking 4874
            'a[href="/Services/Booking/4874"] button.button.primary',
            'a[href="/Services/Booking/4874"] button',
            # Table-based selectors
            '#dataTableServices tr:has(td:text("IDENTITY/TRAVEL DOCUMENTS")):has(td:text("Id card")) a[href*="4874"] button',
            '#dataTableServices a[href="/Services/Booking/4874"] button',
            # Fallback selectors
            'td a[href="/Services/Booking/4874"] button.button.primary'
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
                    print(f"Found IDENTITY/TRAVEL DOCUMENTS/Id card Book button using: {selector}")
                    
                    # Extra human-like behavior to avoid detection
                    # Random mouse movements before clicking
                    await page.mouse.move(random.randint(100, 300), random.randint(100, 300))
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                    
                    # Human-like interaction with random delay
                    await asyncio.sleep(random.uniform(3, 7))  # Longer delay before clicking
                    await book_button.hover()
                    await asyncio.sleep(random.uniform(1.0, 2.5))  # Longer hover time
                    await book_button.click()
                    
                    print("Successfully clicked IDENTITY/TRAVEL DOCUMENTS/Id card Book button!")
                    book_button_clicked = True
                    break
                    
            except Exception as e:
                print(f"Failed to click IDENTITY/TRAVEL DOCUMENTS/Id card Book with '{selector}': {e}")
                continue
        
        if not book_button_clicked:
            print("Could not find IDENTITY/TRAVEL DOCUMENTS/Id card Book button")
            return False
        
        # Wait for the booking page to load
        await asyncio.sleep(random.uniform(3, 6))
        
        # Check if we're on the booking page
        current_url = page.url
        print(f"Current URL after clicking: {current_url}")
        
        if "/Services/Booking/4874" not in current_url:
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
        
        # Now look for and click the "Send new code" button
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
                    await asyncio.sleep(random.uniform(2, 4))
                    await otp_button.hover()
                    await asyncio.sleep(random.uniform(1.0, 2.0))
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
        await asyncio.sleep(random.uniform(2, 4))
        
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

# ================= 获取OTP验证码函数 =================
async def get_otp_code():
    """
    Get OTP code from Gmail account specified in config
    Returns the OTP code as string if found, None otherwise
    """
    try:
        import imaplib
        import email
        from email.header import decode_header
        import re
        import time
        
        print("Connecting to Gmail to retrieve OTP code...")
        
        # Get email credentials from config
        email_address = cfg["prenotami"]["username"]
        email_password = cfg["prenotami"]["password"]
        
        print(f"Connecting to Gmail account: {email_address}")
        
        # Connect to Gmail IMAP server
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_address, email_password)
        
        # Select inbox
        mail.select("inbox")
        
        # Search for recent emails from prenotami (last 10 minutes)
        # Look for emails from the Italian consulate system
        search_criteria = [
            'FROM "prenotami.esteri.it"',
            'FROM "esteri.it"',
            'FROM "noreply@prenotami.esteri.it"',
            'SUBJECT "OTP"',
            'SUBJECT "verification"',
            'SUBJECT "code"'
        ]
        
        otp_code = None
        
        for criteria in search_criteria:
            try:
                print(f"Searching emails with criteria: {criteria}")
                
                # Search for emails from the last hour
                status, messages = mail.search(None, criteria, 'SINCE', time.strftime("%d-%b-%Y", time.gmtime(time.time() - 3600)))
                
                if status == "OK" and messages[0]:
                    email_ids = messages[0].split()
                    
                    # Check the most recent emails first
                    for email_id in reversed(email_ids[-5:]):  # Check last 5 emails
                        try:
                            # Fetch the email
                            status, msg_data = mail.fetch(email_id, "(RFC822)")
                            
                            if status == "OK":
                                # Parse the email
                                email_body = msg_data[0][1]
                                email_message = email.message_from_bytes(email_body)
                                
                                # Get email subject
                                subject = decode_header(email_message["Subject"])[0][0]
                                if isinstance(subject, bytes):
                                    subject = subject.decode()
                                
                                print(f"Checking email with subject: {subject}")
                                
                                # Get email body
                                body = ""
                                if email_message.is_multipart():
                                    for part in email_message.walk():
                                        if part.get_content_type() == "text/plain":
                                            body = part.get_payload(decode=True).decode()
                                            break
                                        elif part.get_content_type() == "text/html":
                                            body = part.get_payload(decode=True).decode()
                                else:
                                    body = email_message.get_payload(decode=True).decode()
                                
                                # Look for OTP patterns in the email body
                                otp_patterns = [
                                    r'(?:OTP|code|verification code|codice)[\s:]*(\d{4,8})',
                                    r'(\d{6})',  # 6-digit code
                                    r'(\d{4})',  # 4-digit code
                                    r'(\d{8})',  # 8-digit code
                                    r'Your code is[:\s]*(\d+)',
                                    r'Il tuo codice è[:\s]*(\d+)',
                                    r'verification code[:\s]*(\d+)',
                                ]
                                
                                for pattern in otp_patterns:
                                    matches = re.findall(pattern, body, re.IGNORECASE)
                                    if matches:
                                        # Get the most likely OTP (usually 4-6 digits)
                                        for match in matches:
                                            if 4 <= len(match) <= 8:
                                                otp_code = match
                                                print(f"Found OTP code: {otp_code}")
                                                break
                                    
                                    if otp_code:
                                        break
                                
                                if otp_code:
                                    break
                                    
                        except Exception as e:
                            print(f"Error processing email {email_id}: {e}")
                            continue
                    
                    if otp_code:
                        break
                        
            except Exception as e:
                print(f"Error searching with criteria '{criteria}': {e}")
                continue
        
        # Close the connection
        mail.close()
        mail.logout()
        
        if otp_code:
            print(f"Successfully retrieved OTP code: {otp_code}")
            
            # Send Telegram notification about OTP retrieval
            telegram_message = f"📧 OTP Code Retrieved\n\n✅ Successfully found OTP code: {otp_code}\n📧 From email: {email_address}\n⏰ Retrieved at: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            await send_telegram_message(telegram_message)
            
            return otp_code
        else:
            print("No OTP code found in recent emails")
            
            # Send Telegram notification about failure
            telegram_message = f"❌ OTP Code Not Found\n\n🔍 Searched recent emails in: {email_address}\n⚠️ No OTP code found\n💡 Please check if the email was received"
            await send_telegram_message(telegram_message)
            
            return None
            
    except Exception as e:
        print(f"Error retrieving OTP code: {e}")
        
        # Send Telegram notification about error
        error_message = f"🚨 OTP Retrieval Error\n\n❌ Failed to retrieve OTP code\n📧 Email: {cfg['prenotami']['username']}\n🔍 Error: {str(e)}"
        await send_telegram_message(error_message)
        
        return None

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
        # Launch browser with human-like settings
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-dev-shm-usage',
                '--disable-extensions',
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        # Create new page with additional stealth settings
        page = await browser.new_page()
        
        # Set viewport to common resolution
        await page.set_viewport_size({"width": 1366, "height": 768})
        
        # Add extra headers to look more human
        await page.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Override navigator.webdriver property
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
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
            await asyncio.sleep(random.uniform(0.3, 0.8))
            
            # Clear field first
            await email_field.fill("")
            await asyncio.sleep(0.2)
            
            # Type email character by character with random delays
            for char in cfg["prenotami"]["username"]:
                await page.keyboard.type(char)
                await asyncio.sleep(random.uniform(0.05, 0.15))
            
            # Move to password field
            print("Filling password field...")
            await asyncio.sleep(random.uniform(0.5, 1.2))
            await password_field.click()
            await asyncio.sleep(random.uniform(0.3, 0.8))
            
            # Clear field first
            await password_field.fill("")
            await asyncio.sleep(0.2)
            
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
            book_success = await click_schengen_book_button(page)
            
            if book_success:
                # Wait for potential popup or page load
                await asyncio.sleep(random.uniform(3, 6))  # Longer wait to avoid server stress
                
                # Check for and handle no-appointments popup
                popup_handled = await handle_no_appointments_popup(page)
                
                if popup_handled:
                    print("No appointments available, will retry...")
                    
                    # Send Telegram notification
                    telegram_message = f"🔄 VISA Bot Update - Attempt {attempt + 1}/{max_attempts}\n\n❌ No appointments available for VISAS/Schengen\n⏰ Will retry in 5-15 seconds\n🌐 URL: {page.url}"
                    await send_telegram_message(telegram_message)
                    
                    # Human-like delay before retry
                    if attempt < max_attempts - 1:  # Don't wait after last attempt
                        retry_delay = random.uniform(5, 15)  # Longer delay to avoid rate limiting
                        print(f"Waiting {retry_delay:.1f} seconds before retry...")
                        await asyncio.sleep(retry_delay)
                        
                        # Add some random mouse movements during wait
                        for _ in range(random.randint(2, 4)):
                            await page.mouse.move(random.randint(200, 800), random.randint(200, 600))
                            await asyncio.sleep(random.uniform(2, 5))
                    else:
                        # Send final attempt message
                        final_message = f"🛑 VISA Bot Final Update\n\n❌ All {max_attempts} attempts completed\n📋 No appointments found for VISAS/Schengen\n⏰ Script will continue monitoring\n🌐 URL: {page.url}"
                        await send_telegram_message(final_message)
                else:
                    print("No popup detected - either appointments are available or booking succeeded!")
                    # Send success notification
                    success_message = f"✅ VISA Bot Success!\n\n🎉 Booking attempt successful or appointments available!\n📋 Service: VISAS/Schengen\n🌐 URL: {page.url}\n⏰ Time: {attempt + 1}/{max_attempts} attempts"
                    await send_telegram_message(success_message)
                    break
            else:
                print("Failed to click Book button or server error occurred")
                
                # Send error notification
                error_message = f"⚠️ VISA Bot Error - Attempt {attempt + 1}/{max_attempts}\n\n❌ Failed to click Book button or server error\n📋 Service: VISAS/Schengen\n🌐 URL: {page.url}"
                await send_telegram_message(error_message)
                
                if attempt < max_attempts - 1:
                    retry_delay = random.uniform(1, 3)  # Longer delay for failed attempts
                    print(f"Waiting {retry_delay:.1f} seconds before retry...")
                    await asyncio.sleep(retry_delay)
        
        print("\n=== Booking attempts completed ===")

        # await page.reload()
        # # 找到同时包含 VISAS 和 Schengen 的行，然后点击该行的 Book 按钮
        # await page.click("//tr[td[text()='VISAS'] and td[text()='Schengen']]//button[text()='Book']")

        # Keep the page open for 10 minutes
        # await asyncio.sleep(1000)  # 600 seconds = 10 minutes
        
        # await browser.close()


asyncio.run(main())

