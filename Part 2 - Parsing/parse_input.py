import re
import json

def parse_physical_interface_input(phy_log_interface):
        interface_obj = {}
        name = re.search(r'(([gx]e-(\d\/){2}\d+)|ae\d+)', phy_log_interface).group()
        interface = phy_log_interface.split('\n')
        for line in interface:
            if 'Physical' in line:
                admin = re.search(r'Enabled|Disabled', line).group()
                link = re.search(r'Up|Down', line).group()
                state = {'admin': admin.lower(), 'link': link.lower()}

        try:
            dscr = re.search(r'Description: \w+', phy_log_interface).group().replace('Description: ', '').strip()
        except:
            dscr = ''

        linkLevelType = re.search(r'Link-level type: [A-Za-z]+', phy_log_interface).group().replace('Link-level type:', '').strip().lower()
        mtu = re.search(r'MTU: \d+', phy_log_interface).group().replace('MTU:', '').strip().lower()

        try:
            duplex = re.search(r'Link-mode: [A-Za-z]+\-[A-Za-z]+', phy_log_interface).group().replace('Link-mode:', '').strip().lower()
            duplex = re.search(r'full', duplex).group()
        except:
            duplex = ''

        speed = re.search(r'Speed: \d+\w+', phy_log_interface).group().replace('Speed:', '').strip().lower()
        if 'mbps' in speed:
            speed = speed.replace('mbps', '0'*6)
        if 'gbps' in speed:
            speed = speed.replace('gbps', '0'*9)

        mac_regex = re.compile(r'(?:[0-9a-fA-F]:?){12}')
        mac = re.search(mac_regex, phy_log_interface).group()
        
        clearing = re.search(r'Statistics last cleared: \w+', phy_log_interface).group().replace('Statistics last cleared:', '').strip().lower()

        statsList = []
        traffic_stats_match = re.search(r"Traffic statistics:(.*?)Label-switched interface", phy_log_interface, re.DOTALL)
        if traffic_stats_match:
            traffic_stats_text = traffic_stats_match.group(1).lower()
            inBytes = re.search(r'input  bytes(\s+)?:\s+\d+', traffic_stats_text).group().replace('input  bytes  :', '').strip()
            outBytes = re.search(r'output bytes(\s+)?:\s+\d+', traffic_stats_text).group().replace('output bytes  :', '').strip()
            inPkts = re.search(r'input  packets(\s+)?:\s+\d+', traffic_stats_text).group().replace('input  packets:', '').strip()
            outPkts = re.search(r'output packets(\s+)?:\s+\d+', traffic_stats_text).group().replace('output packets:', '').strip()
            
            traffic_statistics = {
                'type': 'traffic',
                'counters': {
                    'inBytes': int(inBytes),
                    'outBytes':int(outBytes),
                    'inPkts': int(inPkts),
                    'outPkts': int(outPkts),
                },
                'load': { 'inBytes': 0, 'outBytes': 0, 'inPkts': 0, 'outPkts': 0 },
            }

            statsList.append(traffic_statistics)

            inErr_inDrops_match = re.search(r'Input errors:(.*?)Drops:\s\d+', phy_log_interface, re.DOTALL) 
            if inErr_inDrops_match:
                inErr_inDrops_match_text = inErr_inDrops_match.group().lower()
                inErr_match_text = re.search(r'errors:\s\d+', inErr_inDrops_match_text, re.DOTALL).group().replace('errors:', '').strip()
                inDrops_match_text = re.search(r'drops:\s\d+', inErr_inDrops_match_text, re.DOTALL).group().replace('drops:', '').strip()

            inError_statistics = { 'type': 'inErrors', 'counters': { 'inErr': int(inErr_match_text), 'inDrops':int(inDrops_match_text) } }

            outErr_outDrops_match = re.search(r'Output errors:(.*?)Drops:\s\d+', phy_log_interface, re.DOTALL) 
            if outErr_outDrops_match:
                outErr_outDrops_match_text = outErr_outDrops_match.group().lower()
                outErr_match_text = re.search(r'errors:\s\d+', outErr_outDrops_match_text, re.DOTALL).group().replace('errors:', '').strip()
                outDrops_match_text = re.search(r'drops:\s\d+', outErr_outDrops_match_text, re.DOTALL).group().replace('drops:', '').strip()

            outError_statistics = { 'type': 'outErrors', 'counters': { 'outErr': int(outErr_match_text), 'outDrops':int(outDrops_match_text) } }

            statsList.append(inError_statistics)
            statsList.append(outError_statistics)

        interface_obj['name'] = name
        interface_obj['state'] = state
        if dscr: interface_obj['dscr'] = dscr
        interface_obj['linkLevelType'] = linkLevelType
        interface_obj['mtu'] = int(mtu)
        if duplex: interface_obj['duplex'] = duplex
        interface_obj['speed'] = int(speed)
        interface_obj['mac'] = mac
        interface_obj['clearing'] = clearing
        interface_obj['statsList'] = statsList

        return interface_obj

