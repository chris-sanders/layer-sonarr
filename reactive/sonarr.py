from charms.reactive import when, when_all, when_not, set_state
from charmhelpers.fetch import apt_install, add_source, apt_update
from charmhelpers.core import host
from charmhelpers.core import hookenv
from pathlib import Path
from zipfile import ZipFile
from libsonarr import SonarrHelper

import os
import subprocess
import shutil
import time
import sqlite3
import json

sh = SonarrHelper()


@when_not('sonarr.installed')
def install_sonarr():
    hookenv.status_set('maintenance', 'installing sonarr')
    add_source("deb http://apt.sonarr.tv/ master main", key='''
-----BEGIN PGP PUBLIC KEY BLOCK-----

mQENBFIdLCUBCADL27NXM4ZdnIL9e+2wYlHAT8PNEVVsJzS6xYaNaRF6Z9w1qz9N
qtxI3snY2O3SvaIu6+yRbrTtxghATMjvV/n/kglfffgT04OvzIu7mdN7vYlQ+X3I
3hWZtpJc4pq1RGBErNJ4WSyxqb646EVjrmNRuMMdIG3Pwy8L+5V2f9H/5u2eD8X5
yJvjZgZwjDBIaeLbu/NP2M6GnvDz1UgGY9irCRSuV7/QlxutEQQFcaxpdbTjlnEZ
+/CW/Td8+lAZ3LERyQrihUshV02IZw9/uj4PdjUyZBt/cTXUoMkxopDFrZxZ1+6Z
nzp5WQdcUqyJlmQ3/WTpy9FwExfbicMeHa+FABEBAAG0H056YkRyb25lIDxjb250
YWN0QG56YmRyb25lLmNvbT6JATgEEwECACIFAlIdLCUCGwMGCwkIBwMCBhUIAgkK
CwQWAgMBAh4BAheAAAoJEOv/a5nZt4STC6QH/j3GjVaDK/Y47pmg50PgDHohZfMo
HlMCENxfFwL8sEu63t1E29A+4qgLS1RTRxewc8YrXDYzFhkR9yd71Y/+ydwSRXNF
43hM/KBxh3ssbTuS6EsLKOhfZtjWsMbHJwNhdDtyKyYe5A//5EGl0Tj+EMUV04HY
3Z0INPYBe6igmfSrjaDK3yat/Bl3HR4lQwd7au4DLp488BE70XSlx240/Z1LQErw
qvcPQ95fBZsWot2jOiPIAOQuoDHqYSCd7ICjVHoaSLCmADej1K5rPcQ3YE3z/Okn
JZs/Hn9GmshWcOodzQOmgsmzkPn3yunjamWoPHvsaAMCcE2pVC/ZiYkyJAa5AQ0E
Uh0sJQEIAMiL7P0xLpdOQejcDD7igAvvWFIDHK487M/RP1o8BrQ7tBOLnDqKH1Lt
VffqrCS6MA2sQxYUv4Fx+HYH90BCqbkP0fRWVkREVONDb9ZgfyA4a9rpcZeM9oJX
qBChQjMrK6yM0yvbiIbKgxGs6ZpnxeAk5Ebgwkgrc8G44EPDM1w8lZA3tN8VQXMq
P/Vx8eLCpIviK8iEAos/tq14FGZUFTpPstFrgo1Zj6tc3zQqXHpAd3t9dQrtZNEA
NxnI+Dn/BMsUVmsMi/RS2y5Dg7iCPzXXrZUAQfLgUa3ofHvbTYwU4KecgRMege4n
zD9IjiVPCdpFMQCPPkajKhqzbmcoQ0sAEQEAAYkBHwQYAQIACQUCUh0sJQIbDAAK
CRDr/2uZ2beEk2/iB/4i4jp6aNEBiRZ+oxobTGeAlS8ttK+knlZifMPGC43iAL9i
MNOxV5D4eLAs1IRDYypB+qkjqZPiuTVlQCDBlEDQtZoUNCYUDZqSHPL7OzkeKFc2
h+o90rp2yDzhe3rVBuvEQp69n6qfVlNeWhQjPsxiLMQALlGRJWvdGl1cr6nevQ6s
Vm+pgH7rfgOPYRFlWmw/rQo6FcZjKPuBBjyjhC394WOHPW7v9HUn98UQzyD3A/sc
Qd/aWLSP9oZyapJsMlRHfLCptwoXMCFoH4TJS6PiEJ2DI9KRDEXuk9ueKKhbM11z
gX27DCbagJxljizL7n8mzeGG4qopDEU0jQ0sAXVh
=S/mr
-----END PGP PUBLIC KEY BLOCK-----

''')
    apt_update()
    host.adduser(sh.user, password="", shell='/bin/False', home_dir=sh.home_dir)
    apt_install('nzbdrone')
    os.chmod('/opt/', 0o777)
    shutil.chown('/opt/NzbDrone', user=sh.user, group=sh.user)
    host.chownr('/opt/NzbDrone', owner=sh.user, group=sh.user)
    hookenv.status_set('maintenance', 'installed')
    set_state('sonarr.installed')


