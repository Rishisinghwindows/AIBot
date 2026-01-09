"""
Metro API Tool (Placeholder/Demo)

Demo implementation for metro ticket information.
Can be replaced with actual metro API integration.
"""

from typing import Optional
from common.graph.state import ToolResult
from fuzzywuzzy import process

# Demo metro data for Delhi Metro
DELHI_METRO_LINES = {
    "red": [
        "Rithala",
        "Rohini East",
        "Pitampura",
        "Kohat Enclave",
        "Netaji Subhash Place",
        "Shakti Nagar",
        "Kashmere Gate",
    ],
    "yellow": [
        "Samaypur Badli",
        "Rohini Sector 18",
        "Haiderpur Badli Mor",
        "Jahangirpuri",
        "Adarsh Nagar",
        "Azadpur",
        "Model Town",
        "GTB Nagar",
        "Vishwavidyalaya",
        "Vidhan Sabha",
        "Civil Lines",
        "Kashmere Gate",
        "Chandni Chowk",
        "Chawri Bazar",
        "New Delhi",
        "Rajiv Chowk",
        "Patel Chowk",
        "Central Secretariat",
        "Udyog Bhawan",
        "Lok Kalyan Marg",
        "Jor Bagh",
        "INA",
        "AIIMS",
        "Green Park",
        "Hauz Khas",
        "Malviya Nagar",
        "Saket",
        "Qutub Minar",
        "Chhattarpur",
        "Sultanpur",
        "Ghitorni",
        "Arjan Garh",
        "Guru Dronacharya",
        "Sikanderpur",
        "MG Road",
        "IFFCO Chowk",
        "Huda City Centre",
    ],
    "blue": [
        "Dwarka Sector 21",
        "Dwarka Sector 8",
        "Dwarka Sector 9",
        "Dwarka Sector 10",
        "Dwarka Sector 11",
        "Dwarka Sector 12",
        "Dwarka Sector 13",
        "Dwarka Sector 14",
        "Dwarka",
        "Dwarka Mor",
        "Nawada",
        "Uttam Nagar West",
        "Uttam Nagar East",
        "Janakpuri West",
        "Janakpuri East",
        "Tilak Nagar",
        "Subhash Nagar",
        "Tagore Garden",
        "Rajouri Garden",
        "Ramesh Nagar",
        "Moti Nagar",
        "Kirti Nagar",
        "Shadipur",
        "Patel Nagar",
        "Rajendra Place",
        "Karol Bagh",
        "Jhandewalan",
        "Ramakrishna Ashram Marg",
        "Rajiv Chowk",
        "Barakhamba Road",
        "Mandi House",
        "Supreme Court",
        "Indraprastha",
        "Yamuna Bank",
        "Akshardham",
        "Mayur Vihar Phase 1",
        "Mayur Vihar Extension",
        "New Ashok Nagar",
        "Noida Sector 15",
        "Noida Sector 16",
        "Noida Sector 18",
        "Botanical Garden",
        "Golf Course",
        "Noida City Centre",
        "Noida Sector 34",
        "Noida Sector 52",
        "Noida Sector 61",
        "Noida Sector 59",
        "Noida Sector 62",
        "Noida Electronic City",
    ],
    "violet": [
        "Kashmere Gate",
        "Lal Quila",
        "Jama Masjid",
        "Delhi Gate",
        "ITO",
        "Mandi House",
        "Janpath",
        "Central Secretariat",
        "Khan Market",
        "JLN Stadium",
        "Jangpura",
        "Lajpat Nagar",
        "Moolchand",
        "Kailash Colony",
        "Nehru Place",
        "Kalkaji Mandir",
        "Govind Puri",
        "Okhla",
        "Jasola Apollo",
        "Sarita Vihar",
        "Mohan Estate",
        "Tughlakabad",
        "Badarpur Border",
        "Sarai",
        "NHPC Chowk",
        "Mewala Maharajpur",
        "Sector 28",
        "Badkal Mor",
        "Old Faridabad",
        "Neelam Chowk Ajronda",
        "Bata Chowk",
        "Escorts Mujesar",
        "Sant Surdas",
        "Raja Nahar Singh",
    ],
    "green": [
        "Kirti Nagar",
        "Satguru Ram Singh Marg",
        "Ashok Park Main",
        "Punjabi Bagh",
        "Shivaji Park",
        "Madipur",
        "Paschim Vihar East",
        "Paschim Vihar West",
        "Peera Garhi",
        "Udyog Nagar",
        "Maharaja Surajmal Stadium",
        "Nangloi",
        "Nangloi Railway Station",
        "Rajdhani Park",
        "Mundka",
        "Mundka Industrial Area",
        "Ghevra",
        "Tikri Kalan",
        "Tikri Border",
        "Pandit Shree Ram Sharma",
        "Bahadurgarh City",
        "Brigadier Hoshiar Singh",
    ],
    "pink": [
        "Majlis Park",
        "Azadpur",
        "Shalimar Bagh",
        "Netaji Subhash Place",
        "Shakurpur",
        "Punjabi Bagh West",
        "ESI Hospital",
        "Rajouri Garden",
        "Maya Puri",
        "Naraina Vihar",
        "Delhi Cantt",
        "Durgabai Deshmukh South Campus",
        "Sir Vishweshwaraiah Moti Bagh",
        "Bhikaji Cama Place",
        "Sarojini Nagar",
        "INA",
        "South Extension",
        "Lajpat Nagar",
        "Vinobapuri",
        "Ashram",
        "Hazrat Nizamuddin",
        "Mayur Vihar Phase 1",
        "Mayur Vihar Pocket 1",
        "Trilokpuri Sanjay Lake",
        "Vinod Nagar East",
        "Mandawali West Vinod Nagar",
        "IP Extension",
        "Anand Vihar",
        "Karkarduma",
        "Karkarduma Court",
        "Krishna Nagar",
        "East Azad Nagar",
        "Welcome",
        "Jaffrabad",
        "Maujpur Babarpur",
        "Gokulpuri",
        "Johri Enclave",
        "Shiv Vihar",
    ],
    "magenta": [
        "Botanical Garden",
        "Okhla Bird Sanctuary",
        "Kalindi Kunj",
        "Jasola Vihar Shaheen Bagh",
        "Okhla Vihar",
        "Jamia Millia Islamia",
        "Sukhdev Vihar",
        "Okhla NSIC",
        "Kalkaji Mandir",
        "Nehru Enclave",
        "Greater Kailash",
        "Chirag Delhi",
        "Panchsheel Park",
        "Hauz Khas",
        "IIT Delhi",
        "R K Puram",
        "Munirka",
        "Vasant Vihar",
        "Shankar Vihar",
        "Terminal 1 IGI Airport",
        "Sadar Bazaar Cantonment",
        "Palam",
        "Dashrath Puri",
        "Dabri Mor Janakpuri South",
        "Janakpuri West",
    ],
}

