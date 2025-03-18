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

    @property
    def unique_hash(self) -> str:
        unique_str = f"{self.title}{self.price}{self.location}"
        return hashlib.md5(unique_str.encode()).hexdigest()
