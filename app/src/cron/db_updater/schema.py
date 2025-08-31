from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

from pydantic import ConfigDict

class Facility(BaseModel):
    # JSON fields
    id: str                             # same as JSON (used as uuid in DB)
    facility_name: str
    address: Optional[str] = None
    description: Optional[str] = None

    # transformed fields (replacing URLs)
    detail_html: str = ""               # replaces detail_url
    menu_html: Optional[str] = None     # replaces menu_url; may remain None if no menu existed

    @classmethod
    def from_json_item(cls, item: Dict[str, Any]) -> "Facility":
        """Create a Facility from a raw JSON facility item, replacing *_url with *_html."""
        # keep original keys, drop urls, initialize html fields
        detail_html = ""
        menu_html: Optional[str] = None

        if "menu_url" in item:
            menu_html = ""  # we’ll fill later from filesystem

        # Build with the JSON fields we keep + our html fields
        return cls(
            id=item["id"],
            facility_name=item["facility_name"],
            address=item.get("address"),
            description=item.get("description"),
            detail_html=detail_html,
            menu_html=menu_html,
        )


class LocationFacilities(BaseModel):
    location: str
    canteens: List[Facility] = Field(default_factory=list)
    cafeterias: List[Facility] = Field(default_factory=list)

    @classmethod
    def from_json_item(cls, item: Dict[str, Any]) -> "LocationFacilities":
        return cls(
            location=item["location"],
            canteens=[Facility.from_json_item(x) for x in item.get("canteens", [])],
            cafeterias=[Facility.from_json_item(x) for x in item.get("cafeterias", [])],
        )


class OrganizationBlock(BaseModel):
    organization_name: str
    organization_domain: str
    facilities: List[LocationFacilities] = Field(default_factory=list)

    @classmethod
    def from_json_item(cls, item: Dict[str, Any]) -> "OrganizationBlock":
        return cls(
            organization_name=item["organization_name"],
            organization_domain=item["organization_domain"],
            facilities=[LocationFacilities.from_json_item(x) for x in item.get("facilities", [])],
        )


# Optional convenience wrapper if you like a single root object
class FacilitiesRoot(BaseModel):
    organizations: List[OrganizationBlock]

    @classmethod
    def from_json(cls, data: List[Dict[str, Any]]) -> "FacilitiesRoot":
        return cls(organizations=[OrganizationBlock.from_json_item(x) for x in data])

    # handy lookups
    def by_id(self, uuid: str) -> Optional[Facility]:
        for org in self.organizations:
            for loc in org.facilities:
                for f in (*loc.canteens, *loc.cafeterias):
                    if f.id == uuid:
                        return f
        return None

    def all_facilities(self) -> List[Facility]:
        out: List[Facility] = []
        for org in self.organizations:
            for loc in org.facilities:
                out.extend(loc.canteens)
                out.extend(loc.cafeterias)
        return out
