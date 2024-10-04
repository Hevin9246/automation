import gc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from faker import Faker
import undetected_chromedriver as uc
import time
import random
import pandas as pd
import logging


fake = Faker()

def human_like_delay(min_delay=0.1, max_delay=1.0):
    time.sleep(random.uniform(min_delay, max_delay))

def type_like_a_human(element, text):
    for char in text:
        element.send_keys(char)
        human_like_delay(0.1, 0.3)

def read_credentials_from_excel(file_path, start_index, end_index):
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        sliced_df = df.iloc[start_index:end_index + 1]
        credentials = [
            (
                idx,
                row['pan'],
                row['password'],
                row['error'],
                row['tax refund status'],
                row['refund status date'],
                row['last assessment year'],
                row['response submitted'],
                row['pending status'],
                row.get('last processed date')
            ) for idx, row in sliced_df.iterrows()
        ]
        return df, credentials
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None, []
    
def write_to_excel(df, file_path):
    try:
        # Use Pandas' ExcelWriter with openpyxl engine to modify the existing file
        with pd.ExcelWriter(file_path, engine='openpyxl', mode='w') as writer:
            df.to_excel(writer, index=False)  # Write DataFrame without row indices
            writer.save() 
        # create_or_update_backup(file_path)  # Optional: Create a backup file
        print(f"Data successfully written back to {file_path}")
    except PermissionError as e:
        print(f"Error writing to Excel file: {e}. Please close the file if it is open and try again.")
    except Exception as e:
        print(f"Error writing to Excel file: {e}")

def get_chrome_options():
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")  # Bypass OS security model
    options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")  # Set window size (some websites require this)
    options.add_argument("--log-level=1")

    # Set the binary location for Chromium (important for Render)
    options.binary_location = "/usr/bin/chromium-browser"

    logging.info(f"Chromium binary location set to: {options.binary_location}")

    
    return options

