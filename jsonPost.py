import urllib2
import json

jdata = json.dumps([{"id": "Pib8eYDSFEI","runtime": "3:21","title": "The xx - Crystalised"},{ "id": "8UVNT4wvIGY","runtime": "4:04","title": "Gotye - Somebody That I Used To Know (feat. Kimbra) - official video"},{"id": "M11SvDtPBhA","runtime": "3:21","title": "Miley Cyrus - Party In The U.S.A."}])

urllib2.urlopen("http://127.0.0.1:8880/callback", jdata)