import os
import json
import asyncio
import httpx


from bs4 import BeautifulSoup
from urllib.parse import urljoin
from httpx import Timeout

from proxy import iter_proxy


class UkrDateParser:
    __BASE_URL = "https://ukrdate.net/"
    __n_page_processed = 0
    __translation = {
        "Рост": "height",
        "Семейное положение": "status",
        "Вес": "weight",
        "Я выгляжу": "i_look",
        "Телосложение": "physique",
        "Цвет кожи": "skin_color",
        "Цвет глаз": "eyes_color",
        "Длина волос": "hair_length",
        "Тип волос": "hair_type",
        "Цвет волос": "hair_color",
        "На теле есть": "pirsing_or_tatoo",
        "Национальность": "nation",
        "Вероисповедание": "faith",
        "Политические взгляды": "political_opinion",
        "Служба в армии": "army",
        "Режим дня": "chronotype",
        "Отношение к курению": "smoking_attitude",
        "Отношение к алкоголю": "alcohol_attitude",
        "Отношение к религии": "religion_attitude",
        "Любимый алкогольный напиток": "favorite_alco_drink",
        "Тип питания": "food_type",
        "Любимый стиль музыки": "favorite_music_style",
        "Интересы": "interests",
        "Личные качества": "personal_qualities",
        "Знание языков": "languages",
        "Вакцинация от коронавируса": "is_corono_vaccine",
        "Домашнее животное": "pets",
        "Веб камера": "web_camera",
        "Водительские права на машину": "drive_licence",
        "Личный транспорт": "transport",
        "Производитель": "vendor",
        "Модель": "model",
        "Пол": "gender",
        "Дата рождения": "birthday",
        "Имя": "name",
        "Место жительства": "living",
        "Наличие детей": "children",
        "Этнический тип": "ethnic_type",
        "Страна рождения": "birth_country",
        "Образование": "education",
        "Специализация": "specialisation",
        "Материальное положение": "material_status",
        "Проживание": "apart_status",
        "Проживание детей": "children_living",
    }

    @staticmethod
    def __create_data_dir() -> None:
        if os.path.exists("data") is False:
            os.mkdir("data")

    @staticmethod
    def save_profiles_info_to_file(
            profiles: [dict],
            path_json: str = None,
    ) -> None:

        if path_json is not None:
            with open(path_json, "w", encoding="utf-8") as json_file:
                json.dump(profiles, json_file, indent=4, ensure_ascii=False)

    def __get_base_url(self) -> str:
        return self.__BASE_URL

    def __parse_count_pages(self) -> None:
        filters = "?action=search&op=s&genre=1&look_genre=2&geo_select=0&age_from=18&age_to=90"
        n_page = "600"
        url_n_page = urljoin(self.__BASE_URL, n_page)
        r = httpx.get(url_n_page)  # TODO: add headers with cookies
        page_soup = BeautifulSoup(r.content, "html.parser")
        count_pages = int(page_soup.select(".resultPpaddingItem a")[-1]["href"].rsplit("=")[-1])
        self.__count_pages: int = count_pages

    def __generate_pagination_links(self) -> None:
        self.__pagination_links = [self.__BASE_URL + f"&page={i}"
                                   for i in range(1, self.__count_pages + 1)]

    def __parse_profiles_links(self) -> None:
        self.__profiles_links = []
        for link in self.__pagination_links:
            r = httpx.get(link)  # TODO: add proxy nd headers
            page_soup = BeautifulSoup(r.content, "html.parser")
            profile_links = [urljoin(self.__BASE_URL, link["href"])
                             for link in page_soup.select(".mainUsersPic > a")]
            self.__profiles_links.extend(profile_links)

    async def __parse_all_profiles_info(self) -> None:
        client = httpx.AsyncClient()  # TODO: add timeout 20
        res = await asyncio.gather(
            *[self.__parse_single_profile_info(profile_link, client)
              for profile_link in self.__profiles_links]
        )
        await client.aclose()
        self.__profiles_info = res

    @staticmethod
    def __parse_last_activity(page_soup: BeautifulSoup) -> dict:
        try:
            last_activity = {page_soup.select_one(".view__profile__userinfo__online").text.strip()}
        except AttributeError:
            last_activity = None

        return {"last_activity": last_activity}

    @classmethod
    def __parse_about_me(cls, title_of_block) -> dict:
        return {"about_me": " ".join(title_of_block.next_sibling.next_sibling.text.split()).strip()}

    @staticmethod
    def __parse_common_info(page_soup: BeautifulSoup) -> dict:

        return {
            "profile_id": page_soup.select("#USER_PAGE_ADDRESS #member_id td")[-1].text,
            "first_name": page_soup.select_one(".view__profile__userinfo__name").text[:-1].strip(),
            "age": int(page_soup.select_one(".view__profile__userinfo__age").text.strip()),
            "zodiac": page_soup.select_one(".view__profile__userinfo__zodiac").text.strip(),
            "city": page_soup.select_one(".view__profile__userinfo__region").text.split(", ")[0],
            "country": page_soup.select_one(".view__profile__userinfo__region").text.split(", ")[1],
        }

    def __get_profile_images(self, page_soup: BeautifulSoup) -> dict:
        images = [urljoin(self.__BASE_URL, link["src"].replace("tb_", ""))
                  for link in page_soup.select(".view__profile__photo__img > img")]

        if images[0].rsplit("/")[-1] == "1.gif":
            return {"images": None}
        return {"images": images}

    @staticmethod
    def __look_for_age_range(page_soup: BeautifulSoup) -> {str: str}:
        block_info = page_soup.select_one(".profile_about_anketa_block samp").next_sibling.text
        look_age_from = " ".join(block_info.split()).split(" - ")[0].rsplit()[-1]
        look_age_to = " ".join(block_info.split()).split(" - ")[1].rsplit()[0]

        return {
            "look_age_from": look_age_from,
            "look_age_to": look_age_to,
        }

    @staticmethod
    def __meeting_aim(page_soup: BeautifulSoup) -> dict:
        blocks_info = page_soup.select(".profile_about_anketa_block samp")
        return {"meeting_aims": str(blocks_info[1].next_sibling).replace("\n", "").strip().split(", ")}

    @staticmethod
    def __looking_for(page_soup: BeautifulSoup) -> dict:
        gender = " ".join(page_soup.select_one(".profile_about_anketa_block samp").
                          next_sibling.text.
                          split()).split(" в", 1)[0].split()[1]
        if gender == "женщиной":
            return {"looking_gender": "female"}
        elif gender == "мужчиной":
            return {"looking_gender": "male"}

    @staticmethod
    def __looking_in(page_soup: BeautifulSoup) -> dict:
        cleaned = " ".join(page_soup.select_one(".profile_about_anketa_block samp").next_sibling.text.split())
        if "в районе " not in cleaned:
            country = cleaned.rsplit("в ")[-1]
            area = None
        else:
            area, country = cleaned.rsplit("в районе ")[-1].split(", ")

        return {
            "country": country,
            "area": area,
        }

    def __parse_personal_data(self, personal_data_block) -> dict:
        personal_data = [el.strip()
                         for el in " ".join(personal_data_block.next_sibling.text.strip().
                                            replace("\n\n", "\n").
                                            replace(":\n  ", ":").
                                            replace("\t", "").
                                            replace("я:  \n", "я:").
                                            replace("\n", ",").split()).split(",")
                         if el != " "]

        personal_data_dict = {}
        for el in personal_data:
            k, v = el.split(": ")
            personal_data_dict[self.__translation[k]] = v

        return personal_data_dict

    def __parse_appearance(self, appearance_block) -> dict:
        appearance = [el.strip().replace(";", ",")
                      for el in " ".join(appearance_block.next_sibling.text.strip().
                                         replace("кг", "").
                                         replace("см", "").
                                         replace("\xa0", "").
                                         replace(":\n ", ":").
                                         replace(",", ";").
                                         replace("\n", ",").split()).split(",")
                      if len(el.strip()) > 0]
        appearance_dict = {}
        for el in appearance:
            k, v = el.split(": ")
            appearance_dict[self.__translation[k]] = v

        return appearance_dict

    count = 0

    def __parse_travels_places(self, travels_block) -> dict:
        places = [item.strip()
                  for item in
                  " ".join(travels_block.next_sibling.next_sibling.
                           text.replace("\n", ",").split()).
                  split(", ")
                  if "," not in item and
                  len(item.strip()) != 0]

        return {"visited_places": ", ".join(places)}

    def __parse_habits(self, habits_block) -> dict:
        habits = [el.strip()
                  for el in
                  " ".join(habits_block.next_sibling.text.strip().replace(":\n ", ":").
                           replace("\t", "").replace("\n", ",").split()).split(",")]
        habits_dict = {}
        for el in habits:
            k, v = el.split(": ")
            habits_dict[self.__translation[k]] = v.replace('"', "")
        return habits_dict

    def __parse_country_and_religion(self, country_and_religion_block) -> dict:
        country_and_religion = [el.strip() for el in
                                " ".join(country_and_religion_block.
                                         next_sibling.text.strip().
                                         replace("\n\n", "\n").
                                         replace(":\n", ":").
                                         replace("\t", "").
                                         replace("\n", ",").split()).
                                split(",")
                                if len(el.strip()) != 0]
        country_and_religion_dict = {}
        for el in country_and_religion:
            k, v = el.split(": ")
            try:
                country_and_religion_dict[self.__translation[k]] = v
            except KeyError:
                pass
        return country_and_religion_dict

    def __parse_character_hobbies(self, character_hobbies_block) -> dict:
        get_character_hobbies = [el.replace(":\xa0", ":").
                                 replace('<div class="profile_about_anketa_block">', "")
                                 for el in str(character_hobbies_block.next_sibling).split("<br/>")
                                 if el != '</div>']
        get_character_hobbies_dict = {self.__translation[el.split(":")[0]]: el.split(":")[1].replace(" /", ",")
                                      for el in get_character_hobbies}

        return get_character_hobbies_dict

    def __parse_additional_data(self, additional_data_block) -> dict:
        additional_data = [" ".join(item.
                                    replace('<div class="profile_about_anketa_block">', "").
                                    replace("\xa0", "").split()).
                           replace("</div>", "").
                           replace(": ", ":").strip()
                           for item in str(additional_data_block.next_sibling).split("<br/>")]
        additional_data_dict = {}
        for el in additional_data:
            k, v = el.split(":")
            additional_data_dict[self.__translation[k]] = v
        return additional_data_dict

    @staticmethod
    def __parse_verif_info(page_soup: BeautifulSoup) -> str:
        return ", ".join([verif.text.strip().split(" ")[0] for verif in page_soup.select(".face_table td")
                          if "Анкета подтверждена" not in verif.text])

    async def parse_single_profile_info(self, profile_link: str, client: httpx.AsyncClient):  # TODO: none
        __all_block_titles = {
                              'Личные данные': self.__parse_personal_data,
                              'Внешний вид': self.__parse_appearance,
                              'Характер и увлечения': self.__parse_character_hobbies,
                              'Привычки': self.__parse_habits,
                              'Страна и религия': self.__parse_country_and_religion,
                              'Дополнительные данные': self.__parse_additional_data,
                              'Путешествия': self.__parse_travels_places,
                              'О себе': self.__parse_about_me,
        }

        r = await client.get(profile_link)
        page_soup = BeautifulSoup(r.content, "html.parser")

        try:
            not_found_alert = page_soup.select_one("#mainTableRightTd h1").text
            print(r.status_code, r.url, end=" ")
            print("page not found")
            return {}
        except AttributeError:
            pass

        self.__n_page_processed += 1
        print(r.status_code, r.url, end=" ")
        print(f"[+] request to a profile. Done {self.__n_page_processed}")

        titles_tag = [item for item in page_soup.select("#mainTableRightTd > h2")]
        titles_text = [el.text for el in titles_tag]
        res = {}
        res.update(self.__parse_common_info(page_soup))
        for block_title, v_func in __all_block_titles.items():
            if bool(set(titles_text).intersection([block_title])) is False:
                continue
            tag_index = titles_text.index(block_title)
            block = v_func(titles_tag[tag_index])
            res.update(block)

        res.update(self.__get_profile_images(page_soup))
        res.update({"verif_info": self.__parse_verif_info(page_soup)})
        res.update({"account_link": str(r.url)})
        return res

    async def start_parsing(self, profiles_links: [str]):
        client = httpx.AsyncClient(timeout=Timeout(20), proxies=next(iter_proxy))
        res = await asyncio.gather(
            *[self.parse_single_profile_info(profile_link, client)
              for profile_link in profiles_links]
        )
        await client.aclose()
        return res
