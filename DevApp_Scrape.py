import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains

import csv
import time
import math
import re
from datetime import datetime

# time_id = str(datetime.today().strftime('%Y-%m-%d_%H%M'))
time_id = '2018-05-16_2300' #delete after May 17th 2018 and restore above
log_folder = r'C:/Users/Fabienne/Documents/Projects/Development Applications/Logs'


def initiate_webdriver():
    '''Must be stored as variable, "driver".'''
    driver = webdriver.Edge(r'C:/Users/Fabienne/Py_Practice/MicrosoftWebDriver.exe')
    url = r"http://app.toronto.ca/DevelopmentApplications/mapSearchSetup.do?action=init"
    driver.get(url)
    time.sleep(1)
    return driver
def app_overview():
    '''finds total number of applications in all wards.
    Also logs the number of applications per ward into log.txt'''
    num_of_wards = 44
    initiate_webdriver()
    with open(os.path.join(log_folder,'log '+time_id+'.txt'),'w',newline='') as output:
        total = 0
        for ward in range(1,num_of_wards+1):
            select_ward(ward)
            submit()
            time.sleep(4)
            app_total = driver.find_element_by_xpath('//div[@id = "appResultCount"]')
            total += int(app_total.text)
            row = str("Ward "+str(ward)+" - "+app_total.text)
            print(row)
            output.writelines(row+'\n')
            break
        print("Total of",total,"applications as of", datetime.today())
        output.writelines(str("Total of "+str(total)+" applications as of "+str(datetime.today())))
def City_District(district):
    ''' Selects city district (e.g. Etobicoke, North York, Scarborough, Toronto). Must be entered exactly.'''
    City_District = driver.find_element_by_xpath('//td[@class ="dijitReset dijitStretch dijitButtonContents"]')
    ActionChains(driver).move_to_element(City_District).click().perform()
    print("Clicked!")
    time.sleep(1)
    dictionary = {"Etobicoke": 0, "North York": 1, "Scarborough": 2, "Toronto": 3}
    for i in range(0,dictionary[district]):
        ActionChains(driver).send_keys(Keys.DOWN).perform()
        time.sleep(0.5)
    ActionChains(driver).send_keys(Keys.RETURN).perform()
    time.sleep(1)
def submit():
    '''Presses the submit button.'''
    submit_button = driver.find_element_by_xpath('//span[@widgetid="dijit_form_Button_1"]') #dijit_form_Button_1_label
    submit_button.click()

# PHASE 1 - Scrape address+url from map & list

def select_ward(ward):
    ''' Selects ward.
    ward: int
    '''
    ward_dropdown = driver.find_element_by_xpath('//table[@id="wardNum"]//td')
    ActionChains(driver).move_to_element(ward_dropdown).click().perform()
    time.sleep(0.1)
    for i in range(0,ward-1):
        ActionChains(driver).send_keys(Keys.DOWN).perform()
        time.sleep(0.1)
    ActionChains(driver).send_keys(Keys.RETURN).perform()
    time.sleep(1)
def get_results(ward):
    ''' Finds all address + url by ward. Driver must already be open.
    Must execute "select_ward(ward) + submit()" prior'''

    try:
        app_total = driver.find_element_by_xpath('//div[@id = "appResultCount"]')
        app_total = app_total.text
        num_containers = math.ceil(int(app_total)/25)
        print("WARD ", ward, ". Total Applications: ",app_total, sep="")

        app_list = []

        def get_container_results(container):
            for result in container:
                #Click to show pin on map
                ActionChains(driver).move_to_element(result.find_element_by_xpath('./table')).click().perform()
                time.sleep(1.5)

                popup = driver.find_element_by_xpath('//table[@class="cmsInfoWindowTable"]//a') #why does this grab old one if new one unavailable???
                address = result.find_element_by_xpath('.//tr/td[1]')
                address = address.text
                ward = result.find_element_by_xpath('.//tr/td[2]')
                ward = ward.text
                date = result.find_element_by_xpath('.//tr/td[3]')
                date = date.text
                url = popup.get_attribute("href")

                row = [address,ward,date,url]
                # print(row)
                app_list.append(row)

        for i in range(1,num_containers+1):
            container_xpath = '//div[@class = "dojoxGridContent"]//div['+str(i)+']//div'
            container = driver.find_elements_by_xpath(container_xpath)
            get_container_results(container)

        # Sometimes containers not enough to grab all apps in results table. Additional containers are needed.
        additional = 0
        while len(app_list) < int(app_total):
            container = driver.find_elements_by_xpath('//div[@class="dojoxGridContent"]//div[3]//div') # container 3 is arbitrary
            get_container_results(container)
            additional += 1

        #Results Review
        if additional > 0:
            print(num_containers, "containers, plus additional", additional)
        else:
            print(num_containers, "containers.")
        return app_list

    except:
        print("Something went wrong - retrying...")
        time.sleep(30)
        get_results()
