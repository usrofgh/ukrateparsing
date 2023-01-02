import json
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By

any_country = f"https://ukrdate.net/?action=search&op=s&pt=&genre=1&look_genre=2&age_from=18&age_to=90&geo_select="


def get_data(driver: WebDriver):
    return driver.find_element(By.ID, "geo_options").find_elements(By.TAG_NAME, "option")[1::]


def change_region(driver: WebDriver):
    driver.find_element(By.CSS_SELECTOR, "[title=\"сменить регион\"]").click()


def change_country(driver: WebDriver):
    driver.find_element(By.CSS_SELECTOR, "[title=\"сменить страну\"]").click()
    driver.implicitly_wait(3)


if __name__ == '__main__':
    driver = webdriver.Chrome()
    driver.get(any_country + "0")
    driver.implicitly_wait(5)

    driver.find_element(By.ID, "mainTableRightTd").find_element(By.ID, "geo_select").click()
    driver.find_element(By.ID, "mainTableRightTd").find_element(By.ID, "geo_select").\
        find_elements(By.TAG_NAME, "option")[-1].click()
    driver.implicitly_wait(3)

    change_region(driver)
    change_country(driver)

    places_data = dict()
    places_data["countries"] = {i.text: i.get_attribute("value") for i in get_data(driver)}
    # for name_country, id_country in places_data["countries"].items():
    name_country = "Украина"
    id_country = places_data["countries"][name_country]
    driver.find_element(By.XPATH, f"//option[text()='{' '.join(name_country.split())}']").click()
    driver.implicitly_wait(3)

    places_data["countries"][name_country] = {
        id_country: {region.text: region.get_attribute("value") for region in get_data(driver)}
    }

    for name_region, id_region in places_data["countries"][name_country][id_country].items():
        try:
            driver.find_element(By.XPATH, f"//option[text()='{name_region}']").click()
        except NoSuchElementException:
            driver.find_element(By.XPATH, f"//option[text()='{name_region.replace(' ', ' ' * 2)}']").click()
        driver.implicitly_wait(3)

        places_data["countries"][name_country][id_country][name_region] = {
            id_region: {city.text: city.get_attribute("value") for city in get_data(driver)}
        }
        change_region(driver)
    change_country(driver)

    with open("countries_codes/ukraine.json", "w", encoding="utf-8") as json_file:
        json.dump(places_data["countries"]["Украина"], json_file, indent=4, ensure_ascii=False)
