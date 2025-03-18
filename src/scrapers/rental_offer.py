from dataclasses import dataclass
import hashlib

@dataclass
class RentalOffer:
    """Nabídka pronájmu bytu"""

    link: str
    """URL adresa na nabídku"""

    title: str
    """Popis nabídky (nejčastěji počet pokojů, výměra)"""

    location: str
    """Lokace bytu (městská část, ulice)"""

    price: int | str
    """Cena pronájmu za měsíc bez poplatků a energií"""

    image_url: str
    """Náhledový obrázek nabídky"""

    scraper: 'ScraperBase'
    """Odkaz na instanci srapera, ze kterého tato nabídka pochází"""
    
@property
    def unique_hash(self) -> str:
        """Unikátní identifikátor kombinující titul, cenu a lokaci"""
        unique_str = f"{self.title}{self.price}{self.location}"
        return hashlib.md5(unique_str.encode()).hexdigest()
