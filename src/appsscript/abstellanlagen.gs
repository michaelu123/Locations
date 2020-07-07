"use strict"

function combine() {
  let ssheet = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ssheet.getActiveSheet()
  let dheaders = sheet.getSheetValues(1, 1, 1, sheet.getLastColumn())[0]
  Logger.log("dheaders %s", dheaders)
  let hdrMap = {}
  for (const [i, h] of dheaders.entries()) {
    hdrMap[h] = i
  }
  Logger.log("hdrMap %s", hdrMap)

  const latRoundX = hdrMap["lat_round"]
  const lonRoundX = hdrMap["lon_round"]
  const modifiedX = hdrMap["modified"]
  let maxRow = sheet.getLastRow()
  let maxCol = sheet.getLastColumn()
  if (maxRow <= 2) {
    return;
  }
  let dvalues = sheet.getSheetValues(2, 1, maxRow - 1, maxCol)
  let dlen = dvalues.length
  // save row nr in last column
  let todel = []
  for (const r = 0; r < dlen; r++) {
    dvalues[r][maxCol] = r
  }
  dvalues.sort(function(a,b) {
    if (a[latRoundX] > b[latRoundX])
      return 1;
    if (a[latRoundX] < b[latRoundX])
      return -1;
    if (a[lonRoundX] > b[lonRoundX])
      return 1;
    if (a[lonRoundX] < b[lonRoundX])
      return -1;
    if (a[modifiedX] == "OSM")
      return -1;
    if (b[modifiedX] == "OSM")
      return 1;
    if (a[modifiedX] > b[modifiedX])
      return 1;
    if (a[modifiedX] < b[modifiedX])
      return -1;
    return 0; })

  for (let row1X = 0; row1X < dlen; row1X++) {
    let row1 = dvalues[row1X]
    if (row1.length == 0 || row1[latRoundX] == "" || row1[lonRoundX] == "") {
      todel.push(row1[maxCol] + 2)
      continue
    }
    for (let row2X = row1X + 1; row2X < dlen; row2X++) {
      let row2 = dvalues[row2X]
      if (row2[latRoundX] == row1[latRoundX] && row2[lonRoundX] == row1[lonRoundX]) {
        todel.push(+merge(sheet, dvalues, maxCol, row1X, row2X));
        dlen -= 1;
        row2X--;
      } else {
        break;
      }
    }
  }
  todel.sort(function(a,b){return b-a}) // descending!
  Logger.log("todel %s", todel)
  for (const td of todel) {
    sheet.deleteRow(td)
  }
}

function merge(sheet, dvalues, maxCol, row1X, row2X) {
  let row1 = dvalues[row1X]
  let row2 = dvalues[row2X]
  let changed = false
  for (const colx = 0; colx < maxCol; colx++) {
    if (row2[colx] != null && row2[colx] != "") {
      row1[colx] = row2[colx]
      changed = true
    }
  }
  if (changed) {
    sheet.getRange(row1[maxCol] + 2, 1, 1, maxCol).setValues([row1.slice(0,maxCol)])
  }
  dvalues.splice(row2X, 1);
  return(row2[maxCol] + 2)
}

function geojson() {
  let ssheet = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ssheet.getActiveSheet()
  let dheaders = sheet.getSheetValues(1, 1, 1, sheet.getLastColumn())[0]
  Logger.log("dheaders %s", dheaders)
  let hdrMap = {}
  for (const [i, h] of dheaders.entries()) {
    hdrMap[h] = i
  }
  Logger.log("hdrMap %s", hdrMap)

  const latX = hdrMap["lat"]
  const lonX = hdrMap["lon"]
  const ortX = hdrMap["ort"]
  const anzahlX = hdrMap["anzahl"]
  const auslastungX = hdrMap["auslastung"]
  const wildparkerX = hdrMap["wildparker"]
  const lastenradX = hdrMap["lastenrad"]
  const abschließbarX = hdrMap["abschließbar"]
  const anlehnbarX = hdrMap["anlehnbar"]
  const abstandX = hdrMap["abstand"]
  const ausparkenX = hdrMap["ausparken"]
  const geschütztX = hdrMap["geschützt"]
  const zustandX = hdrMap["zustand"]
  const bemerkungX = hdrMap["bemerkung"]

  let maxRow = sheet.getLastRow()
  let maxCol = sheet.getLastColumn()
  if (maxRow <= 2) {
    return;
  }
  let dvalues = sheet.getSheetValues(2, 1, maxRow - 1, maxCol)
  let dlen = dvalues.length

  let gjs = {
    "type": "FeatureCollection",
    "name": "Fahrradabstellplätze_München",
    "crs": {
        "type": "name",
        "properties": {
            "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
        }
    },
    "features": []
  }

  for (let rowX = 0; rowX < dlen; rowX++) {
    let row = dvalues[rowX]
    if (row.length == 0 || row[latX] == "" || row[lonX] == "") {
      continue
    }
    let loc = {
      "type": "Feature",
      "properties": {},
      "geometry": {
        "type": "Point",
        "coordinates": [row[lonX], row[latX]]
      }
    }
    if (row[ortX]) loc.properties["ort"] = row[ortX]
    if (row[anzahlX]) loc.properties["anzahl"] = row[anzahlX]
    if (row[auslastungX]) loc.properties["auslastung"] = row[auslastungX]
    if (row[wildparkerX]) loc.properties["wildparker"] = row[wildparkerX]
    if (row[lastenradX]) loc.properties["lastenrad"] = row[lastenradX]
    if (row[abschließbarX]) loc.properties["abschließbar"] = row[abschließbarX]
    if (row[anlehnbarX]) loc.properties["anlehnbar"] = row[anlehnbarX]
    if (row[abstandX]) loc.properties["abstand"] = row[abstandX]
    if (row[ausparkenX]) loc.properties["ausparken"] = row[ausparkenX]
    if (row[geschütztX]) loc.properties["geschützt"] = row[geschütztX]
    if (row[zustandX]) loc.properties["zustand"] = row[zustandX]
    if (row[bemerkungX]) loc.properties["bemerkung"] = row[bemerkungX]

    gjs.features.push(loc)
  }
  let gjsStr = JSON.stringify(gjs, null, 2)

  let thisFileId = SpreadsheetApp.getActive().getId();
  let thisFile = DriveApp.getFileById(thisFileId);
  let parent = thisFile.getParents().next();
  parent.createFile("abstellanlagen.geojson", gjsStr)
}

//#########################################################
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  // Or DocumentApp or FormApp.
  ui.createMenu('Locations')
      .addItem('Daten vereinen', 'combine')
      .addItem('Erzeuge Geojson-Datei', 'geojson')
      .addToUi();
}