def save_all_wards():
    '''Retrieves development applications from all 44 wards.
    Requires initiate_webdriver(), select_ward(), get_results(), submit(), and  to run.'''

    t1_start = time.perf_counter()

    def write_to_file(ward):
        '''write to file, with custom seconds - wards 20 and 27 take longer
        i: default
        wait_secs: int '''
        try:
            if ward == 20 or ward == 27:
                wait_secs = 30
            else:
                wait_secs = 15

            filename = 'ward' + str(ward) +' '+time_id+'.txt'

            with open(filename, 'w', encoding='utf-8', newline='') as file:
                # write a function that scrolls up -- otherwise can't select ward...
                select_ward(ward)
                submit()
                time.sleep(wait_secs)
                results = get_results(ward)
                # print(results)
                writer = csv.writer(file, delimiter=',')
                writer.writerows(results)
                print('Successful write to file ward', ward)
        except:
            print("Failed to write to ward ", ward,". Retrying...", sep="")
            os.remove(filename)
            search_container = driver.find_element_by_xpath('//div[@widgetid="dataFilterContainer_wrapper"]')
            ActionChains(driver).move_to_element(search_container).click().perform()
            time.sleep(2)
            write_to_file(ward)

    for ward in [ward for ward in range(1,45)]:
        write_to_file(ward)

    t1_end = time.perf_counter()
    print("Save_all_wards run time: %.1f [min]" % ((t1_end - t1_start) / 60))

# PHASE 2 - Aggregate all wards (wardxx.txt) into one reference file ('master.csv').

def txt_compiler():
    ''' Returns total number of apps.'''
    files = re.findall(str("ward[0-9]{1,2}\s"+time_id+"\.txt"), str(os.listdir()))
    app_counter = 0
    with open('master.csv', 'w', newline='', encoding='utf-8') as master:
        for file in files:
            with open(file,'r', newline='') as child:
                for line in child:
                    master.write(line)
                    app_counter += 1
    print(len(files), "ward textfiles compiled.", app_counter, "applications total.")
    return app_counter

# PHASE 3 (FINAL) - from master csv

