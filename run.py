import lxml.html as html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json


# file creation and append logic
def append_to_file_json(filename, data_list):
    with open(filename, mode='a+') as f:
        f.seek(0)
        file_contents = f.read()

        if len(file_contents) == 0:
            f.write('[' + json.dumps(data_list) + ']')
        else:
            json_contents = get_json_from_file(filename)
            json_contents.append(data_list)
            json_contents_to_string = json.dumps(json_contents)
            write_json_to_file(filename, json_contents_to_string)


# separate write function to avoid overwriting file before its contents are read
def write_json_to_file(filename, data):
    with open(filename, mode='w+') as file:
        file.write(data)


# read the file contents and return contents as json
def get_json_from_file(filename):
    with open(filename, mode='r') as file:
        contents = file.read()
        return json.loads(contents)


# get the the value of the last pagination element to identify total number of pages
def get_number_of_pages(page_content):
    last_page_elem_attr_value = page_content.xpath('string(//div[@class="pageNumbers"]/*[@data-page-number][last()])')
    return int(float(last_page_elem_attr_value))


# get the number of items located on given page
def get_number_of_page_links(page_content):
    page_links_list = page_content.xpath('//div[@id="EATERY_SEARCH_RESULTS"]/*[@data-index]')
    return len(page_links_list)


# creating single working days if received e.g. 'Fri'
def create_single_working_day(days_string, hours, days, target_obj):
    for day in days:
        if day.get(days_string) is not None:
            split_hours = hours.replace(' ', '').split('-')
            target_obj[day.get(days_string)] = {'open': split_hours[0], 'close': split_hours[1]}


# get days mapping object key, e.g. out of {'Mon', 'monday'} get 'Mon',
# to apply it for searching the right day value: target_obj[day.get(current_day)]
def parse_dict_day(obj):
    for k in obj:
        return k


# creating multiple working days if received e.g. 'Fri - Sun'
def create_multiple_working_days(days_string, hours, days, target_obj):
    split_days = days_string.replace(' ', '').split('-')
    split_hours = hours.replace(' ', '').split('-')
    start_day = split_days[0]
    end_day = split_days[1]
    start_day_found = False
    end_day_found = False

    for day in days:
        if start_day_found is False and day.get(start_day) is not None:
            target_obj[day.get(start_day)] = {'open': split_hours[0], 'close': split_hours[1]}
            start_day_found = True
        elif start_day_found is True and end_day_found is False and day.get(end_day) is None:
            current_day = parse_dict_day(day)
            target_obj[day.get(current_day)] = {'open': split_hours[0], 'close': split_hours[1]}
        elif start_day_found is True and end_day_found is False and day.get(end_day) is not None:
            target_obj[day.get(end_day)] = {'open': split_hours[0], 'close': split_hours[1]}
            end_day_found = True
        elif start_day_found is True and end_day_found is True:
            break
        else:
            continue


# read working hours data from DOM and return after parsing to required object model
def get_working_hours():
    # days mapping counter
    days_list = [
        {'Mon': 'monday'},
        {'Tue': 'tuesday'},
        {'Wed': 'wednesday'},
        {'Thu': 'thursday'},
        {'Fri': 'friday'},
        {'Sat': 'saturday'},
        {'Sun': 'sunday'}
    ]

    # find working hours clickable component and click on it to expose working hours popup
    browser.find_element(By.XPATH, '//div[@id="component_6"]').click() if len(
        browser.find_elements(By.XPATH, '//div[@id="component_6"]')) != 0 else None

    # wait until working hours popup appears to be able to read its DOM contents (dynamically injected DOM)
    wait = WebDriverWait(browser, 10)
    element = wait.until(EC.visibility_of_element_located((By.XPATH, '//div[@class="all-open-hours"]')))

    # get list of working hours element containers
    working_hours_elements = element.find_elements(By.XPATH,
                                                   '//div[@class="public-location-hours-AllHoursList__container--3f4ud ui_columns is-mobile"]')

    # iterate over working hours elements containers to extract data if there is any working hours data present
    if len(working_hours_elements):
        working_days_dict = {}
        for working_hours in working_hours_elements:
            # find element holding information on working days
            working_day = working_hours.find_element(By.XPATH,
                                                     '//div[@class="public-location-hours-AllHoursList__daysAndTimesRow--2JSVL ui_column is-5"]').text
            # find element of holding information on working hours in given day
            working_day_hours = working_hours.find_element(By.XPATH,
                                                           '//div[@class="public-location-hours-AllHoursList__daysAndTimesRow--2JSVL ui_column is-7"]').text

            # if given string doesn't contain dash '-' it means that information
            # of working hours is given for one single day (e.g. 'Sat'), otherwise for multiple days (e.g. 'Mon - Fri')
            if working_day.find('-') == -1:
                create_single_working_day(working_day, working_day_hours, days_list, working_days_dict)
            else:
                create_multiple_working_days(working_day, working_day_hours, days_list, working_days_dict)

        return working_days_dict


