"""
Train Status Scraper - Enhanced Version

Scrapes detailed train running status with:
- Current station and platform
- Distance traveled
- All upcoming stations with ETAs
- Delay information

Sources:
1. etrain.info - detailed station-wise data
2. runningstatus.in - fallback
"""

import httpx
import re
import logging
from typing import Dict, Optional, List
from datetime import datetime

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

logger = logging.getLogger(__name__)


async def scrape_train_status_detailed(train_number: str) -> Dict:
    """
    Scrape detailed train running status from etrain.info

    Args:
        train_number: 5-digit train number

    Returns:
        Dict with detailed train status data
    """
    if not BS4_AVAILABLE:
        return {
            "success": False,
            "error": "BeautifulSoup not installed. Run: pip install beautifulsoup4",
            "data": None
        }

    url = f"https://etrain.info/train/{train_number}/running-status"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
    }

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)

            if response.status_code != 200:
                logger.warning(f"etrain.info returned {response.status_code}, trying fallback")
                return await scrape_train_status(train_number)

            soup = BeautifulSoup(response.text, 'html.parser')

            # Get train name from title
            title = soup.find('title')
            train_name = "Unknown Train"
            if title:
                title_text = title.text.strip()
                # Extract train name from title
                name_match = re.search(r'(.+?)\s*\(' + train_number, title_text)
                if name_match:
                    train_name = name_match.group(1).strip()
                elif train_number in title_text:
                    train_name = title_text.split(' Running')[0].strip()

            # Try to find running status info
            status_info = {}
            delay_minutes = 0
            running_status = "Unknown"

            # Look for delay/status info
            delay_elem = soup.find(text=re.compile(r'(\d+)\s*(?:min|minute)', re.I))
            if delay_elem:
                delay_match = re.search(r'(\d+)\s*(?:min|minute)', delay_elem, re.I)
                if delay_match:
                    delay_minutes = int(delay_match.group(1))

            # Check for "on time" or "late" text
            status_text = soup.get_text()
            if re.search(r'on\s*time', status_text, re.I):
                running_status = "समय पर" if delay_minutes == 0 else f"{delay_minutes} मिनट की देरी"
            elif re.search(r'(\d+)\s*(?:min|minute).*late', status_text, re.I):
                running_status = f"{delay_minutes} मिनट की देरी"
            elif delay_minutes > 0:
                running_status = f"{delay_minutes} मिनट की देरी"
            else:
                running_status = "समय पर"

            # Find station table
            stations = []
            current_station = None
            current_station_code = ""
            current_platform = ""
            next_stations = []

            # Look for tables with station data
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 2:
                        station_text = cols[0].get_text(strip=True)
                        # Skip header rows
                        if 'Station' in station_text or 'station' in station_text:
                            continue

                        # Extract station code
                        code_match = re.search(r'\(([A-Z]{2,5})\)', station_text)
                        station_code = code_match.group(1) if code_match else ""
                        station_name = re.sub(r'\([A-Z]{2,5}\)', '', station_text).strip()

                        # Get timing info
                        arrival = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                        departure = cols[2].get_text(strip=True) if len(cols) > 2 else arrival
                        platform = cols[3].get_text(strip=True) if len(cols) > 3 else ""

                        # Clean platform text
                        platform = re.sub(r'[^\d]', '', platform)

                        station_info = {
                            "name": station_name,
                            "code": station_code,
                            "arrival": arrival,
                            "departure": departure,
                            "platform": platform
                        }

                        # Check if this station has been passed (look for actual times)
                        if re.search(r'\d{1,2}:\d{2}.*\d{1,2}:\d{2}', arrival):
                            current_station = station_info
                        else:
                            next_stations.append(station_info)

            # If no current station found from table, try to find from text
            if not current_station:
                current_match = re.search(r'(?:at|reached|departed)\s+([A-Za-z\s]+)\s*(?:\(([A-Z]{2,5})\))?', status_text, re.I)
                if current_match:
                    current_station = {
                        "name": current_match.group(1).strip(),
                        "code": current_match.group(2) if current_match.group(2) else "",
                        "arrival": "",
                        "departure": "",
                        "platform": ""
                    }

            # Get source and destination
            source = ""
            destination = ""
            route_match = re.search(r'from\s+([A-Za-z\s]+)\s+to\s+([A-Za-z\s]+)', status_text, re.I)
            if route_match:
                source = route_match.group(1).strip()
                destination = route_match.group(2).strip()

            # Try to get distance info
            distance_traveled = 0
            total_distance = 0
            dist_match = re.search(r'(\d+)\s*/\s*(\d+)\s*km', status_text, re.I)
            if dist_match:
                distance_traveled = int(dist_match.group(1))
                total_distance = int(dist_match.group(2))

            # Get scheduled departure
            scheduled_departure = ""
            sched_match = re.search(r'(?:scheduled|departs?)\s+(?:at\s+)?(\d{1,2}:\d{2})', status_text, re.I)
            if sched_match:
                scheduled_departure = sched_match.group(1)

            # Build result
            result_data = {
                "train_number": train_number,
                "train_name": train_name,
                "running_status": running_status,
                "delay_minutes": delay_minutes,
                "source": source,
                "destination": destination,
                "travel_date": datetime.now().strftime("%Y-%m-%d"),
                "scheduled_departure": scheduled_departure,
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S +0530"),
                "current_station": current_station.get("name", "N/A") if current_station else "N/A",
                "current_station_code": current_station.get("code", "") if current_station else "",
                "current_platform": current_station.get("platform", "अज्ञात") if current_station else "अज्ञात",
                "current_arrival": current_station.get("arrival", "") if current_station else "",
                "current_departure": current_station.get("departure", "") if current_station else "",
                "distance_traveled": distance_traveled,
                "total_distance": total_distance,
                "next_stations": next_stations[:6],  # First 6 upcoming stations
                "data_source": "etrain.info",
                "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
            }

            # If we got minimal data, try fallback
            if not current_station and not next_stations:
                logger.info("Minimal data from etrain.info, trying fallback scraper")
                fallback = await scrape_train_status(train_number)
                if fallback["success"]:
                    # Merge data
                    fb_data = fallback["data"]
                    result_data["current_station"] = fb_data.get("last_station", result_data["current_station"])
                    result_data["running_status"] = fb_data.get("running_status", result_data["running_status"])
                    result_data["delay_minutes"] = fb_data.get("delay_minutes", result_data["delay_minutes"])
                    if fb_data.get("stations"):
                        result_data["next_stations"] = fb_data["stations"][:6]

            return {
                "success": True,
                "error": None,
                "data": result_data
            }

    except httpx.TimeoutException:
        logger.warning("etrain.info timeout, trying fallback")
        return await scrape_train_status(train_number)
    except Exception as e:
        logger.error(f"etrain.info scraper error: {e}", exc_info=True)
        return await scrape_train_status(train_number)


