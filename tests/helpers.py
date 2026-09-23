import xml.etree.ElementTree as ET

def is_well_formed_xml(xml_string: str) -> bool:
    """Prüft ob der übergebene String ein well formed XML ist

    Args:
        xml_string (str): String, der auf well formedness geprüft werden soll

    Returns:
        bool: Ist der String well formed Ja/Nein?
    """
    try:
        ET.fromstring(xml_string)
        return True
    except ET.ParseError:
        return False