def get_details(address=None,ward=None,url=None):
    test1 = r"http://app.toronto.ca/DevelopmentApplications/associatedApplicationsList.do?action=init&folderRsn=3321559&isCofASearch=false&isTlabSearch=false"
    test2 = r"http://app.toronto.ca/DevelopmentApplications/associatedApplicationsList.do?action=init&folderRsn=3302641&isCofASearch=false&isTlabSearch=false"
    #1 yonge:
    test3 = r"http://app.toronto.ca/DevelopmentApplications/associatedApplicationsList.do?action=init&folderRsn=3307989&isCofASearch=false&isTlabSearch=false"
    test4 = r"http://app.toronto.ca/DevelopmentApplications/associatedApplicationsList.do?action=init&folderRsn=1331885&isCofASearch=false&isTlabSearch=false"
    test5 = r"http://app.toronto.ca/DevelopmentApplications/associatedApplicationsList.do?action=init&folderRsn=3850168&isCofASearch=false&isTlabSearch=false"
    test6 = r"http://app.toronto.ca/DevelopmentApplications/associatedApplicationsList.do?action=init&folderRsn=3928679&isCofASearch=false&isTlabSearch=false"
    test7 = r"http://app.toronto.ca/DevelopmentApplications/associatedApplicationsList.do?action=init&folderRsn=2956244&isCofASearch=false&isTlabSearch=false"
    # error page:
    test8 = r"http://app.toronto.ca/DevelopmentApplications/associatedApplicationsList.do?action=init&folderRsn=1666313&isCofASearch=false&isTlabSearch=false"

    if url == None:
        row = [address, ward, "Property not mapped. No url available."]
    else:
        driver.get(url)
        try:
            header = driver.find_element_by_xpath('//h3')
            ward = str(re.findall('^[A-Za-z\s0-9]{7}',header.text.split('\n')[1])).strip('[]')[-3:-1]

            smalltext = driver.find_elements_by_xpath('/ html / body / table[2] / tbody / tr / td / table / tbody / tr[3]//td[@class = "smallText"]')
            description = smalltext[0].text.strip()
            proposed_use = smalltext[1].text.replace("Proposed Use", "").strip()
            storeys = re.sub('[^0-9]', '', smalltext[2].text)
            units = re.sub('[^0-9]', '', smalltext[3].text)

            # Unhide secondary addresses and supporting documentation tabs:
            addresspath = '//table[2]/tbody/tr/td/table/tbody/tr[2]/td[2]'
            address2_container = driver.find_element_by_xpath(addresspath+'/a')
            address2_container.send_keys(Keys.RETURN)
            unhide = driver.find_elements_by_xpath('//a[@class = "slideToggle"]')
            for i in unhide:
                i.send_keys(Keys.RETURN)
            time.sleep(0.5)

            address2 = driver.find_element_by_xpath(addresspath+'//table')
            address2 = [" ".join(address2.text.replace('\n',',').split())]

            # Location of planner info varies between -2 and -3 position depending on if Building Permit Info is available.
            plan = driver.find_elements_by_xpath('//td[@class = "smallText"]')
            if "A building permit application has been applied for" in plan[-1].text:
                planner = plan[-3].text.replace('\n', ', ')
            else:
                planner = plan[-2].text.replace('\n', ', ') # varies between -2 and -3

            app_path = '/html/body/table[2]/tbody/tr/td/table/tbody/tr[3]/td[2]/table[1]/tbody/tr[3]/td/table/tbody'
            all_apps = driver.find_elements_by_xpath(app_path+'//td[@class = "smallText"]')
            app_list = [row.text.strip() for row in all_apps]
            num_apps = len(all_apps)/4
            new_app_list = [app_list[i:i+4] for i in range(0,len(app_list),4)]

            # Supporting docs:
            box = driver.find_elements_by_xpath('//div[@class = "slideTogglebox"]')
            supp_docs = [re.sub("\nDownload \n\n", ";", package.text.strip().replace("Disclaimer|\xa0", "")) for package in box]
            # This only works if each application has supporting documents. Otherwise length does not match:
            # [new_app_list[app].append(supp_docs[app]) for app in range(0,len(new_app_list))]

            # Most Recent and Earliest Activity
            date_format = '[A-Z][a-z]{2}\s[0-9]{1,2}\,\s[0-9]{4}'
            all_dates = re.findall(date_format,str(supp_docs + new_app_list))
            formatted_dates = [datetime.strptime(i, '%b %d, %Y') for i in all_dates]
            most_recent = datetime.strftime(max(formatted_dates), '%b %d, %Y')

            # Oldest Activity
            oldest_doc = datetime.strftime(min(formatted_dates), '%b %d, %Y')

            row = [address, oldest_doc, most_recent, address2, ward, description, proposed_use, storeys, units,
                   planner, num_apps, new_app_list, supp_docs, url]

        except:
            flag = driver.find_element_by_xpath('//div[@id = "listTbl"]')
            if "Please try again later." in flag.text:
                row = [address,"Page error!", url]

    return row
def scrape_master(master_file='master.csv'):
    """Assumes input document is a csv file, "master.csv", which contains all apps.
    Requires get_details() to run. """

    t2_start = time.perf_counter()
    with open(master_file, 'r') as master:
        reader = csv.reader(master)
        id = 'DevApps'+time_id+'.csv'
        tracker = 0
        with open(id, 'w', newline='',encoding='utf-8') as output:
            output.write(
                "Address,First_Activity,Last_Activity,All_Addresses,Ward,Description,Proposed_Use,Storeys,Units,Planner,Num_apps,Apps,Supporting_Docs,Link\n")
            writer = csv.writer(output)
            for app in reader:
                app_info = get_details(address = app[0],ward=app[1],url = app[3])
                writer.writerow(app_info)
                tracker += 1
                if tracker == any([1,200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800]): #this doesn't work lol wtf
                    print(tracker, "apps printed.")
                    print(app_info)
    t2_end = time.perf_counter()
    print("Scrape time: %.1f [min]" % ((t2_end-t2_start)/60))
    driver.close()

###

def run_program():
    start_time = time.perf_counter()
    global driver
    # driver = initiate_webdriver()
    # save_all_wards()
    # driver.close()
    total_num_apps = txt_compiler()
    print("Total number of apps:", total_num_apps,"\nInitialize Phase 2.")
    driver = initiate_webdriver()
    scrape_master()
    driver.close()
    end_time = time.perf_counter()
    print("Total time elapsed: %.1f minutes" % ((end_time - start_time)/60))


if __name__ == "__main__":
    run_program()
    print('finished!')