# Demo fare structure (in INR)
BASE_FARE = 10
PER_STATION_FARE = 3
MAX_FARE = 60


def _find_station_fuzzy(station_name: str) -> tuple[Optional[str], int]:
    """
    Find a station in any metro line using fuzzy matching.

    Args:
        station_name: Station name to search

    Returns:
        Tuple of (line_name, station_index) or (None, -1) if not found
    """
    station_lower = station_name.strip().lower()
    all_stations = {station: line for line, stations in DELHI_METRO_LINES.items() for station in stations}
    
    best_match = process.extractOne(station_lower, all_stations.keys())
    if best_match and best_match[1] > 80:
        station = best_match[0]
        line_name = all_stations[station]
        return line_name, DELHI_METRO_LINES[line_name].index(station)

    return None, -1


def _find_station(station_name: str) -> tuple[Optional[str], int]:
    """
    Find a station in any metro line.

    Args:
        station_name: Station name to search

    Returns:
        Tuple of (line_name, station_index) or (None, -1) if not found
    """
    return _find_station_fuzzy(station_name)


def get_metro_info(source: str, destination: str) -> ToolResult:
    """
    Get metro route and fare information (demo).

    Args:
        source: Source station name
        destination: Destination station name

    Returns:
        ToolResult with route info or error
    """
    try:
        source_line, source_idx = _find_station(source)
        dest_line, dest_idx = _find_station(destination)

        if source_line is None:
            return ToolResult(
                success=False,
                data=None,
                error=f"Source station '{source}' not found in demo data",
                tool_name="metro_api",
            )

        if dest_line is None:
            return ToolResult(
                success=False,
                data=None,
                error=f"Destination station '{destination}' not found in demo data",
                tool_name="metro_api",
            )

        # Calculate demo metrics
        if source_line == dest_line:
            station_count = abs(dest_idx - source_idx)
            line_info = f"{source_line.capitalize()} Line"
            interchange_required = False
        else:
            # Simplified: assume one interchange at a common station
            station_count = source_idx + dest_idx + 5  # Approximate
            line_info = f"{source_line.capitalize()} Line + {dest_line.capitalize()} Line"
            interchange_required = True

        # Calculate fare
        fare = min(BASE_FARE + (station_count * PER_STATION_FARE), MAX_FARE)
        travel_time = station_count * 3  # ~3 minutes per station

        # Find actual station names from our data
        source_actual = DELHI_METRO_LINES[source_line][source_idx]
        dest_actual = DELHI_METRO_LINES[dest_line][dest_idx]

        return ToolResult(
            success=True,
            data={
                "source": source_actual,
                "destination": dest_actual,
                "line": line_info,
                "station_count": station_count,
                "fare": fare,
                "travel_time": travel_time,
                "interchange_required": interchange_required,
                "note": "Demo data - please verify with official DMRC sources",
            },
            error=None,
            tool_name="metro_api",
        )

    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            error=str(e),
            tool_name="metro_api",
        )


def get_all_metro_lines() -> ToolResult:
    """
    Get all metro lines.

    Returns:
        ToolResult with a list of all metro lines
    """
    return ToolResult(
        success=True,
        data={
            "lines": list(DELHI_METRO_LINES.keys())
        },
        error=None,
        tool_name="metro_api",
    )


def get_metro_stations(line: Optional[str] = None) -> ToolResult:
    """
    Get list of metro stations.

    Args:
        line: Optional line name to filter (red, yellow, blue, etc.)

    Returns:
        ToolResult with station list
    """
    try:
        if line:
            line_lower = line.strip().lower()
            if line_lower in DELHI_METRO_LINES:
                return ToolResult(
                    success=True,
                    data={
                        "line": line_lower.capitalize(),
                        "stations": DELHI_METRO_LINES[line_lower],
                        "station_count": len(DELHI_METRO_LINES[line_lower]),
                    },
                    error=None,
                    tool_name="metro_api",
                )
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Line '{line}' not found. Available: {', '.join(get_all_metro_lines()['data']['lines'])}",
                    tool_name="metro_api",
                )
        else:
            # Return all lines summary
            return ToolResult(
                success=True,
                data={
                    "lines": {
                        name: {
                            "station_count": len(stations),
                            "terminals": [stations[0], stations[-1]],
                        }
                        for name, stations in DELHI_METRO_LINES.items()
                    }
                },
                error=None,
                tool_name="metro_api",
            )

    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            error=str(e),
            tool_name="metro_api",
        )
