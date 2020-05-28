function combine() {
  var ssheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ssheet.getActiveSheet()
  var dheaders = sheet.getSheetValues(1, 1, 1, sheet.getLastColumn())[0]
  Logger.log("dheaders %s", dheaders)
  var hdrMap = {}
  for (const [i, h] of dheaders.entries()) {
    hdrMap[h] = i
  }
  Logger.log("hdrMap %s", hdrMap)

  const latRoundX = hdrMap["lat_round"]
  const lonRoundX = hdrMap["lon_round"]
  const modifiedX = hdrMap["modified"]
  var dvalues = [];
  if (sheet.getLastRow() <= 2) {
    return;
  }
  maxRow = sheet.getLastRow()
  maxCol = sheet.getLastColumn()
  dvalues = sheet.getSheetValues(2, 1, maxRow - 1, maxCol)
  dlen = dvalues.length
  // save row nr in last column
  todel = []
  for (r = 0; r < dlen; r++) {
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

  for (row1X = 0; row1X < dlen; row1X++) {
    if (dvalues[row1X].length == 0 || dvalues[row1X][latRoundX] == "" || dvalues[row1X][lonRoundX] == "") {
      todel.push(dvalues[row1X][maxCol] + 2)
      continue
    }
    for (row2X = row1X + 1; row2X < dlen; row2X++) {
      if (dvalues[row2X][latRoundX] == dvalues[row1X][latRoundX] && dvalues[row2X][lonRoundX] == dvalues[row1X][lonRoundX]) {
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
  row1 = dvalues[row1X]
  row2 = dvalues[row2X]
  changed = false
  for (colx = 0; colx < maxCol; colx++) {
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

//#########################################################
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  // Or DocumentApp or FormApp.
  ui.createMenu('Locations')
      .addItem('Daten vereinen', 'combine')
      .addToUi();
}