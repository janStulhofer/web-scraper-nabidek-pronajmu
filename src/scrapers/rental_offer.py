from dataclasses import dataclass
import hashlib

@dataclass
class RentalOffer:
    """Nabídka pronájmu bytu"""

    link: str
    title: str
    location: str
    price: int | str
    image_url: str
    scraper: 'ScraperBase'

    @property  # Správně odsazeno (4 mezery/tab pod třídou)
    def unique_hash(self) -> str:
        """Unikátní identifikátor kombinující titul, cenu a lokaci"""
        unique_str = f"{self.title}{self.price}{self.location}"
        return hashlib.md5(unique_str.encode()).hexdigest()