@when('sonarr.installed')
@when_not('sonarr.autostart')
def auto_start():
    hookenv.status_set('maintenance', 'setting up auto-start')
    with open('/lib/systemd/system/sonarr.service', 'w') as serviceFile:
        serviceFile.write('''
[Unit]
Description=Sonarr Daemon
After=syslog.target network.target

[Service]
User={user}
Group={group}

Type=simple
ExecStart={mono} --debug {sonarr} -nobrowser
ExecStopPost=/usr/bin/killall -9 mono
TimeoutStopSec=20
KillMode=process
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
'''.format(user=sh.user,
           group=sh.user,
           mono='/usr/bin/mono',
           sonarr='/opt/NzbDrone/NzbDrone.exe'))
    subprocess.check_call("systemctl enable sonarr.service", shell=True)
    set_state('sonarr.autostart')


@when_all('sonarr.autostart', 'layer-hostname.installed')
@when_not('sonarr.configured')
def setup_config():
    hookenv.status_set('maintenance', 'configuring sonarr')
    backups = './backups'
    if sh.charm_config['restore-config']:
        try:
            os.mkdir(backups)
        except OSError as e:
            if e.errno is 17:
                pass
        backupFile = hookenv.resource_get('sonarrconfig')
        if backupFile:
            with ZipFile(backupFile, 'r') as inFile:
                inFile.extractall(sh.config_dir)
            hookenv.log("Restoring config, indexers are disabled enable with action when configuration has been checked", 'INFO')
            # Turn off indexers
            sh.set_indexers(False)
        else:
            hookenv.log("Add sonarrconfig resource, see juju attach or disable restore-config", 'WARN')
            hookenv.status_set('blocked', 'waiting for sonarrconfig resource')
            return
    else:
        host.service_start(sh.service_name)
        configFile = Path(sh.config_file)
        while not configFile.is_file():
            time.sleep(1)
    sh.modify_config(port=sh.charm_config['port'], 
                     sslport=sh.charm_config['ssl-port'], 
                     urlbase='None')
    hookenv.open_port(sh.charm_config['port'], 'TCP')
    # TODO: How does ssl port work for sonarr, looks to require more config
    # hookenv.open_port(config['ssl-port'],'TCP')
    host.service_start(sh.service_name)
    hookenv.status_set('active', '')
    set_state('sonarr.configured')
        

@when_not('usenet-downloader.configured')
@when_all('usenet-downloader.triggered', 'usenet-downloader.available', 'sonarr.configured')
def configure_downloader(usenetdownloader, *args):
    hookenv.log("Setting up sabnzbd relation requires editing the database and may not work", "WARNING")
    host.service_stop(sh.service_name)
    conn = sqlite3.connect(sh.database_file)
    c = conn.cursor()
    c.execute('''SELECT Settings FROM DownloadClients WHERE ConfigContract is "SabnzbdSettings"''')
    result = c.fetchall()
    if len(result):
        hookenv.log("Modifying existing sabnzbd setting for sonarr", "INFO")
        row = result[0]
        settings = json.loads(row[0])
        settings['port'] = usenetdownloader.port()
        settings['apiKey'] = usenetdownloader.apikey()
        settings['host'] = usenetdownloader.hostname()
        conn.execute('''UPDATE DownloadClients SET Settings = ? WHERE ConfigContract is "SabnzbdSettings"''',
                     (json.dumps(settings),))
    else:
        hookenv.log("Creating sabnzbd setting for sonarr.", "INFO")
        settings = {"tvCategory": "tv", "port": usenetdownloader.port(), "apiKey": usenetdownloader.apikey(), 
                    "olderTvPriority": -100, "host": usenetdownloader.hostname(), "useSsl": False, "recentTvPriority": -100}
        c.execute('''INSERT INTO DownloadClients
                  (Enable,Name,Implementation,Settings,ConfigContract) VALUES
                  (?,?,?,?,?)''', 
                  (1, 'Sabnzbd', 'Sabnzbd', json.dumps(settings), 'SabnzbdSettings'))
    conn.commit()
    host.service_start(sh.service_name)
    usenetdownloader.configured()


@when_not('plex-info.configured')
@when_all('plex-info.triggered', 'plex-info.available', 'sonarr.configured')
def configure_plex(plexinfo, *args):
    hookenv.log("Setting up plex relation requires editing the database and may not work", "WARNING")
    sh.setup_plex(hostname=plexinfo.hostname(), port=plexinfo.port(),
                  user=plexinfo.user(), passwd=plexinfo.passwd())
    plexinfo.configured()


