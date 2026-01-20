function doGet() {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Data"); // Ensure your sheet is named "Data"
    var data = sheet.getDataRange().getValues();

    // terminate if no data
    if (data.length <= 1) {
        return ContentService.createTextOutput(JSON.stringify({ error: "No data found" })).setMimeType(ContentService.MimeType.JSON);
    }

    // Assume Row 1 is Headers
    var headers = data[0];
    var machines = [];

    // Parse rows 2 to N
    for (var i = 1; i < data.length; i++) {
        var row = data[i];
        var machineObj = {};

        // Map headers to object keys
        for (var j = 0; j < headers.length; j++) {
            var key = headers[j];
            // Convert to camelCase if needed, or keep as is if headers match React keys
            // e.g. "Present Cycle" -> "presentCycle"
            // Simple format: assume headers in sheet are like "id", "presentCycle", "status", etc.
            machineObj[key] = row[j];
        }

        // Basic type conversion
        if (machineObj.id) {
            machines.push(machineObj);
        }
    }

    // You can also add waterTank data from another sheet or specific cells
    var waterTank = {
        level: 75, // Default or fetch from a specific cell
        flow: 45.2,
        temp: 28.5
    };

    // Should ideally fetch water tank data from a "WaterTank" sheet
    var waterSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("WaterTank");
    if (waterSheet) {
        var wData = waterSheet.getDataRange().getValues();
        // Assume known cell structure, e.g., B1: Level, B2: Flow, B3: Temp
        // customized based on your actual sheet
        // waterTank.level = waterSheet.getRange("B1").getValue(); 
    }

    // Construct final response
    var result = {
        machines: machines,
        waterTank: waterTank
    };

    return ContentService.createTextOutput(JSON.stringify(result))
        .setMimeType(ContentService.MimeType.JSON);
}
