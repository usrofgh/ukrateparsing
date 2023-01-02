import itertools
from dotenv import load_dotenv
import os

load_dotenv(".env")
LOGIN_PROXY = os.environ.get("LOGIN_PROXY")
PASSWORD_PROXY = os.environ.get("PASSWORD_PROXY")

proxy = [
    {"https://": f"http://{LOGIN_PROXY}:{PASSWORD_PROXY}@131.108.17.20:9713"},
    {"https://": f"http://{LOGIN_PROXY}:{PASSWORD_PROXY}@131.108.17.115:9579"},
    {"https://": f"http://{LOGIN_PROXY}:{PASSWORD_PROXY}@138.59.207.11:9218"},
]

iter_proxy = itertools.cycle(iter(proxy))


headers = {

}