def return_restaurant_details(details_name, driver):
    return driver.find_element(By.XPATH, '//div[contains(text(),"' + details_name + '")]/following-sibling::div')\
        .get_attribute('innerText') if len(driver.find_elements(By.XPATH, '//div[contains(text(),"' + details_name + '")]/following-sibling::div')) != 0 else ''


def map_source_obj_with_data(driver):
    restaurant_name = driver.find_element(By.XPATH, '//div[contains(@class, "restaurantName")]/h1').get_attribute(
        'innerText') \
        if len(driver.find_elements(By.XPATH, '//div[contains(@class, "restaurantName")]/h1')) != 0 else ''
    restaurant_description = '<p>' + restaurant_name + '</p>'
    street_name = driver.find_element(By.XPATH, '//span[@class="street-address"]').get_attribute('innerText') \
        if len(driver.find_elements(By.XPATH, '//span[@class="street-address"]')) != 0 else ''
    city_and_zip_code = driver.find_element(By.XPATH, '//span[@class="locality"]').get_attribute('innerText').split() \
        if len(driver.find_elements(By.XPATH, '//span[@class="locality"]')) != 0 else ''
    phone = driver.find_element(By.XPATH, '//div[@data-blcontact="PHONE"]/a/span[@class="detail"]').get_attribute(
        'innerText') \
        if len(driver.find_elements(By.XPATH, '//div[@data-blcontact="PHONE"]/a/span[@class="detail"]')) != 0 else ''

    mail = driver.find_element(By.XPATH, '//a[contains(@href, "mailto")]').get_attribute('href') \
        if len(driver.find_elements(By.XPATH, '//a[contains(@href, "mailto")]')) != 0 else ''

    website_address = driver.find_element(By.XPATH, '//a[contains(@style, "display: none")]') \
        .get_attribute('href') if len(
        driver.find_elements(By.XPATH, '//a[contains(@style, "display: none")]')) != 0 else ''
    restaurant_location_class = 'restaurants-detail-overview-cards-LocationOverviewCard__mapImage--rAA8X'
    restaurant_location_url = driver.find_element(By.XPATH,
                                                  '//img[@class="' + restaurant_location_class + '"]').get_attribute(
        'src') \
        if len(driver.find_elements(By.XPATH, '//img[@class="' + restaurant_location_class + '"]')) != 0 else ''
    restaurant_location_data = restaurant_location_url.split('|')[1].split(',') \
        if restaurant_location_url.find('|') > -1 else ''
    rating_class = 'restaurants-detail-overview-cards-RatingsOverviewCard__overallRating--r2Cf6'
    rating = driver.find_element(By.XPATH, '//span[@class="' + rating_class + '"]').get_attribute('innerText').replace(
        '\xa0', '') \
        if len(driver.find_elements(By.XPATH, '//span[@class="' + rating_class + '"]')) != 0 else ''

    price_range_string = driver.find_element(By.XPATH,
                                             '//div[@class="restaurants-details-card-DetailsCard__innerDiv--2uDs1"]/div[position()=2]/div/div[position()=2]/div/div[@class="restaurants-details-card-TagCategories__tagText--2170b"]').text \
        if len(driver.find_elements(By.XPATH,
                                    '//div[@class="restaurants-details-card-DetailsCard__innerDiv--2uDs1"]/div[position()=2]/div/div[position()=2]/div/div[@class="restaurants-details-card-TagCategories__tagText--2170b"]')) != 0 else ''
    price_range_list = price_range_string.replace(' ', '').replace('€', '').split('-') if len(
        price_range_string) > 0 else []
    review_count = driver.find_element(By.XPATH, '//span[@class="reviewCount"]').text.replace(' reviews', '').replace(
        ' review', '') if len(driver.find_elements(By.XPATH, '//span[@class="reviewCount"]')) != 0 else ''

    cuisines = return_restaurant_details('CUISINES', driver)
    meals = return_restaurant_details('Meals', driver)
    special_diets = return_restaurant_details('Special Diets', driver)
    features = return_restaurant_details('FEATURES', driver)

    obj_template = {
        "active": 1,
        "sectionId": "",
        "categoryId": "",
        "companyId": None,
        "paid": 1,
        "paidTots": None,
        "badge": "none",
        "title": restaurant_name,
        "alias": restaurant_name.lower(),
        "placeType": [
            "restaurant"
        ],
        "timeZone": "Europe/Riga",
        "description": restaurant_description,
        "tags": [],
        "address": {
            "street": street_name,
            "zipCode": ('LV' + city_and_zip_code[1]) if isinstance(city_and_zip_code, list) and len(
                city_and_zip_code) > 1 else '',
            "city": city_and_zip_code[0] if isinstance(city_and_zip_code, list) else '',
            "state": "xx",
            "country": "lv"
        },
        "contacts": {
            "phone": phone,
            "fax": "",
            "email": mail.replace('mailto:', '').split('?')[0] if len(mail) > 0 else '',
            "skype": "",
            "website": website_address,
            "social": {}
        },
        "location": {
            "lon": restaurant_location_data[1] if len(restaurant_location_data) > 1 else '',
            "lat": restaurant_location_data[0] if len(restaurant_location_data) > 1 else ''
        },
        "gallery": [
            {
                "src": "https://media-cdn.tripadvisor.com/media/photo-f/11/04/20/f7/faroe-islands-langoustine.jpg"
            }
        ],
        "videos": [],
        "workHours": get_working_hours(),
        "reservationConfig": {
            "tableTypes": [
                "standard",
                "outdoor"
            ],
            "tables": "3",
            "skipAfterOpen": "60",
            "skipBeforeClose": "60",
            "lockAfterReservation": "120",
            "step": "30",
            "enabled": "1"
        },
        "attendingCost": {
            "min": price_range_list[0] if len(price_range_list) > 1 else 0,
            "max": price_range_list[1].replace(',', '') if len(price_range_list) > 1 else 0,
            "currency": "eur"
        },
        "translation": {
            "lv": {
                "title": restaurant_name,
                "description": restaurant_description,
                "metaKeys": restaurant_name.lower(),
                "metaDesc": restaurant_name.lower()
            },
            "ru": {
                "title": restaurant_name,
                "description": restaurant_description,
                "metaKeys": restaurant_name.lower(),
                "metaDesc": restaurant_name.lower()
            }
        },
        "extraFields": {
            "cuisines": [cuisines],
            "meals": [meals],
            "diets": [special_diets],
            "features": [features],
            "languages": [],
            "ratings": {
                "food": 0,
                "product_quality": 0,
                "serving": 0,
                "atmosphere": 0,
                "hospitality": 0,
                "waiters": 0,
                "prices": 0
            }
        },
        "rating": rating,
        "votes": review_count,
        "metaKeys": restaurant_name.lower(),
        "metaDesc": restaurant_name,
        "createdBy": "",
        "updatedBy": "",
        "createdTs": int(time.time()) * 1000,
        "updatedTs": int(time.time()) * 1000,
        "orderFoodConfig": {
            "enabled": 0,
            "minPrice": 5
        },
        "priceLevel": 0
    }

    return obj_template


