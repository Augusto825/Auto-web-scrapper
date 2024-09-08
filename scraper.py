from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time
import csv
import ftplib
import io

def goto_SearchView(search_keys, writer):
    for address, street in search_keys:
        # Set up the Chrome driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)

        try:
            # Go to the disclaimer page
            driver.get('https://assessorpropertydetails.cookcountyil.gov/Search/Disclaimer.aspx?FromUrl=../search/commonsearch.aspx?mode=address')

            # Wait for the "Agree" button to be visible and then click it
            agree_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'btAgree')))
            agree_button.click()

            # Wait for the navigation to complete
            WebDriverWait(driver, 10).until(EC.url_matches('.*commonsearch.aspx.*'))

            enterKey_getResult(address, street, driver, writer)

        finally:
            # Close the browser
            driver.quit()

def enterKey_getResult(address, street, driver, writer):
    # Now on the search page, locate the input fields and the search button
    inp_number = driver.find_element(By.ID, 'inpNumber')
    inp_street = driver.find_element(By.ID, 'inpStreet')
    bt_search = driver.find_element(By.ID, 'btSearch')
    # Clear input fields before entering new values
    inp_number.clear()
    inp_street.clear()

    # Fill in the search form
    inp_number.send_keys(address)
    inp_street.send_keys(street)

    # Click the search button
    bt_search.click()

    # Wait for the results to load
    time.sleep(3)  # Adjust sleep time as necessary

    try:
        next_button_element = driver.find_element(By.XPATH, "//b[contains(text(), 'Next >>')]")
        nextbtn = next_button_element.find_element(By.XPATH, '..')
        # Check if "IndexLink" element exists before iterating
        if nextbtn:
            gotoDetail_clickNextBTN(address, street, driver, writer)

    except NoSuchElementException:
        # If not found, go to detail
        getTop4_categoryResult(address, street, driver, writer)

def gotoDetail_clickNextBTN(address, street, driver, writer):
    # Locate the table with id "searchResults"
    search_results_table = driver.find_element(By.ID, "searchResults")

    # Locate the first tr tag with class name "SearchResults"
    first_tr_element = search_results_table.find_element(By.CSS_SELECTOR, "tr.SearchResults")
    
    first_tr_element.click()
    
    time.sleep(5)

    from_to_value = driver.find_element(By.ID, "DTLNavigator_txtFromTo").get_attribute("value")
    preceding_number, following_number = map(int, from_to_value.split(" of "))

    while preceding_number < following_number+1 :

        title = driver.find_element(By.CSS_SELECTOR, "td.DataletHeaderTop").text
        
        driver.find_element(By.ID, "DTLNavigator_imageNext")

        from_to_value = driver.find_element(By.ID, "DTLNavigator_txtFromTo").get_attribute("value")

        # Split the value to get the preceding and following numbers
        preceding_number, following_number = map(int, from_to_value.split(" of "))

        next_icon = driver.find_element(By.ID, "DTLNavigator_imageNext")

        next_icon.click()

        time.sleep(5)
        
        writer.writerow([title, "", "", "", ""])
        getTop4_categoryResult("", "", driver, writer)
    
def getTop4_categoryResult(address, street, driver, writer):
    # Find the sidemenu and extract all anchor tags within it
    categories_elements = driver.find_elements(By.CSS_SELECTOR, '#sidemenu a')
    categories_info = [(elem.text, elem.get_attribute('href')) for elem in categories_elements]

    # Iterate over the first 4 category URLs and get HTML content
    for index, (inner_text, category_url) in enumerate(categories_info[:4]):
        # Navigate to the category page
        driver.get(category_url)

        # Wait for the page to load
        time.sleep(3)

        # Locate the div with class 'holder'
        holder_div = driver.find_element(By.CLASS_NAME, 'holder')

        # Find all tables inside the holder div
        tables = holder_div.find_elements(By.TAG_NAME, 'table')

        # Ensure there are at least two tables and select the second one
        if len(tables) >= 2:
            second_table = tables[1]

            # Find all tr elements inside the second table
            rows = second_table.find_elements(By.TAG_NAME, 'tr')

            first_row = True  # Flag to check if it's the first row

            # Iterate through each row and get the text from the td elements
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, 'td')
                if len(cols) >= 2:
                    title = cols[0].text.strip()
                    value = cols[1].text.strip()

                    if first_row:
                        writer.writerow([address, street, inner_text, title, value])
                        first_row = False  # Set the flag to False after the first row
                    else:
                        writer.writerow(["", "", "", title, value])

def prepareCSV_searchStart(search_keys, csv_filename):

    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['address', 'street', 'category', 'title', 'value'])

        goto_SearchView(search_keys, writer)

# Function to get the list of files in the directory
def get_file_list(ftp):
    file_names = ftp.nlst()
    file_names = [file_name for file_name in file_names if file_name not in ('.', '..')]
    return file_names

# Function to download and read file content
def download_and_read_file(ftp, filename):
    csv_data = io.BytesIO()
    ftp.retrbinary('RETR ' + filename, csv_data.write)
    csv_data.seek(0)
    
    csv_data = io.TextIOWrapper(csv_data, encoding='utf-8')
    csv_reader = csv.reader(csv_data, delimiter=",")
    print("+++++++++++++++++++++", csv_reader)
    # Skip the first row (header)
    next(csv_reader)
    print("==================", csv_reader)
    return csv_reader

# Prepare the CSV file
basename ='ill_prop_records_'
now = datetime.now()
# Extract year, month, date, hour, minute, second
year = str(now.year)
month = str(now.month)
date = str(now.day)
hour = str(now.hour)
minute = str(now.minute)
second = str(now.second)
csv_filename = basename + year + '_' + month + '_' + date + '_' + hour + '_' + minute + '_' + second + '.csv'

# FTP server details
ftp_server = 'malachairising.com'
ftp_user = 'freelancer@burgerkingclaim.com'
ftp_password = 'Freelancer2024@900AM'
source_directory_path = '/wp-content/ill_prop_addresses'
upload_directory_path = '/wp-content/ill_prop_records'

# Connect to the FTP server
ftp = ftplib.FTP(ftp_server)
ftp.login(user=ftp_user, passwd=ftp_password)
ftp.cwd(source_directory_path)

# Initialize the previous file list
previous_files = get_file_list(ftp)

try:
    while True:
        # Get the current list of files
        current_files = get_file_list(ftp)
        
        # Identify new files
        new_files = [file for file in current_files if file not in previous_files]
        # Process new files
        if(len(new_files) > 0):
            # for new_file in new_files:
            new_file = new_files[-1]
            print(f"New file detected: {new_file}")
            search_keys = download_and_read_file(ftp, new_file)
            prepareCSV_searchStart(search_keys, csv_filename)

            # Change to the desired directory
            ftp.cwd(upload_directory_path)

            # Open the local file in binary mode
            with open(csv_filename, 'rb') as file:
                # Upload the file
                ftp.storbinary(f'STOR {csv_filename}', file)

            print("File uploaded successfully.")
            ftp.cwd(source_directory_path)
        
        # Update the previous file list
        previous_files = current_files
        
        # Wait before checking again
        time.sleep(5)  # Check for new files every 3 seconds



except KeyboardInterrupt:
    print("Monitoring stopped by user")

# Close the FTP connection
ftp.quit()