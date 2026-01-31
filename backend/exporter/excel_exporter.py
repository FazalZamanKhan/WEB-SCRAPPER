import pandas as pd
from typing import List, Dict, Any

def export_to_excel(data: List[Dict[str, Any]], file_path: str, include_website: bool = True):
    if not data:
        return
    columns = [
        "Business Name",
        "Phone Number",
        "Address",
        "Website" if include_website else None,
        "Rating",
        "Location",
        "Google Maps URL"
    ]
    columns = [col for col in columns if col is not None]
    rows = []
    for item in data:
        row = [
            item.get("name"),
            item.get("phone"),
            item.get("address"),
        ]
        if include_website:
            row.append(item.get("website"))
        row += [
            item.get("rating"),
            item.get("location"),
            item.get("maps_url")
        ]
        rows.append(row)
    df = pd.DataFrame(rows, columns=columns)
    df.to_excel(file_path, index=False)