def perform_login_and_action(pan, password, df, index):
    logging.info("1")
    options = get_chrome_options()
    logging.info("2")
    driver = uc.Chrome(options=options)
    logging.info("3")

    try:
        

        driver.get("https://eportal.incometax.gov.in/iec/foservices/#/login")
        human_like_delay(1, 3)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "panAdhaarUserId")))

        username_field = driver.find_element(By.ID, "panAdhaarUserId")
        username_field.send_keys(pan)
        human_like_delay(2, 4)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button')))
        continue_buttons = driver.find_elements(
            By.CSS_SELECTOR, '#maincontentid > app-login > div > app-login-page > div > div.row.card-border > div.col-md-12.col-lg-5.login.card-padding.whiteBackground.radius4 > div:nth-child(4) > button')
        for button in continue_buttons:
            if button.find_element(By.CSS_SELECTOR, "span").text.strip().lower() == "continue":
                button.click()
                break
        df.at[index, 'error'] = "panAdhaarUserId entered successfull."
        print("panAdhaarUserId entered successfull.")
        human_like_delay(2, 4)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "loginPasswordField")))

        password_field = driver.find_element(By.ID, "loginPasswordField")
        password_field.send_keys(password)
        human_like_delay(2, 4)

        checkbox = driver.find_element(By.ID, "passwordCheckBox")
        if not checkbox.is_selected():
            checkbox.click()
        human_like_delay(2, 4)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button')))
        continue_buttons = driver.find_elements(
            By.CSS_SELECTOR, '#maincontentid > app-login > div > app-password-page > div.container > div.row.card-border.lightBackgroundColor > div.col-lg-5.login.card-padding.whiteBackground > div:nth-child(6) > button')
        for button in continue_buttons:
            if button.find_element(By.CSS_SELECTOR, "span").text.strip().lower() == "continue":
                button.click()
                break
        df.at[index, 'error'] = "loginPasswordField entered successfull."
        print("loginPasswordField entered successfull.")
        human_like_delay(2, 4)

        try:
            otp_message = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#maincontentid > app-login > div > app-otp-options > div > div.row.card-border.lightBackgroundColor > div.col-lg-5.login.whiteBackground.card-padding > h1")))
            df.at[index, 'error'] = "OTP occurred"
            print("OTP occurred")

        except Exception:

            try:
                error_message = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "/html/body/app-root/div[1]/div[3]/app-login/div/app-password-page/div[1]/div[2]/div[1]/div[4]/mat-error/div/div/span[2]"))
                )
                df.at[index, 'error'] = "Incorrect password. Please try again."
                print("Incorrect password. Please try again.")
            except Exception:

                try:
                    login_here_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//button[contains(text(), 'Login Here')]"))
                    )
                    login_here_button.click()
                    human_like_delay(2, 4)
                except Exception as e:
                    print("No session already active message appeared")

                pending_action_link = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
                    (By.XPATH, "/html/body/app-root/div[1]/div[1]/app-navbar/mat-toolbar/div/div/div[1]/a[6]")))
                actions = ActionChains(driver)
                # human_like_delay(2, 4)
                actions.move_to_element(pending_action_link).perform()
                # human_like_delay(2, 4)

                worklist_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[text()='Response to Outstanding Demand']")))
                worklist_link.click()
                human_like_delay(1, 3)

                try:
                    # Fetch assessment year
                    assessment_year = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "#maincontentid > app-dashboard > app-response-to-outstanding-demand > div > app-master > div > div.row3 > div.col-md-12 > div > div.row.pl-3.pr-3.ng-star-inserted > div > div.row.flex-row.d-flex.m-0.innerBoxHeader > div.col-lg-10.p-0.m-0.headline-5-text.color-code-087.d-flex.mob-disp-block > div > span.heading5"))
                    )
                    human_like_delay(2, 4)
                    assessment_year_text = assessment_year.text
                    # print(f"Assessment year: {assessment_year_text}")
                except Exception as e:
                    assessment_year_text = "No assessment year found"
                    df.at[index, 'error'] = "No assessment year found"
                    print("No assessment year found")

                try:
                    # Fetch demand amount
                    demand_amount = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "#maincontentid > app-dashboard > app-response-to-outstanding-demand > div > app-master > div > div.row3 > div.col-md-12 > div > div.row.pl-3.pr-3.ng-star-inserted > div > div.card-body > div > div.col-lg-3.col-md-3.col-width > section > div"))
                    )
                    human_like_delay(2, 4)
                    demand_amount_text = demand_amount.text
                    # print(f"Demand amount: {demand_amount_text}")
                except Exception as e:
                    demand_amount_text = "No demand amount found"
                    df.at[index, 'error'] = "No demand amount found"
                    print("No demand amount found")

                # Save both in the same column
                df.at[index, 'last assessment year'] = f"Assessment Year: {assessment_year_text}, Demand Amount: {demand_amount_text}"
                print(f"Assessment Year: {assessment_year_text}, Demand Amount: {demand_amount_text}");


    except Exception as e:
        df.at[index, 'error'] = "please try again"
        print(e)

    finally:
        # time.sleep(1)
        gc.collect()
        driver.quit()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])

def run_automation(file_path, start_index, end_index):
    logging.info(f"Starting automation with file: {file_path}, start_index: {start_index}, end_index: {end_index}")

    # Convert 1-based indices to 0-based indices
    start_index = start_index - 1
    end_index = end_index - 1
    logging.info(f"Converted indices: start_index={start_index}, end_index={end_index}")

    # Read the Excel file and get the credentials between the start and end indices
    df, credentials = read_credentials_from_excel(file_path, start_index, end_index)
    logging.info(f"Credentials extracted: {len(credentials)} rows to process")

    if credentials:
        for index, pan, password, *rest in credentials:
            if isinstance(pan, str) and isinstance(password, str):
                logging.info(f"Attempting login for PAN: {pan}")

                # Perform the login and action
                perform_login_and_action(pan, password, df, index)
                logging.info(f"Action completed successfully for PAN: {pan}")
                
                # Optionally update the 'error' field or other existing fields
                df.at[index, 'error'] = "Action completed successfully"  # Example of modifying the existing 'error' column
                logging.error(f"Action failed for PAN: {pan}. Error: {str(e)}")

    # After processing, write the updated DataFrame back to the Excel file
    logging.info(f"Writing back to the Excel file: {file_path}")
    write_to_excel(df, file_path)
    logging.info("Automation process completed")
