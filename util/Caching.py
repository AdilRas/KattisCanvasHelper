import pickle
from collections import defaultdict
import logging as log
from typing import Optional, Set


class CacheUtil:
    def __init__(self, cache_folder_path: str):
        self.cache_folder_path = cache_folder_path

    # noinspection PyBroadException
    def load_names_map_from_pickle(self, filename: str) -> Optional[defaultdict[str]]:
        kattis_name_to_canvas_name: Optional[defaultdict[str]] = None
        try:
            with open(f"{self.cache_folder_path}/{filename}", "rb") as file:
                kattis_name_to_canvas_name = pickle.load(file)
                log.info(f"Successfully loaded Kattis->Canvas student name map from cache. "
                         f"Loaded {len(kattis_name_to_canvas_name)} entries.")
                log.info("If you want to clear the cache, delete the items in the 'cache' folder.")
        except FileNotFoundError:
            log.warning("No cache file found for Kattis->Canvas student name mappings. Generating..")
        except pickle.UnpicklingError:
            log.warning("Error reading cache file for Kattis->Canvas student name mappings. Generating..")
        # noinspection PyBroadException
        except:
            log.warning("Unknown error reading Kattis->Canvas student name map cache. Generating..")

        return kattis_name_to_canvas_name

    def update_names_map_to_pickle(self, filename: str, kattis_name_to_canvas_name: defaultdict[str]):
        ans = input("Save matches? [Y/n]")
        if ans.lower() == 'yes' or ans.lower() == 'y' or len(ans.strip()) == 0:
            with open(f"{self.cache_folder_path}/{filename}", "wb+") as file:
                pickle.dump(kattis_name_to_canvas_name, file)
                print(f"Saved selections! ({len(kattis_name_to_canvas_name)} items).")

    def read_honors_skips(self, filename) -> Optional[Set[str]]:
        honors_skips: Optional[Set[str]] = None

        try:
            honors_skips = set()
            with open(f"{self.cache_folder_path}/{filename}", "r") as file:
                for line in file:
                    honors_skips.add(line.lower().strip())
                log.info(f"Successfully loaded honors skips file."
                         f" Loaded {len(honors_skips)} entries.")
        except FileNotFoundError:
            log.error(f"No file found for honors skips... please make one at {self.cache_folder_path}/{filename}")
        except pickle.UnpicklingError:
            log.error(f"Unable to read honors skips file at {self.cache_folder_path}/{filename}.")
        # noinspection PyBroadException
        except Exception as e:
            log.error(f"Unknown error reading honors skips: {e}")

        return honors_skips


