import os
import hashlib
from scrapers.rental_offer import RentalOffer

class OffersStorage:
    def __init__(self, path: str):
        self.path = path
        self.first_time = False
        self._hashes: set[str] = set()  # Ukládáme pouze hashe

        try:
            with open(self.path) as file:
                for line in file:
                    self._hashes.add(line.strip())
        except FileNotFoundError:
            self.first_time = True

    def contains(self, offer: RentalOffer) -> bool:
        # Kontrola pomocí hashe
        return offer.unique_hash in self._hashes

    def save_offers(self, offers: list[RentalOffer]):
        with open(self.path, 'a+') as file_object:
            for offer in offers:
                offer_hash = offer.unique_hash
                if offer_hash not in self._hashes:
                    self._hashes.add(offer_hash)
                    file_object.write(offer_hash + os.linesep)

        self.first_time = False
