"""Pobieranie z API Sejmu (z ponawianiem) i zapis atomowy plików."""
import json
import logging
import time

import requests

log = logging.getLogger("amc.http")
session = requests.Session()
session.headers["User-Agent"] = "AMC-research (projekt studencki, analiza wypowiedzi)"


def get(url, as_="json", tries=5, timeout=60):
    """GET z ponawianiem i backoffem wykładniczym; błędy 5xx też ponawiamy (API komisji często zwraca 502).

    as_: "json" | "text" | "response". Zwraca None przy 404 albo po wyczerpaniu prób.
    """
    for i in range(tries):
        try:
            r = session.get(url, timeout=timeout)
            if r.status_code == 404:
                return None
            if r.status_code >= 500:
                raise requests.HTTPError(str(r.status_code))
            r.raise_for_status()
            return r.json() if as_ == "json" else r.text if as_ == "text" else r
        except requests.RequestException as e:
            if i == tries - 1:
                log.warning("nie udało się pobrać %s: %s", url, e)
                return None
            time.sleep(2 ** i)


def write_bytes(path, data):
    """Zapis atomowy: przerwane pobranie nie zostawia połówki pliku."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def write_json(path, obj):
    write_bytes(path, json.dumps(obj, ensure_ascii=False).encode("utf-8"))
