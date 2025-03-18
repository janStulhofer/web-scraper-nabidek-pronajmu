import os

from scrapers.rental_offer import RentalOffer


class OffersStorage:
    """Úložiště dříve nalezených nabídek"""

    def __init__(self, path: str):
        self.path = path
        self.first_time = False
        self._hashes: set[str] = set()  
        try:
            with open(self.path) as file:
                for line in file:
                    self._hashes.add(line.strip())
        except FileNotFoundError:
            self.first_time = True

    def contains(self, offer: RentalOffer) -> bool:
        # Generujeme hash z titulku, ceny a lokace
        unique_str = f"{offer.title}{offer.price}{offer.location}"
        offer_hash = hashlib.md5(unique_str.encode()).hexdigest()
        return offer_hash in self._hashes

    def save_offers(self, offers: list[RentalOffer]):
        with open(self.path, 'a+') as file_object:
            for offer in offers:
                unique_str = f"{offer.title}{offer.price}{offer.location}"
                offer_hash = hashlib.md5(unique_str.encode()).hexdigest()
                self._hashes.add(offer_hash)
                file_object.write(offer_hash + os.linesep)

        self.first_time = False

        
        """Cesta k uloženým odkazům"""

        self.first_time = False
        """Neproběhl pokus o uložení nabídek (soubor neexistuje)"""

        self._links: set[str] = set()
        """Seznam URL odkazů na všechny nalezené nabídky"""

        try:
            with open(self.path) as file:
                for line in file:
                    self._links.add(line.strip())
        except FileNotFoundError:
            self.first_time = True


    def contains(self, offer: RentalOffer) -> bool:
        """Objevila se nabídka již dříve?

        Args:
            offer (RentalOffer): Nabídka

        Returns:
            bool: Jde o starou nabídku
        """
        return offer.link in self._links


    def save_offers(self, offers: list[RentalOffer]):
        """Uložit nabídky jako nalezené

        Args:
            offers (list[RentalOffer]): Nalezené nabídky
        """
        with open(self.path, 'a+') as file_object:
            for offer in offers:
                self._links.add(offer.link)
                file_object.write(offer.link + os.linesep)

            self.first_time = False
