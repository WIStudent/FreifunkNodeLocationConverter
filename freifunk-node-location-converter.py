import json
import requests
import sys
import time
import gzip
import shutil

from Logger import Logger

NODE_LOCATION_FILE_URL = "https://api.freifunk.net/data/freifunk-karte-data.json"
TIMEOUT = 5
OUTPUT_FILE = "nodes.json"
LOG_OUTPUT_FILE = "log.txt"
IF_MODIFIED_SINCE_FILE = "if-modified-since.txt"


def download_node_location_file(logger):
    """
    Download the file that contains the node locations

    :param logger: Logger object that is used for logging
    :return: The json structure or None if the file could not be downloaded
    """
    headers = {}
    # Get the timestamp the json file was last downloaded and use it for the 'If-Modified-Since' flag in the http
    # request
    try:
        with open(IF_MODIFIED_SINCE_FILE) as f:
            headers['If-Modified-Since'] = f.read()
    except IOError:
        logger.log(IF_MODIFIED_SINCE_FILE + ' file does not exist')
    logger.log('Request header: ' + str(headers))

    # Send the http request
    response = requests.get(NODE_LOCATION_FILE_URL, allow_redirects=True, timeout=TIMEOUT, headers=headers)

    # Check the response code. If it was 200, save the 'Last-Modified' date and return the downloaded json object.
    logger.log('Response status code: ' + str(response.status_code))
    if response.status_code == requests.codes.ok:
        last_modified_str = response.headers['Last-Modified']
        with open(IF_MODIFIED_SINCE_FILE, 'w') as f:
            f.write(last_modified_str)
        logger.log('Updated file ' + IF_MODIFIED_SINCE_FILE + ' with "' +last_modified_str + '"')
        return response.json()
    else:
        return None


def convert_json(logger, json_data):
    """
    Converts the nodes from the freifunk-karte-data.json structure to the structure that is used by the Freifunk Auto
    Connect app

    :param logger: Logger object that is used for logging
    :param json_data: json structure from freifunk-karte-data.json
    :return: A dict containing the json structure suitable for the Freifunk Auto Connect app
    """
    data = {'timestamp': int(time.time())}
    new_nodes = {}
    for node in json_data['allTheRouters']:
        print(node)
        print(type(node['lat']))
        online = (node['status'] == 'online')
        try:
            new_nodes[node['id']] = {
                'online': online,
                'lat':    float(node['lat']),
                'lon':    float(node['long']),
                'name':   node['name']
            }
        except ValueError:
            logger.log("Node " + node['id'] + " in community " + node['community'] + " has invalid lat or lon!")
    logger.log(str(len(new_nodes)) + " nodes found.")
    data['nodes'] = new_nodes
    return data


def write_json_to_file(file_path, json_data):
    """ Writes json_data as json into the file at file_path """
    with open(file_path, 'w') as outfile:
        json.dump(json_data, outfile)

def gzip_file(file_path):
    """ Compresses a file using gzip and saves it at file_path.gz """
    with open(file_path, 'rb') as f_in:
        with gzip.open(file_path + '.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


def main():
    start_time = time.perf_counter()

    # Setup logger
    log_to_console = '-p' in sys.argv
    log_to_console = True
    logger = Logger(LOG_OUTPUT_FILE, log_to_console)

    json_data = download_node_location_file(logger)
    if json_data is None:
        sys.exit('Could not download a new version of freifunk-karte-data.json')

    new_json = convert_json(logger, json_data)
    write_json_to_file(OUTPUT_FILE, new_json)
    gzip_file(OUTPUT_FILE)

    end_time = time.perf_counter()
    duration = end_time - start_time
    logger.log('Elapsed time: ' + str(duration))


if __name__ == '__main__':
    main()
