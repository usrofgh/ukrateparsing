import asyncio
from parser_ukr_date import UkrDateParser


async def main():
    ukrdate_parser = UkrDateParser()
    with open("data/profile_links.txt", "r", encoding="UTF-8") as file:
        links = file.read().splitlines()

    info = await ukrdate_parser.start_parsing(links[:10])
    ukrdate_parser.save_profiles_info_to_file(info, path_json="data/delit.json")

if __name__ == '__main__':
    asyncio.run(main())
