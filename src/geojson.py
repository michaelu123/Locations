import codecs
import json

import config
import db

paths = [r"C:\Users\Michael\Downloads\2020-04-26_Fahrradabstellplätze_München_Punkte.geojson",
         r"C:\Users\Michael\Downloads\2020-04-26_Fahrradabstellplätze_München_Flächen.geojson",
         r"C:\Users\Michael\Downloads\2020-04-26_Fahrradabstellplätze_München_Linien.geojson"]
translate = {
    'addr:housenumber': '',
    'addr:postcode': '',
    'addr:street': 'ort',
    'anchors': 'Anker',
    'bicycle': '',
    'bicycle_parking': 'anlagentyp',
    'building': 'Gebäude',
    'capacity': 'anzahl',
    'covered': 'überdacht',
    'description': 'bemerkung',
    'description:de': 'bemerkung',
    'front_wheel': 'Vorderradhalter',
    'front_wheel_only': 'Vorderradhalter',
    'ground_slots': 'Erdschlitze',
    'hooks': 'Haken',
    'informal': 'Informell',
    'loops': 'Wendel',
    'maxstay': '',
    'multi-storey_racks': 'Mehrstöckig',
    'multistorey': 'Mehrstöckig',
    'name': 'name',
    'no': 'Nein',
    'note:total_capacity': '',
    'opening_hours': '',
    'rack': 'Träger',
    'scooter_parking': 'Scooter-Parkplatz',
    'shed': 'Schuppen',
    'shelter': 'überdacht',
    'source:capacity': '',
    'stands': 'Ständer',
    'wall_loops': 'Wandschlaufen',
    'wide_stands': 'BreiteStänder',
    'yes': 'Ja',
}

def conv():
    propSet = set()
    nrTotal = 0
    nrProps = 0
    res = {}
    for path in paths:
        with open(path, "r") as jsonFile:
            geoJS = json.load(jsonFile)
            featuresJS = geoJS.get("features")
            print("Path", path)
            for featureJS in featuresJS:
                geomJS = featureJS.get("geometry")
                geoType = geomJS.get("type")
                geoCoords = geomJS.get("coordinates")
                coord = mean(geoCoords)

                nrTotal += 1
                geoProps = featureJS.get("properties")
                valuesStr = []
                values = {}
                for p in ["bicycle_parking", "capacity", "covered", "shelter", "name", "description",
                          "source:capacity", "bicycle", "note:total_capacity", "description:de",
                          "maxstay", "addr:housenumber", "addr:postcode", "addr:street", "opening_hours"]:
                    v = geoProps.get(p)
                    if v:
                        # v = codecs.decode(v, encoding = "unicode_escape")
                        v = codecs.encode(v, "Windows-1252")
                        v = codecs.decode(v, "utf-8")
                        valuesStr.append(p + ":" + v)
                        propSet.add(p)
                        values[translate.get(p, p)] = translate.get(v, v)
                if len(valuesStr) != 0:
                    print(coord, ", ".join(valuesStr))
                    nrProps += 1
                res[tuple(coord)] = values
    print("Total", nrTotal, "Props", nrProps, "Diff", nrTotal - nrProps)
    print("Props set:", list(propSet))
    return res


def mean(coord):
    if isinstance(coord[0], list):
        ac = [mean(o) for o in coord]
        l = len(ac)
        if l == 1:
            return ac[0]
        m = [sum([c[0] for c in ac]) / l, sum([c[1] for c in ac]) / l]
        return m
    else:
        return coord


class OSM:
    def main(self, *argv):
        self.baseConfig = config.Config(self)
        base = "Abstellanlagen"
        self.baseJS = self.baseConfig.getBase(base)
        self.dbinst = db.DB.instance()
        self.dbinst.initDB(self)
        values = conv()
        self.dbinst.insert_data_from_osm(values)
        # duplicate: 48.12553483, 11.66346097

osm = OSM()
osm.main()
