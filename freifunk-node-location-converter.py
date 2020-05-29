import json
import requests
import sys
import time
import gzip
import shutil
from typing import Union, Any, TypedDict, Dict

NODE_LOCATION_FILE_URL = "https://api.freifunk.net/data/freifunk-karte-data.json"
TIMEOUT = 5
OUTPUT_FILE = "nodes.json"
LOG_OUTPUT_FILE = "log.txt"


def convert_time(last_modified_str: str) -> int:
    return int(time.mktime(time.strptime(last_modified_str, "%a, %d %b %Y %H:%M:%S %Z")))

class DownloadResult(TypedDict):
    last_modified: int
    json: Any

def download_node_location_file() -> Union[None, DownloadResult]:
    """
    Download the file that contains the node locations
    """
    response = requests.get(NODE_LOCATION_FILE_URL, allow_redirects=True, timeout=TIMEOUT)

    print('Response status code: ' + str(response.status_code))
    if response.status_code != requests.codes.ok:
        return None

    return {
        'last_modified': convert_time(response.headers['Last-Modified']),
        'json': response.json()
    }

class Node(TypedDict):
    online: bool
    lat: float
    lon: float
    name: str

class ConvertedJson(TypedDict):
    timestamp: int
    nodes: Dict[str, Node]

def convert_json(download_result: DownloadResult) -> ConvertedJson:
    """
    Converts the nodes from the freifunk-karte-data.json structure to the structure that is used by the Freifunk Auto
    Connect app
    """
    new_nodes = {}
    for node in download_result['json']['allTheRouters']:
        try:
            new_nodes[node['id']] = {
                'online': (node['status'] == 'online'),
                'lat':    float(node['lat']),
                'lon':    float(node['long']),
                'name':   node['name']
            }
        except ValueError:
            print("Node " + node['id'] + " in community " + node['community'] + " has invalid lat or lon!")
    print(str(len(new_nodes)) + " nodes found.")
    return {
        'nodes': new_nodes,
        'timestamp': download_result['last_modified']
    }


def write_json_to_file(file_path: str, json_data: Any):
    """ Writes json_data as json into the file at file_path """
    with open(file_path, 'w') as outfile:
        json.dump(json_data, outfile)

def gzip_file(file_path: str):
    """ Compresses a file using gzip and saves it at file_path.gz """
    with open(file_path, 'rb') as f_in:
        with gzip.open(file_path + '.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


def main():
    download_result = download_node_location_file()
    if download_result is None:
        sys.exit('Could not download a new version of freifunk-karte-data.json')

    new_json = convert_json(download_result)
    write_json_to_file(OUTPUT_FILE, new_json)
    gzip_file(OUTPUT_FILE)


if __name__ == '__main__':
    main()