async def scrape_train_status(train_number: str) -> Dict:
    """
    Scrape train running status from runningstatus.in (fallback)

    Args:
        train_number: 5-digit train number

    Returns:
        Dict with train status data or error
    """
    if not BS4_AVAILABLE:
        return {
            "success": False,
            "error": "BeautifulSoup not installed. Run: pip install beautifulsoup4",
            "data": None
        }

    url = f"https://www.runningstatus.in/status/{train_number}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Website returned status {response.status_code}",
                    "data": None
                }

            soup = BeautifulSoup(response.text, 'html.parser')

            # Get train name from title
            title = soup.find('title')
            train_name = "Unknown Train"
            if title:
                title_text = title.text.strip()
                if '/' in title_text:
                    train_name = title_text.split('/')[0].strip()
                elif train_number in title_text:
                    train_name = title_text.split(train_number)[0].strip()

            # Find the station table
            table = soup.find('table')
            stations = []
            last_station = None
            next_station = None
            delay_minutes = 0
            running_status = "Unknown"

            if table:
                rows = table.find_all('tr')

                for row in rows[2:]:  # Skip header rows
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 3:
                        station_cell = cols[0].get_text(strip=True)
                        arrival_cell = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                        departure_cell = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                        platform = cols[3].get_text(strip=True) if len(cols) > 3 else ""

                        # Extract station name and code
                        station_name = re.sub(r'\d+\s*Km/Hr', '', station_cell).strip()
                        code_match = re.search(r'\(([A-Z]{2,5})\)', station_name)
                        station_code = code_match.group(1) if code_match else ""
                        station_name = re.sub(r'\([A-Z]{2,5}\)', '', station_name).strip()

                        # Check if station has been passed
                        has_actual_time = re.search(r'\d{1,2}:\d{2}[AP]M\s*/\s*\d{1,2}:\d{2}[AP]M', arrival_cell)

                        # Extract delay
                        delay_match = re.search(r'(\d+)M\s*Late', arrival_cell + " " + departure_cell, re.I)
                        early_match = re.search(r'(\d+)M\s*Early', arrival_cell + " " + departure_cell, re.I)

                        station_delay = 0
                        if delay_match:
                            station_delay = int(delay_match.group(1))
                        elif early_match:
                            station_delay = -int(early_match.group(1))

                        # Extract times
                        arr_time = ""
                        dep_time = ""
                        arr_match = re.search(r'(\d{1,2}:\d{2}[AP]M)', arrival_cell)
                        dep_match = re.search(r'(\d{1,2}:\d{2}[AP]M)', departure_cell)
                        if arr_match:
                            arr_time = arr_match.group(1)
                        if dep_match:
                            dep_time = dep_match.group(1)

                        station_info = {
                            "name": station_name,
                            "code": station_code,
                            "arrival": arr_time,
                            "departure": dep_time,
                            "platform": platform.replace("PF:", "").strip() if platform else "",
                            "passed": has_actual_time is not None,
                            "delay": station_delay
                        }

                        stations.append(station_info)

                        if station_info["passed"]:
                            last_station = station_info
                            delay_minutes = station_delay
                        elif next_station is None and not station_info["passed"]:
                            next_station = station_info

            # Determine running status
            if delay_minutes == 0:
                running_status = "समय पर"
            elif delay_minutes > 0:
                running_status = f"{delay_minutes} मिनट की देरी"
            else:
                running_status = f"{abs(delay_minutes)} मिनट पहले"

            # Extract last station time
            last_station_time = ""
            if last_station:
                time_match = re.search(r'/\s*(\d{1,2}:\d{2}[AP]M)', last_station.get("arrival", ""))
                if time_match:
                    last_station_time = time_match.group(1)

            # Extract ETA for next station
            eta_next = ""
            if next_station:
                eta_match = re.search(r'^(\d{1,2}:\d{2}[AP]M)', next_station.get("arrival", ""))
                if eta_match:
                    eta_next = eta_match.group(1)

            # Get source and destination
            valid_stations = [s for s in stations if s["name"] and "Station" not in s["name"] and "Speed" not in s["name"]]
            source = valid_stations[0]["name"] if valid_stations else ""
            destination = valid_stations[-1]["name"] if valid_stations else ""

            # Filter next stations (stations not yet passed)
            next_stations = [s for s in valid_stations if not s["passed"]][:6]

            return {
                "success": True,
                "error": None,
                "data": {
                    "train_number": train_number,
                    "train_name": train_name,
                    "running_status": running_status,
                    "delay_minutes": delay_minutes,
                    "source": source,
                    "destination": destination,
                    "travel_date": datetime.now().strftime("%Y-%m-%d"),
                    "scheduled_departure": "",
                    "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S +0530"),
                    "current_station": last_station["name"] if last_station else "N/A",
                    "current_station_code": last_station.get("code", "") if last_station else "",
                    "current_platform": last_station.get("platform", "अज्ञात") if last_station else "अज्ञात",
                    "current_arrival": last_station.get("arrival", "") if last_station else "",
                    "current_departure": last_station.get("departure", "") if last_station else "",
                    "distance_traveled": 0,
                    "total_distance": 0,
                    "next_station": next_station["name"] if next_station else "N/A",
                    "eta_next_station": eta_next,
                    "next_stations": next_stations,
                    "stations": valid_stations[:10],
                    "data_source": "runningstatus.in",
                    "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
                }
            }

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "Request timed out. Please try again.",
            "data": None
        }
    except Exception as e:
        logger.error(f"Train scraper error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to fetch train status: {str(e)}",
            "data": None
        }


def scrape_train_status_sync(train_number: str) -> Dict:
    """Synchronous version of scrape_train_status."""
    import asyncio
    return asyncio.run(scrape_train_status(train_number))


# Test function
if __name__ == "__main__":
    import asyncio

    async def test():
        result = await scrape_train_status_detailed("12565")
        print(f"Success: {result['success']}")
        if result['success']:
            data = result['data']
            print(f"Train: {data['train_name']} ({data['train_number']})")
            print(f"Status: {data['running_status']}")
            print(f"Delay: {data['delay_minutes']} min")
            print(f"Current: {data['current_station']} ({data['current_station_code']})")
            print(f"Platform: {data['current_platform']}")
            print(f"\nNext Stations:")
            for st in data.get('next_stations', [])[:5]:
                print(f"  - {st['name']} ({st.get('code', '')}) Arr: {st.get('arrival', '-')} Dep: {st.get('departure', '-')} PF: {st.get('platform', '-')}")
        else:
            print(f"Error: {result['error']}")

    asyncio.run(test())
