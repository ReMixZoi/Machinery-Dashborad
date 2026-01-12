/**
 * Google Apps Script API สำหรับอ่านข้อมูลจาก Google Sheets
 * Deploy เป็น Web App เพื่อให้ Dashboard ดึงข้อมูลได้
 */

// ===== CONFIG =====
const SPREADSHEET_ID = "1RJ9OI8Bz8Xy_7HW7fZVQnjeYshDd0BZUZrkG3ycJfy0";
const TANK_SHEET_NAME = "Tank";

/**
 * รับ HTTP GET Request
 * URL: https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec
 */
function doGet(e) {
  try {
    const params = e.parameter || {};
    const action = params.action || 'getLatest';
    
    if (action === 'getLatest') {
      return getLatestTankData();
    } else if (action === 'getAll') {
      return getAllTankData();
    } else {
      return createResponse({ error: 'Invalid action' }, 400);
    }
  } catch (error) {
    Logger.log('Error: ' + error.toString());
    return createResponse({ error: error.toString() }, 500);
  }
}

/**
 * ดึงข้อมูลถังน้ำล่าสุด (บรรทัดท้ายสุด)
 */
function getLatestTankData() {
  const sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(TANK_SHEET_NAME);
  
  if (!sheet) {
    return createResponse({ error: 'Sheet not found: ' + TANK_SHEET_NAME }, 404);
  }
  
  const lastRow = sheet.getLastRow();
  
  if (lastRow < 2) {
    // ไม่มีข้อมูล (มีแค่ header)
    return createResponse({
      waterTank: {
        level: 0,
        flow: 0,
        temp: 0,
        status: 'NO_DATA',
        timestamp: new Date().toISOString()
      }
    });
  }
  
  // อ่านข้อมูลบรรทัดสุดท้าย
  // สมมติว่า columns: [Timestamp, Level, Status, Flow, Temp]
  const data = sheet.getRange(lastRow, 1, 1, 5).getValues()[0];
  
  const waterTankData = {
    timestamp: data[0] ? formatTimestamp(data[0]) : new Date().toISOString(),
    level: parseFloat(data[1]) || 0,
    status: data[2] || 'UNKNOWN',
    flow: parseFloat(data[3]) || 0,
    temp: parseFloat(data[4]) || 0
  };
  
  return createResponse({
    waterTank: waterTankData,
    machines: [] // เพิ่มส่วนนี้เพื่อให้ format ตรงกับเดิม
  });
}

/**
 * ดึงข้อมูลทั้งหมด (สำหรับ historical data)
 */
function getAllTankData() {
  const sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(TANK_SHEET_NAME);
  
  if (!sheet) {
    return createResponse({ error: 'Sheet not found' }, 404);
  }
  
  const lastRow = sheet.getLastRow();
  
  if (lastRow < 2) {
    return createResponse({ data: [] });
  }
  
  // อ่านข้อมูลทั้งหมด (ยกเว้น header)
  const data = sheet.getRange(2, 1, lastRow - 1, 5).getValues();
  
  const records = data.map(row => ({
    timestamp: formatTimestamp(row[0]),
    level: parseFloat(row[1]) || 0,
    status: row[2] || 'UNKNOWN',
    flow: parseFloat(row[3]) || 0,
    temp: parseFloat(row[4]) || 0
  }));
  
  return createResponse({ data: records });
}

/**
 * สร้าง Response แบบ JSON
 */
function createResponse(data, statusCode = 200) {
  const output = JSON.stringify(data);
  
  return ContentService
    .createTextOutput(output)
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * แปลง Timestamp ให้เป็น ISO String
 */
function formatTimestamp(timestamp) {
  if (timestamp instanceof Date) {
    return timestamp.toISOString();
  }
  
  // ถ้าเป็น string พยายามแปลง
  try {
    return new Date(timestamp).toISOString();
  } catch (e) {
    return new Date().toISOString();
  }
}

/**
 * ฟังก์ชันทดสอบ (รันใน Apps Script Editor)
 */
function testGetLatest() {
  const result = getLatestTankData();
  Logger.log(result.getContent());
}

/**
 * ฟังก์ชันทดสอบ (รันใน Apps Script Editor)
 */
function testGetAll() {
  const result = getAllTankData();
  Logger.log(result.getContent());
}
