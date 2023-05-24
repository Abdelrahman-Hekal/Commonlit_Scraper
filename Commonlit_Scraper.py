from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService 
import undetected_chromedriver as uc
import pandas as pd
import time
import unidecode
import csv
import sys
import numpy as np

def initialize_bot():

    # Setting up chrome driver for the bot
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # installing the chrome driver
    driver_path = ChromeDriverManager().install()
    chrome_service = ChromeService(driver_path)
    # configuring the driver
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    ver = int(driver.capabilities['chrome']['chromedriverVersion'].split('.')[0])
    driver.quit()
    chrome_options = uc.ChromeOptions()
    #chrome_options.add_argument('--headless')
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.page_load_strategy = 'normal'
    chrome_options.add_argument("--disable-notifications")
    # disable location prompts & disable images loading
    prefs = {"profile.default_content_setting_values.geolocation": 1, "profile.managed_default_content_settings.images": 1, "profile.default_content_setting_values.cookies": 1}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = uc.Chrome(version_main = ver, options=chrome_options) 
    driver.set_window_size(1920, 1080)
    driver.maximize_window()
    driver.set_page_load_timeout(300)

    return driver

def login(driver):

    driver.get('https://www.commonlit.org/en/user/login')
    time.sleep(5)
    username = wait(driver, 90).until(EC.presence_of_element_located((By.XPATH, "//input[@name='login' and @id='login']")))
    username.send_keys('brandperformancedata@gmail.com')
    time.sleep(3)
    password = wait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//input[@name='password' and @id='password']")))
    password.send_keys('asd2376312')
    time.sleep(3)
    button = wait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//button[@class='cl-button medium cl-primary-btn' and @type='submit']")))
    driver.execute_script("arguments[0].click();", button)
    time.sleep(5)

    return driver

def scrape_commonlit(path):

    start = time.time()
    print('-'*75)
    print('Scraping commonlit.org ...')
    print('-'*75)
    # initialize the web driver
    driver = initialize_bot()

    # initializing the dataframe
    data = pd.DataFrame()

    # if no books links provided then get the links
    if path == '':

        #login
        driver = login(driver)
        name = 'commonlit_data.csv'   
        links = []
        # scraping books urls
        driver.get('https://www.commonlit.org/en/library?contentTypes=text&initiatedFrom=library&language=english')
        nbooks = 0
        while True:
            titles = wait(driver, 90).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.cl-card-body")))
            for title in titles:        
                try:
                    cat = wait(title, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.cl-label.blue"))).get_attribute('textContent').strip()
                    url = wait(title, 2).until(EC.presence_of_element_located((By.TAG_NAME, "a"))).get_attribute('href')
                    links.append((url, cat))
                    nbooks += 1
                    print(f'Scraping url for book {nbooks}')
                except Exception as err:
                    pass

            # check for the last page to stop
            try:
                wait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//a[@class='page-number-link disabled' and @aria-label='Next Page']")))
                break
            except:
                pass

            # moving to the next page
            try:
                link = wait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//a[@aria-label='Next Page']"))).get_attribute('href')
                driver.get(link)
            except:
                break

        # saving the links to a csv file
        print('Exporting links to a csv file ....')
        with open('commonlit_links.csv', 'w', newline='\n', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Link', 'Category'])
            for row in links:
                writer.writerow([row[0], row[1]])


    scraped = []
    if path != '':
        df_links = pd.read_csv(path)
        driver = login(driver)
    else:
        df_links = pd.read_csv('commonlit_links.csv')

    links = df_links['Link'].values.tolist()
    cats = df_links["Category"].values.tolist()
    name = path.split('\\')[-1][:-4]
    name = name + '_data.xlsx'
    try:
        data = pd.read_excel(name)
        scraped = data['Title Link'].values.tolist()
    except:
        pass
    # scraping books details
    print('-'*75)
    print('Scraping Books Info...')
    n = 0
    for i, link in enumerate(links):
        try:      
            if link in scraped: continue
            driver.get(link)
            time.sleep(2)
            details = {}
            print(f'Scraping the info for book {n+1}')
            n += 1

            title = ''
            try:
                title = wait(driver, 2).until(EC.presence_of_element_located((By.TAG_NAME, "h1"))).get_attribute('textContent').strip()
            except:
                pass

            details['Title'] = title
            details['Title Link'] = link

            author, date = '', ''
            try:
                tags = wait(driver, 2).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.byline")))
                for tag in tags:
                    text = tag.get_attribute('textContent')
                    if 'by' in text:
                        author = text.replace('by', '').strip()
                    else:
                        try:
                            date = int(text)
                        except:
                            pass
            except:
                pass

            details['Author'] = author
            details[' Release Year'] = date

            # grade
            grade = ''
            try:
                grade = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.label.label-success"))).get_attribute('textContent').strip()
            except:
                pass          
                
            details['Grade'] = grade                
                
            # lexile
            lexile = ''
            try:
                lexile = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.label.label-info"))).get_attribute('textContent').split(':')[-1].strip()
            except:
                pass          
                
            details['Lexile'] = lexile                

            details['Category'] = cats[i]                   
            # appending the output to the datafame            
            data = data.append([details.copy()])
            # saving data to csv file each 100 links
            if np.mod(i+1, 100) == 0:
                print('Outputting scraped data to Excel sheet ...')
                data.to_excel(name, index=False)
        except:
            pass

    # optional output to Excel
    data.to_excel(name, index=False)
    elapsed = round((time.time() - start)/60, 2)
    print('-'*75)
    print(f'commonlit.org scraping process completed successfully! Elapsed time {elapsed} mins')
    print('-'*75)
    driver.quit()

    return data

if __name__ == "__main__":
    
    path = ''
    if len(sys.argv) == 2:
        path = sys.argv[1]
    data = scrape_commonlit(path)

