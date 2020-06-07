function doGet(e) {
  console.log("1doget");
  var templ = HtmlService.createTemplateFromFile("map");
  templ.markers = JSON.stringify(getMarkers())
  return templ.evaluate().setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

var dlatRoundX = 0;
var dlonRoundX = 0;
var ilatRoundX = 0;
var ilonRoundX = 0;

function getMarkers() {
  var ss = SpreadsheetApp.openById("1ULqk5oKgA78pprCupGxApRKTHDTl9fJzECXYEO4QXJ8");
  var datasheet = ss.getSheetByName("abstellanlagen_daten");
  var imagesheet = ss.getSheetByName("abstellanlagen_images");

  var dheaders = datasheet.getSheetValues(1, 1, 1, datasheet.getLastColumn())[0]
  Logger.log("dheaders %s", dheaders)
  var dhdrMap = {}
  for (const [i, h] of dheaders.entries()) {
    dhdrMap[h] = i
  }
  Logger.log("dhdrMap %s", dhdrMap)

  dlatRoundX = dhdrMap["lat_round"]
  dlonRoundX = dhdrMap["lon_round"]
  var dvalues = [];
  if (datasheet.getLastRow() <= 2) {
    return "";
  }
  dmaxRow = datasheet.getLastRow()
  dmaxCol = datasheet.getLastColumn()
  dvalues = datasheet.getSheetValues(2, 1, dmaxRow - 1, dmaxCol)
  dvalues.sort(dcompar)
  dlen = dvalues.length

  var iheaders = imagesheet.getSheetValues(1, 1, 1, imagesheet.getLastColumn())[0]
  Logger.log("iheaders %s", iheaders)
  var ihdrMap = {}
  for (const [i, h] of iheaders.entries()) {
    ihdrMap[h] = i
  }
  Logger.log("ihdrMap %s", ihdrMap)

  ilatRoundX = ihdrMap["lat_round"]
  ilonRoundX = ihdrMap["lon_round"]
  imagePathX = ihdrMap["image_path"]
  imageUrlX = ihdrMap["image_url"]
  var ivalues = [];
  if (imagesheet.getLastRow() <= 2) {
    return "";
  }
  imaxRow = imagesheet.getLastRow()
  imaxCol = imagesheet.getLastColumn()
  ivalues = imagesheet.getSheetValues(2, 1, imaxRow - 1, imaxCol)
  ivalues.sort(icompar)
  ilen = ivalues.length

  var markers = []
  var irowX = 0;
  for (var drowX = 0; drowX < dlen; drowX++) {
    var drow = dvalues[drowX]
    // Logger.log("drow", drow);
    if (drow.length < dlatRoundX) {
      continue
    }
    var dlat = drow[dlatRoundX];
    var dlon = drow[dlonRoundX];
    if (dlat == "" || dlon == "") {
      continue
    }
    var images = []
    while (irowX < ilen) {
      var irow = ivalues[irowX];
      var ilat = irow[ilatRoundX];
      if (ilat < dlat) {
        irowX += 1;
        continue;
      }
      if (ilat > dlat) {
        break;
      }
      var ilon = irow[ilonRoundX];
      if (ilon < dlon) {
        irowX += 1;
        continue;
      }
      if (ilon > dlon) {
        break;
      }
      Logger.log("irowX", irowX, "url", irow[imageUrlX]);
      images.push(irow[imageUrlX])
      irowX += 1;
      continue;
    }
    var m = {lat: dlat, lng:dlon, imgs: images};
    Logger.log("m", m);
    markers.push(m);
  }
  return markers
}

function dcompar(a,b) {
  if (a[dlatRoundX] > b[dlatRoundX])
    return 1;
  if (a[dlatRoundX] < b[dlatRoundX])
    return -1;
  if (a[dlonRoundX] > b[dlonRoundX])
    return 1;
  if (a[dlonRoundX] < b[dlonRoundX])
    return -1;
  return 0;
}

function icompar(a,b) {
  if (a[ilatRoundX] > b[ilatRoundX])
    return 1;
  if (a[ilatRoundX] < b[ilatRoundX])
    return -1;
  if (a[ilonRoundX] > b[ilonRoundX])
    return 1;
  if (a[ilonRoundX] < b[ilonRoundX])
    return -1;
  return 0;
}