base_url = 'https://www.tripadvisor.com/Restaurants-g274967-Riga_Riga_Region.html'
opened_page = 1

# linux chromedriver path: /mnt/c/chromedriver.exe
# windows chromedriver path: C:\\chromedriver.exe

browser = webdriver.Chrome("C:\\chromedriver.exe")
browser.get(base_url)
time.sleep(5)
content = browser.page_source
trip_content = html.document_fromstring(content)
contents_seen = 0

pages_total = get_number_of_pages(trip_content)
main_window = browser.current_window_handle

while opened_page <= pages_total:
    contents_seen = 0
    # get the number of restaurant links on given search results page
    page_content_count = get_number_of_page_links(trip_content)

    while contents_seen < page_content_count:
        # get the list of currently opened page restaurant list items
        all_restaurants_link_elements = browser.find_elements(By.XPATH, '//a[@class="photo_link"]')

        # click page content item (restaurant)
        all_restaurants_link_elements[contents_seen].click()

        time.sleep(5)

        # select tab with index 1
        browser.switch_to.window(browser.window_handles[1])

        # click the link which exposes restaurant homepage link (otherwise, by default the homepage
        # link is not visible on the tripadvisor content details page)
        website_link_route = '//div[contains(@class,"restaurants-detail-overview-cards-LocationOverviewCard__detailLink--36TL1 restaurants-detail-overview-cards-LocationOverviewCard__contactItem--3jdfb")]//div[contains(@class,"ui_link")]'
        if len(browser.find_elements(By.XPATH, website_link_route)) != 0:
            browser.find_element(By.XPATH, website_link_route).click()
            time.sleep(2)
            browser.switch_to.window(browser.window_handles[2])
            browser.close()
            browser.switch_to.window(browser.window_handles[1])

        # start mapping data
        restaurant_data = map_source_obj_with_data(browser)

        # start writing data to file
        append_to_file_json('restaurant_data.json', restaurant_data)

        # close browser active tab (tab with particular restaurant data
        browser.close()

        # switch to first window
        browser.switch_to.window(main_window)
        contents_seen += 1

        # wait 60 seconds before opening next content
        time.sleep(60)

    opened_page += 1
    if opened_page <= pages_total:
        # wait 60 before page change
        time.sleep(60)

        # select next page
        browser.find_element(By.XPATH, '//a[@data-page-number="' + opened_page + '"]').click()

        # wait 5 seconds to load the page and restart while cycle
        time.sleep(5)