def parse_logical_interface_input(phy_log_interface):
    log_interface_obj = {}
    logIntList = []
    name = re.search(r'(([gx]e-(\d\/){2}\d+)|ae\d+)(\.\d+)?', phy_log_interface).group()
    
    protocol_inet_match = re.search(r'Protocol inet', phy_log_interface).group().replace('Protocol ', '').strip()
    mtu_match = re.findall(r'MTU: \d+', phy_log_interface)[0].replace('MTU: ', '').strip()
    protocol_inet_ip_match = re.search(r'Destination: [0-9]+(?:\.[0-9]+){3}', phy_log_interface).group().replace('Destination: ', '').strip()
    protocol_inet_mask_match = re.search(r'Destination: (.*?)\/\d+', phy_log_interface).group().replace('Destination: ', '').strip()
    protocol_inet_mask_match = re.search(r'\/\d+', protocol_inet_mask_match).group().replace('/', '')
    protocol_inet_net_match = re.search(r'Local: [0-9]+(?:\.[0-9]+){3}', phy_log_interface).group().replace('Local: ', '').strip()
    protocol_inet_net_long_match = 'netLong'
    protocol_inet_broad_long_match = 'broadLong'
    protocol_inet_flag_list_match = re.search(r'Addresses, Flags: [A-Za-z\-].*', phy_log_interface).group().replace('Addresses, Flags: ', '').strip().split(' ')
    protocol_iso_match = re.search(r'Protocol iso', phy_log_interface).group().replace('Protocol ', '').strip()
    protocol_mpls_match = re.search(r'Protocol mpls', phy_log_interface).group().replace('Protocol ', '').strip()
    
    try:
        dscr = re.search(r'Description: \w+', phy_log_interface).group().replace('Description: ', '').strip()
    except:
        dscr = ''

    protocol_inet = {
        'type' : protocol_inet_match,
        'value' : {
            'ipList': [
                {
                    'ip': protocol_inet_ip_match,
                    'mask' : protocol_inet_mask_match,
                    'net' : protocol_inet_net_match,
                    'netLong' : protocol_inet_net_long_match,
                    'broadLong' : protocol_inet_broad_long_match,
                    'flagList' : protocol_inet_flag_list_match
                }
            ]
        }
    }
    protocol_iso = { 'type' : protocol_iso_match }
    protocol_mpls = { 'type' : protocol_mpls_match }

    protocolList = [protocol_inet, protocol_iso, protocol_mpls]

    if 'bundle' in phy_log_interface.lower():

        bundle_stats_match = re.search(r"Bundle:(.*?)Link:", phy_log_interface, re.DOTALL)
        if bundle_stats_match:
            bundle_stats_text = bundle_stats_match.group(1).lower().replace('input :', '').replace('output:', '').strip()
            bundle_stats_text = re.sub(r'\s+', ' ', bundle_stats_text).split(' ')
            
            inPkts = bundle_stats_text[0]
            inBytes = bundle_stats_text[2] 
            outPkts = bundle_stats_text[4]
            outBytes = bundle_stats_text[6]

        bundle_statistics = {
            'type': 'bundle',
            'counters': {
                'inPkts': inPkts,
                'inBytes': inBytes,
                'outPkts': outPkts,
                'outBytes':outBytes,
            },
            'load': { 'inBytes': 0, 'outBytes': 0, 'inPkts': 0, 'outPkts': 0 },
        }

        statsList = [bundle_statistics]

    else:

        traffic_stats_match = re.search(r"Traffic statistics:(.*?)Local statistics:", phy_log_interface, re.DOTALL)
        if traffic_stats_match:
            traffic_stats_text = traffic_stats_match.group(1).lower()
            inBytes = re.search(r'input  bytes(\s+)?:\s+\d+', traffic_stats_text).group().replace('input  bytes  :', '').strip()
            outBytes = re.search(r'output bytes(\s+)?:\s+\d+', traffic_stats_text).group().replace('output bytes  :', '').strip()
            inPkts = re.search(r'input  packets(\s+)?:\s+\d+', traffic_stats_text).group().replace('input  packets:', '').strip()
            outPkts = re.search(r'output packets(\s+)?:\s+\d+', traffic_stats_text).group().replace('output packets:', '').strip()

        traffic_statistics = {
            'type': 'traffic',
            'counters': {
                'inBytes': int(inBytes),
                'outBytes':int(outBytes),
                'inPkts': int(inPkts),
                'outPkts': int(outPkts),
            }
        }

        local_stats_match = re.search(r"Local statistics:(.*?)Transit statistics:", phy_log_interface, re.DOTALL)
        if local_stats_match:
            local_stats_text = local_stats_match.group(1).lower()
            inBytes = re.search(r'input  bytes(\s+)?:\s+\d+', local_stats_text).group().replace('input  bytes  :', '').strip()
            outBytes = re.search(r'output bytes(\s+)?:\s+\d+', local_stats_text).group().replace('output bytes  :', '').strip()
            inPkts = re.search(r'input  packets(\s+)?:\s+\d+', local_stats_text).group().replace('input  packets:', '').strip()
            outPkts = re.search(r'output packets(\s+)?:\s+\d+', local_stats_text).group().replace('output packets:', '').strip()

        local_statistics = {
            'type': 'local',
            'counters': {
                'inBytes': int(inBytes),
                'outBytes':int(outBytes),
                'inPkts': int(inPkts),
                'outPkts': int(outPkts),
            }
        }

        statsList = [traffic_statistics, local_statistics]

    log_interface_obj['name'] = name
    if dscr: log_interface_obj['dscr'] = dscr
    log_interface_obj['protocolList'] = protocolList
    log_interface_obj['statsList'] = statsList
    log_interface_obj['mtu'] = int(mtu_match)

    logIntList.append(log_interface_obj)

    return [logIntList]

if __name__ == '__main__':
    
    parseResult1 = []
    input_data = open('input.txt', 'r').read()
    
    physical_interfaces = re.split(r'Physical interface:', input_data)[1:]

    for phy_interface in physical_interfaces:
        temp_obj = {}
        phy_log_interfaces = re.split(r'Logical interface ', phy_interface)
        for phy_log_interface in phy_log_interfaces:
            if 'Physical' in phy_log_interface:
                temp_obj = parse_physical_interface_input(phy_log_interface)
            else:
                temp_obj['logIntList'] = parse_logical_interface_input(phy_log_interface)
        parseResult1.append(temp_obj)
        
    open('parsed_result.json', 'w').write(json.dumps(parseResult1, indent=4))

